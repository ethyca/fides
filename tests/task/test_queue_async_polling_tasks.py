import uuid
from datetime import datetime, timedelta
from unittest import mock

import pytest

from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.service.privacy_request.request_service import poll_async_tasks_status


@pytest.fixture
def pending_privacy_request(db, policy):
    """Create a privacy request in the pending state"""
    privacy_request = PrivacyRequest.create(
        db=db,
        data={
            "external_id": f"ext-{str(uuid.uuid4())}",
            "started_processing_at": datetime.utcnow(),
            "requested_at": datetime.utcnow() - timedelta(days=1),
            "status": PrivacyRequestStatus.pending,
            "origin": "https://example.com/testing",
            "policy_id": policy.id,
            "client_id": policy.client_id,
        },
    )
    yield privacy_request
    privacy_request.delete(db)


@pytest.fixture
def polling_request_task(db, pending_privacy_request):
    """Create a request task that is awaiting processing and is a polling task"""
    request_task = RequestTask.create(
        db,
        data={
            "action_type": ActionType.access,
            "status": ExecutionLogStatus.awaiting_processing,
            "privacy_request_id": pending_privacy_request.id,
            "collection_address": "test_dataset:customer",
            "dataset_name": "test_dataset",
            "collection_name": "customer",
            "upstream_tasks": [],
            "downstream_tasks": [],
            "polling_async_task": True,
        },
    )
    yield request_task
    request_task.delete(db)


@pytest.fixture
def non_polling_request_task(db, pending_privacy_request):
    """Create a request task that is awaiting processing but is not a polling task"""
    request_task = RequestTask.create(
        db,
        data={
            "action_type": ActionType.access,
            "status": ExecutionLogStatus.awaiting_processing,
            "privacy_request_id": pending_privacy_request.id,
            "collection_address": "test_dataset:customer",
            "dataset_name": "test_dataset",
            "collection_name": "customer",
            "upstream_tasks": [],
            "downstream_tasks": [],
            "polling_async_task": False,
        },
    )
    yield request_task
    request_task.delete(db)


@pytest.fixture
def in_progress_polling_request_task(db, pending_privacy_request):
    """Create a request task that is in progress and is a polling task"""
    request_task = RequestTask.create(
        db,
        data={
            "action_type": ActionType.access,
            "status": ExecutionLogStatus.in_processing,
            "privacy_request_id": pending_privacy_request.id,
            "collection_address": "test_dataset:customer",
            "dataset_name": "test_dataset",
            "collection_name": "customer",
            "upstream_tasks": [],
            "downstream_tasks": [],
            "polling_async_task": True,
        },
    )
    yield request_task
    request_task.delete(db)


class TestPollAsyncTasksStatus:
    @pytest.mark.usefixtures("polling_request_task")
    @mock.patch(
        "fides.service.privacy_request.privacy_request_service._requeue_polling_request"
    )
    def test_polling_task_is_requeued(self, mock_requeue_polling_request):
        """Test that a task awaiting processing and marked as a polling task is requeued."""
        poll_async_tasks_status.apply().get()
        mock_requeue_polling_request.assert_called_once()

    @pytest.mark.usefixtures("non_polling_request_task")
    @mock.patch(
        "fides.service.privacy_request.privacy_request_service._requeue_polling_request"
    )
    def test_non_polling_task_is_not_requeued(self, mock_requeue_polling_request):
        """Test that a task awaiting processing but not a polling task is not requeued."""
        poll_async_tasks_status.apply().get()
        mock_requeue_polling_request.assert_not_called()

    @pytest.mark.usefixtures("in_progress_polling_request_task")
    @mock.patch(
        "fides.service.privacy_request.privacy_request_service._requeue_polling_request"
    )
    def test_in_progress_polling_task_is_not_requeued(
        self, mock_requeue_polling_request
    ):
        """Test that a polling task not awaiting processing is not requeued."""
        poll_async_tasks_status.apply().get()
        mock_requeue_polling_request.assert_not_called()

    @pytest.mark.usefixtures(
        "non_polling_request_task", "in_progress_polling_request_task"
    )
    @mock.patch(
        "fides.service.privacy_request.privacy_request_service._requeue_polling_request"
    )
    def test_no_matching_tasks_are_not_requeued(self, mock_requeue_polling_request):
        """Test that no tasks are requeued when none meet the criteria."""
        poll_async_tasks_status.apply().get()
        mock_requeue_polling_request.assert_not_called()

    @pytest.mark.usefixtures(
        "polling_request_task",
        "non_polling_request_task",
        "in_progress_polling_request_task",
    )
    @mock.patch(
        "fides.service.privacy_request.privacy_request_service._requeue_polling_request"
    )
    def test_only_matching_task_is_requeued(self, mock_requeue_polling_request):
        """Test that only the task that meets all criteria is requeued."""
        poll_async_tasks_status.apply().get()
        mock_requeue_polling_request.assert_called_once()
