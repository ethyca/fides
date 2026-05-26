"""Tests for requeue_requires_input_requests in connection_util.

The function incorrectly requeues ALL requires_input DSRs when no
AccessManualWebhooks exist. DSRs paused by manual_task connections (which have
RequestTasks) should not be requeued — only DSRs paused by manual_webhook
connections (which have zero RequestTasks) should be affected.
"""

from unittest import mock

import pytest

from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.util.connection_util import requeue_requires_input_requests


@pytest.fixture()
def second_privacy_request(db, policy) -> PrivacyRequest:
    """A second privacy request for coexistence tests."""
    pr = PrivacyRequest.create(
        db=db,
        data={
            "requested_at": None,
            "policy_id": policy.id,
            "status": PrivacyRequestStatus.requires_input,
        },
    )
    yield pr
    pr.delete(db)


class TestRequeueRequiresInputRequests:
    """requeue_requires_input_requests should only requeue manual_webhook DSRs."""

    def test_dsr_with_request_tasks_not_requeued(self, db, privacy_request):
        """A requires_input DSR with RequestTasks (manual_task) should not be requeued."""
        privacy_request.status = PrivacyRequestStatus.requires_input
        privacy_request.save(db)

        # Create a RequestTask — simulates a manual_task DSR paused in-graph
        request_task = RequestTask.create(
            db,
            data={
                "privacy_request_id": privacy_request.id,
                "action_type": ActionType.access,
                "status": ExecutionLogStatus.awaiting_processing,
                "collection_address": "manual_dataset:manual_collection",
                "dataset_name": "manual_dataset",
                "collection_name": "manual_collection",
                "upstream_tasks": [],
                "downstream_tasks": [],
                "all_descendant_tasks": [],
            },
        )

        try:
            # No AccessManualWebhooks exist — guard passes
            requeue_requires_input_requests(db)

            db.refresh(privacy_request)
            assert privacy_request.status == PrivacyRequestStatus.requires_input
        finally:
            request_task.delete(db)

    @mock.patch("fides.api.util.connection_util.queue_privacy_request")
    def test_dsr_without_request_tasks_is_requeued(
        self, mock_queue, db, privacy_request
    ):
        """A requires_input DSR with no RequestTasks (manual_webhook) should be requeued."""
        privacy_request.status = PrivacyRequestStatus.requires_input
        privacy_request.save(db)

        # No RequestTasks — DSR was paused pre-graph by a manual_webhook
        # No AccessManualWebhooks exist — guard passes
        requeue_requires_input_requests(db)

        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.in_processing
        mock_queue.assert_called_once_with(privacy_request_id=privacy_request.id)

    @mock.patch("fides.api.util.connection_util.queue_privacy_request")
    def test_coexistence_only_webhook_dsr_requeued(
        self, mock_queue, db, privacy_request, second_privacy_request
    ):
        """When both webhook and task DSRs are in requires_input, only the webhook DSR is requeued."""
        # DSR 1: manual_webhook (no RequestTasks)
        privacy_request.status = PrivacyRequestStatus.requires_input
        privacy_request.save(db)

        # DSR 2: manual_task (has RequestTasks)
        second_privacy_request.status = PrivacyRequestStatus.requires_input
        second_privacy_request.save(db)
        request_task = RequestTask.create(
            db,
            data={
                "privacy_request_id": second_privacy_request.id,
                "action_type": ActionType.access,
                "status": ExecutionLogStatus.awaiting_processing,
                "collection_address": "manual_dataset:manual_collection",
                "dataset_name": "manual_dataset",
                "collection_name": "manual_collection",
                "upstream_tasks": [],
                "downstream_tasks": [],
                "all_descendant_tasks": [],
            },
        )

        try:
            requeue_requires_input_requests(db)

            db.refresh(privacy_request)
            db.refresh(second_privacy_request)

            # Webhook DSR requeued
            assert privacy_request.status == PrivacyRequestStatus.in_processing
            # Manual task DSR untouched
            assert second_privacy_request.status == PrivacyRequestStatus.requires_input
            # Only one DSR was queued
            mock_queue.assert_called_once_with(privacy_request_id=privacy_request.id)
        finally:
            request_task.delete(db)
