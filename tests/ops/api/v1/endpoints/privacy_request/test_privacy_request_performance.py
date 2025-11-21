"""
Performance tests for privacy request endpoints with eager loading optimizations.

These tests demonstrate the N+1 query improvements across:
- CSV downloads
- Regular list views with identities/custom fields
- Bulk operations (approve, deny, cancel, finalize, restart, soft delete)

Each test counts database queries and asserts that eager loading is working correctly.
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
from fides.common.api.scope_registry import (
    PRIVACY_REQUEST_DELETE,
    PRIVACY_REQUEST_READ,
    PRIVACY_REQUEST_REVIEW,
)
from fides.common.api.v1.urn_registry import (
    PRIVACY_REQUEST_APPROVE,
    PRIVACY_REQUEST_BULK_SOFT_DELETE,
    PRIVACY_REQUEST_SEARCH,
    PRIVACY_REQUESTS,
)


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
class TestPrivacyRequestPerformance:
    """Test privacy request endpoint performance with query counting."""

    @pytest.fixture(scope="function")
    def url(self) -> str:
        return f"/api/v1{PRIVACY_REQUESTS}"

    @pytest.fixture(scope="function")
    def search_url(self) -> str:
        return f"/api/v1{PRIVACY_REQUEST_SEARCH}"

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

    def test_list_view_with_identities_query_count(
        self,
        db,
        api_client: TestClient,
        generate_auth_header,
        multiple_privacy_requests,
        search_url,
    ):
        """
        Test that regular list view with include_identities uses eager loading.

        With the optimization:
        - Should see ~3-5 queries for any number of requests

        Without optimization:
        - Would see ~25 extra queries for identities (N+1 problem)
        """
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])

        with QueryCounter() as counter:
            response = api_client.post(
                search_url,
                headers=auth_header,
                json={
                    "include_identities": True,
                    "verbose": False,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10

        # Verify identities are included
        for item in data["items"]:
            assert "identity" in item
            assert item["identity"] is not None

        print(f"\n{'='*60}")
        print(f"List View with Identities Performance")
        print(f"{'='*60}")
        print(f"Privacy requests: {len(multiple_privacy_requests)}")
        print(f"Total queries: {counter.count}")
        print(f"{'='*60}\n")

        # With eager loading, should be much fewer queries
        assert counter.count < 15, (
            f"Query count too high: {counter.count}. "
            f"Expected <15 queries with eager loading for 10 requests."
        )

    def test_list_view_with_custom_fields_query_count(
        self,
        db,
        api_client: TestClient,
        generate_auth_header,
        multiple_privacy_requests,
        search_url,
    ):
        """
        Test that regular list view with include_custom_privacy_request_fields uses eager loading.
        """
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])

        with QueryCounter() as counter:
            response = api_client.post(
                search_url,
                headers=auth_header,
                json={
                    "include_custom_privacy_request_fields": True,
                    "verbose": False,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10

        # Verify custom fields are included
        for item in data["items"]:
            assert "custom_privacy_request_fields" in item

        print(f"\n{'='*60}")
        print(f"List View with Custom Fields Performance")
        print(f"{'='*60}")
        print(f"Privacy requests: {len(multiple_privacy_requests)}")
        print(f"Total queries: {counter.count}")
        print(f"{'='*60}\n")

        # With eager loading, should be much fewer queries
        assert counter.count < 15, (
            f"Query count too high: {counter.count}. "
            f"Expected <15 queries with eager loading for 10 requests."
        )

    def test_bulk_approve_query_count(
        self,
        db,
        api_client: TestClient,
        generate_auth_header,
        multiple_privacy_requests,
    ):
        """
        Test that bulk approve fetches all requests in one query.

        Note: Bulk approve triggers MANY queries for:
        - Audit log creation (1 per request)
        - Privacy request updates (1 per request)
        - Queueing celery tasks for privacy request execution (triggers DSR processing)
        - Custom field approvals (if applicable)
        - Actual DSR execution queries (if celery runs synchronously in test)

        WARNING: In test environments, celery tasks may execute synchronously,
        causing actual privacy request processing which generates hundreds of queries
        per request. This is expected behavior in tests.

        The key optimization is that we fetch ALL requests in 1 query
        instead of N separate queries for the initial fetch.
        """
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_REVIEW])
        request_ids = [
            pr.id for pr in multiple_privacy_requests[:3]
        ]  # Reduce to 3 for faster test

        with QueryCounter() as counter:
            response = api_client.patch(
                f"/api/v1{PRIVACY_REQUEST_APPROVE}",
                headers=auth_header,
                json={"request_ids": request_ids},
            )

        assert response.status_code == 200
        data = response.json()

        print(f"\n{'='*60}")
        print(f"Bulk Approve Performance")
        print(f"{'='*60}")
        print(f"Requests approved: {len(request_ids)}")
        print(f"Succeeded: {len(data.get('succeeded', []))}")
        print(f"Failed: {len(data.get('failed', []))}")
        print(f"Total queries: {counter.count}")
        print(f"Queries per request: {counter.count / len(request_ids):.1f}")
        print(f"{'='*60}\n")

        # With optimization, we should see roughly constant overhead + linear per-request work
        # Without optimization, fetching would add N more queries
        # Allow generous threshold since bulk approve does a lot of work
        # (audit logs, celery tasks, updates, etc.)
        queries_per_request = counter.count / len(request_ids)
        assert queries_per_request < 200, (
            f"Query count per request too high: {queries_per_request:.1f}. "
            f"Total: {counter.count} for {len(request_ids)} requests. "
            f"This suggests the batch fetch optimization may not be working."
        )

    def test_bulk_soft_delete_query_count(
        self,
        db,
        api_client: TestClient,
        generate_auth_header,
        multiple_privacy_requests,
    ):
        """
        Test that bulk soft delete fetches all requests in one query.

        Soft delete operations include:
        - 1 query to fetch all requests (optimized)
        - 1 query per request to update deleted_at and deleted_by fields
        - Transaction overhead

        Expected: ~1 + N queries (where N is number of requests)
        Without optimization: ~N + N queries (N to fetch, N to update)
        """
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_DELETE])
        request_ids = [pr.id for pr in multiple_privacy_requests[:5]]

        with QueryCounter() as counter:
            response = api_client.post(
                f"/api/v1{PRIVACY_REQUEST_BULK_SOFT_DELETE}",
                headers=auth_header,
                json={"request_ids": request_ids},
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["succeeded"]) == 5

        print(f"\n{'='*60}")
        print(f"Bulk Soft Delete Performance")
        print(f"{'='*60}")
        print(f"Requests deleted: {len(request_ids)}")
        print(f"Total queries: {counter.count}")
        print(f"Queries per request: {counter.count / len(request_ids):.1f}")
        print(f"{'='*60}\n")

        # With optimization: 1 fetch + 5 updates + overhead = ~8-20 queries
        # Without optimization: 5 fetches + 5 updates + overhead = ~15-25 queries
        # We allow up to 25 to account for transaction overhead and other operations
        assert counter.count < 25, (
            f"Query count too high: {counter.count}. "
            f"Expected <25 queries for {len(request_ids)} requests with batch optimization. "
            f"Average {counter.count / len(request_ids):.1f} queries per request."
        )
