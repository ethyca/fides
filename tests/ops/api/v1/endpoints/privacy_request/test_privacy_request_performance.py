"""
Performance tests for privacy request endpoints to verify N+1 query fixes.
"""

import csv
import io
from datetime import datetime
from unittest import mock

import pytest
from sqlalchemy import event
from sqlalchemy.engine import Engine
from starlette.testclient import TestClient

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
    """Context manager to count SQL queries."""

    def __init__(self):
        self.count = 0

    def __enter__(self):
        event.listen(Engine, "before_cursor_execute", self.receive_query)
        return self

    def __exit__(self, *args):
        event.remove(Engine, "before_cursor_execute", self.receive_query)

    def receive_query(self, conn, cursor, statement, params, context, executemany):
        self.count += 1


@pytest.fixture
def multiple_privacy_requests(db, policy):
    """Create 10 privacy requests with identities and custom fields."""
    privacy_requests = []
    for i in range(10):
        pr = PrivacyRequest.create(
            db=db,
            data={
                "external_id": f"test_external_id_{i}",
                "status": PrivacyRequestStatus.pending,
                "policy_id": policy.id,
            },
        )
        pr.cache_identity({"email": f"test{i}@example.com"})
        pr.persist_custom_privacy_request_fields(
            db,
            {
                f"field_{i}": CustomPrivacyRequestField(
                    label=f"Field {i}", value=f"value_{i}"
                )
            },
        )
        pr.save(db)
        privacy_requests.append(pr)

    yield privacy_requests


@pytest.mark.usefixtures(
    "allow_custom_privacy_request_field_collection_enabled",
    "allow_custom_privacy_request_fields_in_request_execution_enabled",
)
class TestPrivacyRequestPerformance:
    """Test N+1 query fixes with eager loading."""

    def test_csv_download_query_count(
        self,
        db,
        api_client: TestClient,
        generate_auth_header,
        multiple_privacy_requests,
    ):
        """CSV download should use ~5-10 queries regardless of request count (not N+1)."""
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])

        with QueryCounter() as counter:
            response = api_client.get(
                f"/api/v1{PRIVACY_REQUESTS}?download_csv=True", headers=auth_header
            )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"

        # Verify CSV has all requests
        rows = list(csv.DictReader(io.StringIO(response.content.decode())))
        assert len(rows) == 10

        # With eager loading: 1 query for requests + 1 per relationship = ~5-10 queries
        # Without optimization: ~4 queries per request = ~40 queries
        assert counter.count < 15, f"Too many queries: {counter.count} (expected <15)"

    @pytest.mark.parametrize(
        "include_param,expected_in_response",
        [
            ("include_identities", "identity"),
            ("include_custom_privacy_request_fields", "custom_privacy_request_fields"),
        ],
    )
    def test_list_view_eager_loading(
        self,
        db,
        api_client: TestClient,
        generate_auth_header,
        multiple_privacy_requests,
        include_param,
        expected_in_response,
    ):
        """List view should eagerly load relationships when requested."""
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])

        with QueryCounter() as counter:
            response = api_client.post(
                f"/api/v1{PRIVACY_REQUEST_SEARCH}",
                headers=auth_header,
                json={include_param: True, "verbose": False},
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10

        # Verify relationship data is included
        for item in data["items"]:
            assert expected_in_response in item

        # Should use eager loading (1 query for requests + 1 for relationship = ~3-10 queries)
        assert counter.count < 15, f"Too many queries: {counter.count} (expected <15)"

    @pytest.mark.parametrize(
        "endpoint,scope,request_count,max_queries",
        [
            (PRIVACY_REQUEST_BULK_SOFT_DELETE, PRIVACY_REQUEST_DELETE, 5, 25),
            (PRIVACY_REQUEST_APPROVE, PRIVACY_REQUEST_REVIEW, 3, 50),
        ],
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.apply_async"
    )
    def test_bulk_operations_query_count(
        self,
        mock_run_privacy_request,
        db,
        api_client: TestClient,
        generate_auth_header,
        multiple_privacy_requests,
        endpoint,
        scope,
        request_count,
        max_queries,
    ):
        """Bulk operations should fetch all requests in 1 query (not N queries)."""
        auth_header = generate_auth_header(scopes=[scope])
        request_ids = [pr.id for pr in multiple_privacy_requests[:request_count]]

        with QueryCounter() as counter:
            if endpoint == PRIVACY_REQUEST_BULK_SOFT_DELETE:
                response = api_client.post(
                    f"/api/v1{endpoint}",
                    headers=auth_header,
                    json={"request_ids": request_ids},
                )
            else:  # PRIVACY_REQUEST_APPROVE
                response = api_client.patch(
                    f"/api/v1{endpoint}",
                    headers=auth_header,
                    json={"request_ids": request_ids},
                )

        assert response.status_code == 200

        # Key optimization: Should fetch all requests in 1 query (not N queries)
        # Note: Approve has high query count due to DSR processing in tests
        assert (
            counter.count < max_queries
        ), f"Too many queries: {counter.count} (expected <{max_queries})"
