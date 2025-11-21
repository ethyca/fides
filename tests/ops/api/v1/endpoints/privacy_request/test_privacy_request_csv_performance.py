"""
Test to demonstrate the performance improvement of CSV download with eager loading.

This test shows the difference in database query count before and after the optimization.
"""

import csv
import io
from datetime import datetime

import pytest
from sqlalchemy import event
from sqlalchemy.engine import Engine
from starlette.testclient import TestClient

from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.privacy_request import (
    CustomPrivacyRequestField,
    PrivacyRequestStatus,
)
from fides.common.api.scope_registry import PRIVACY_REQUEST_READ
from fides.common.api.v1.urn_registry import PRIVACY_REQUESTS


class QueryCounter:
    """Context manager to count SQL queries executed."""

    def __init__(self):
        self.queries = []
        self.count = 0

    def __enter__(self):
        event.listen(Engine, "before_cursor_execute", self.receive_query)
        return self

    def __exit__(self, *args):
        event.remove(Engine, "before_cursor_execute", self.receive_query)

    def receive_query(self, conn, cursor, statement, params, context, executemany):
        self.queries.append(statement)
        self.count += 1


@pytest.fixture
def multiple_privacy_requests(db, policy):
    """Create multiple privacy requests with identities and custom fields for testing."""
    privacy_requests = []

    for i in range(10):
        pr = PrivacyRequest.create(
            db=db,
            data={
                "external_id": f"test_external_id_{i}",
                "started_processing_at": None,
                "finished_processing_at": None,
                "requested_at": None,
                "status": PrivacyRequestStatus.pending,
                "policy_id": policy.id,
            },
        )

        # Add identities
        pr.cache_identity(
            {
                "email": f"test{i}@example.com",
                "phone_number": f"+1234567890{i}",
            }
        )

        # Add custom fields
        custom_field = CustomPrivacyRequestField(
            label=f"Custom Field {i}",
            value=f"custom_value_{i}",
        )
        pr.persist_custom_privacy_request_fields(
            db, {f"custom_field_{i}": custom_field}
        )

        pr.save(db)
        privacy_requests.append(pr)

    yield privacy_requests

    # Cleanup
    for pr in privacy_requests:
        pr.delete(db)


@pytest.mark.usefixtures(
    "allow_custom_privacy_request_field_collection_enabled",
    "allow_custom_privacy_request_fields_in_request_execution_enabled",
)
class TestCSVDownloadPerformance:
    """Test CSV download performance with query counting."""

    @pytest.fixture(scope="function")
    def url(self) -> str:
        return f"/api/v1{PRIVACY_REQUESTS}"

    def test_csv_download_query_count(
        self,
        db,
        api_client: TestClient,
        generate_auth_header,
        multiple_privacy_requests,
        url,
    ):
        """
        Test that CSV download uses eager loading to minimize database queries.

        With the optimization:
        - We should see approximately 5-6 queries regardless of the number of privacy requests
        - Without optimization, we'd see ~4 queries per privacy request (N+1 problem)

        For 10 privacy requests:
        - Optimized: ~5-6 queries
        - Unoptimized: ~40+ queries
        """
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])

        with QueryCounter() as counter:
            response = api_client.get(url + "?download_csv=True", headers=auth_header)

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"

        # Verify CSV content
        content = response.content.decode()
        file = io.StringIO(content)
        csv_file = csv.DictReader(file, delimiter=",")
        rows = list(csv_file)

        assert len(rows) == 10, "Should have 10 privacy requests in CSV"

        # Check query count - with eager loading, should be much lower
        print(f"\n{'='*60}")
        print(f"Query Performance Report")
        print(f"{'='*60}")
        print(f"Number of privacy requests: {len(multiple_privacy_requests)}")
        print(f"Total queries executed: {counter.count}")
        print(
            f"Average queries per request: {counter.count / len(multiple_privacy_requests):.2f}"
        )
        print(f"{'='*60}\n")

        if counter.count > 20:
            print(f"⚠️  WARNING: Query count is high ({counter.count})")
            print(f"Expected: ~5-10 queries with eager loading")
            print(f"This suggests the N+1 query problem may still exist\n")
        else:
            print(f"✅ GOOD: Query count is optimized ({counter.count} queries)")
            print(f"Eager loading is working correctly\n")

        # With eager loading, we expect approximately:
        # 1. Query to get privacy requests with filters/pagination
        # 2. Query to eager load provided_identities
        # 3. Query to eager load custom_fields
        # 4. Query to eager load policies
        # 5. Query to get denial audit logs
        # Plus a few overhead queries (begin transaction, etc.)
        #
        # Total should be around 5-10 queries regardless of number of requests
        assert counter.count < 15, (
            f"Query count too high: {counter.count}. "
            f"Expected <15 queries with eager loading for 10 requests. "
            f"This indicates the N+1 query problem may not be fully resolved."
        )

    def test_csv_download_detailed_query_analysis(
        self,
        db,
        api_client: TestClient,
        generate_auth_header,
        multiple_privacy_requests,
        url,
    ):
        """
        Detailed analysis of queries to verify eager loading is working.
        """
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])

        with QueryCounter() as counter:
            response = api_client.get(url + "?download_csv=True", headers=auth_header)

        assert response.status_code == 200

        # Analyze query patterns
        print(f"\n{'='*60}")
        print(f"Detailed Query Analysis")
        print(f"{'='*60}\n")

        # Count queries by table
        query_tables = {
            "privacyrequest": 0,
            "providedidentity": 0,
            "customprivacyrequestfield": 0,
            "ctl_policies": 0,
            "auditlog": 0,
            "other": 0,
        }

        for query in counter.queries:
            query_lower = query.lower()
            if "privacyrequest" in query_lower:
                query_tables["privacyrequest"] += 1
            elif "providedidentity" in query_lower:
                query_tables["providedidentity"] += 1
            elif "customprivacyrequestfield" in query_lower:
                query_tables["customprivacyrequestfield"] += 1
            elif "ctl_policies" in query_lower:
                query_tables["ctl_policies"] += 1
            elif "auditlog" in query_lower:
                query_tables["auditlog"] += 1
            else:
                query_tables["other"] += 1

        for table, count in query_tables.items():
            if count > 0:
                print(f"{table:30} {count} queries")

        print(f"\n{'='*60}")
        print(f"Total: {counter.count} queries")
        print(f"{'='*60}\n")

        # Verify eager loading is working by checking that we don't have
        # multiple queries for relationships (should be 1 query per relationship type)
        assert query_tables["providedidentity"] <= 2, (
            f"Too many ProvidedIdentity queries ({query_tables['providedidentity']}). "
            "Expected 1-2 with eager loading."
        )
        assert query_tables["customprivacyrequestfield"] <= 2, (
            f"Too many CustomPrivacyRequestField queries ({query_tables['customprivacyrequestfield']}). "
            "Expected 1-2 with eager loading."
        )
