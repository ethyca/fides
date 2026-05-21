"""Tests for requeue_requires_input_requests in connection_util.

ENG-3687: The function incorrectly requeues ALL requires_input DSRs when no
AccessManualWebhooks exist. DSRs paused by manual_task connections (which have
RequestTasks) should not be requeued — only DSRs paused by manual_webhook
connections (which have zero RequestTasks) should be affected.
"""

from unittest import mock

from fides.api.models.privacy_request import RequestTask
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.util.connection_util import requeue_requires_input_requests


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
