from unittest import mock

import pytest

from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.common.api.scope_registry import (
    PRIVACY_REQUEST_DELETE,
    PRIVACY_REQUEST_REVIEW,
)
from fides.common.api.v1.urn_registry import (
    PRIVACY_REQUEST_APPROVE,
    PRIVACY_REQUEST_BULK_FINALIZE,
    PRIVACY_REQUEST_BULK_SOFT_DELETE,
    PRIVACY_REQUEST_CANCEL,
    PRIVACY_REQUEST_DENY,
    V1_URL_PREFIX,
)


class TestBulkOperationsBatching:
    """Test that bulk operations correctly handle batching for large request lists."""

    @pytest.fixture(scope="function")
    def large_privacy_requests(self, db, policy):
        """Create more than BULK_PRIVACY_REQUEST_BATCH_SIZE privacy requests to test batching."""
        privacy_requests = []
        # Create 75 requests (more than the batch size of 50)
        request_count = 75
        for i in range(request_count):
            pr = PrivacyRequest.create(
                db=db,
                data={
                    "external_id": f"bulk_test_{i}",
                    "status": PrivacyRequestStatus.pending,
                    "policy_id": policy.id,
                    "client_id": policy.client_id,
                },
            )
            privacy_requests.append(pr)
        yield privacy_requests
        for pr in privacy_requests:
            pr.delete(db)

    @pytest.mark.parametrize(
        "operation,endpoint,method,scope,initial_status,expected_status,reason_required",
        [
            (
                "approve",
                PRIVACY_REQUEST_APPROVE,
                "patch",
                PRIVACY_REQUEST_REVIEW,
                PrivacyRequestStatus.pending,
                PrivacyRequestStatus.approved,
                False,
            ),
            (
                "deny",
                PRIVACY_REQUEST_DENY,
                "patch",
                PRIVACY_REQUEST_REVIEW,
                PrivacyRequestStatus.pending,
                PrivacyRequestStatus.denied,
                True,
            ),
            (
                "cancel",
                PRIVACY_REQUEST_CANCEL,
                "patch",
                PRIVACY_REQUEST_REVIEW,
                PrivacyRequestStatus.in_processing,
                PrivacyRequestStatus.canceled,
                False,
            ),
            (
                "soft_delete",
                PRIVACY_REQUEST_BULK_SOFT_DELETE,
                "post",
                PRIVACY_REQUEST_DELETE,
                PrivacyRequestStatus.pending,
                None,  # Soft delete doesn't change status, just sets deleted_at
                False,
            ),
        ],
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.apply_async"
    )
    @mock.patch(
        "fides.service.messaging.messaging_service.dispatch_message_task.apply_async"
    )
    def test_bulk_operations_with_batching(
        self,
        mock_dispatch_message,
        submit_mock,
        db,
        api_client,
        generate_auth_header,
        user,
        large_privacy_requests,
        operation,
        endpoint,
        method,
        scope,
        initial_status,
        expected_status,
        reason_required,
    ):
        """Test that bulk operations correctly process all requests across multiple batches."""
        # Set all requests to the initial status required for the operation
        for pr in large_privacy_requests:
            pr.update(db=db, data={"status": initial_status})
        db.commit()

        auth_header = generate_auth_header(scopes=[scope])
        request_ids = [pr.id for pr in large_privacy_requests]

        # Prepare request body
        body = {"request_ids": request_ids}
        if reason_required:
            body["reason"] = f"Bulk {operation} test reason"

        # Make the request
        url = V1_URL_PREFIX + endpoint
        if method == "patch":
            response = api_client.patch(url, headers=auth_header, json=body)
        else:  # post
            response = api_client.post(url, headers=auth_header, json=body)

        assert response.status_code == 200
        response_body = response.json()

        # Verify all requests were processed successfully
        assert len(response_body["succeeded"]) == len(large_privacy_requests)
        assert len(response_body["failed"]) == 0

        # Verify all requests have the expected status (or are soft deleted)
        db.expire_all()
        for pr in large_privacy_requests:
            db.refresh(pr)
            if operation == "soft_delete":
                assert pr.deleted_at is not None
                # Note: deleted_by may be None if oauth_client has no associated user
            else:
                assert pr.status == expected_status

        # Verify all request IDs are in the succeeded list
        # Note: soft_delete returns List[str], other operations return List[dict]
        if operation == "soft_delete":
            succeeded_ids = response_body["succeeded"]
        else:
            succeeded_ids = [r["id"] for r in response_body["succeeded"]]
        for pr in large_privacy_requests:
            assert pr.id in succeeded_ids

    @pytest.mark.parametrize(
        "operation,endpoint,method,scope,initial_status",
        [
            (
                "finalize",
                PRIVACY_REQUEST_BULK_FINALIZE,
                "post",
                PRIVACY_REQUEST_REVIEW,
                PrivacyRequestStatus.requires_manual_finalization,
            ),
        ],
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.apply_async"
    )
    def test_bulk_finalize_with_batching(
        self,
        submit_mock,
        db,
        api_client,
        generate_auth_header,
        user,
        large_privacy_requests,
        operation,
        endpoint,
        method,
        scope,
        initial_status,
    ):
        """Test that bulk finalize correctly processes all requests across multiple batches."""
        # Set all requests to requires_manual_finalization
        for pr in large_privacy_requests:
            pr.update(db=db, data={"status": initial_status})
        db.commit()

        auth_header = generate_auth_header(scopes=[scope])
        request_ids = [pr.id for pr in large_privacy_requests]

        # Make the request
        url = V1_URL_PREFIX + endpoint
        body = {"request_ids": request_ids}
        response = api_client.post(url, headers=auth_header, json=body)

        assert response.status_code == 200
        response_body = response.json()

        # Verify all requests were processed successfully
        assert len(response_body["succeeded"]) == len(large_privacy_requests)
        assert len(response_body["failed"]) == 0

        # Verify all requests have finalized_at set
        db.expire_all()
        for pr in large_privacy_requests:
            db.refresh(pr)
            assert pr.finalized_at is not None
            # Note: finalized_by may be None if oauth_client has no associated user

        # Verify all request IDs are in the succeeded list
        succeeded_ids = [r["id"] for r in response_body["succeeded"]]
        for pr in large_privacy_requests:
            assert pr.id in succeeded_ids
