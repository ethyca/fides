import uuid
from datetime import datetime, timedelta
from unittest import mock

import pytest

from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.models.privacy_request.request_task import AsyncTaskType
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.service.privacy_request.request_service import poll_async_tasks_status


class TestPollAsyncTasksStatus:
    @pytest.mark.usefixtures("polling_request_task")
    @mock.patch("fides.api.service.async_dsr.async_dsr_service.requeue_polling_request")
    def test_polling_task_is_requeued(self, mock_requeue_polling_request):
        """Test that a task awaiting processing and marked as a polling task is requeued."""
        poll_async_tasks_status.apply().get()
        mock_requeue_polling_request.assert_called_once()

    @pytest.mark.usefixtures("non_async_request_task")
    @mock.patch("fides.api.service.async_dsr.async_dsr_service.requeue_polling_request")
    def test_non_polling_task_is_not_requeued(self, mock_requeue_polling_request):
        """Test that a task awaiting processing but not a polling task is not requeued."""
        poll_async_tasks_status.apply().get()
        mock_requeue_polling_request.assert_not_called()

    @pytest.mark.usefixtures("in_progress_polling_request_task")
    @mock.patch("fides.api.service.async_dsr.async_dsr_service.requeue_polling_request")
    def test_in_progress_polling_task_is_not_requeued(
        self, mock_requeue_polling_request
    ):
        """Test that a polling task not awaiting processing is not requeued."""
        poll_async_tasks_status.apply().get()
        mock_requeue_polling_request.assert_not_called()

    @pytest.mark.usefixtures(
        "non_async_request_task", "in_progress_polling_request_task"
    )
    @mock.patch("fides.api.service.async_dsr.async_dsr_service.requeue_polling_request")
    def test_no_matching_tasks_are_not_requeued(self, mock_requeue_polling_request):
        """Test that no tasks are requeued when none meet the criteria."""
        poll_async_tasks_status.apply().get()
        mock_requeue_polling_request.assert_not_called()

    @pytest.mark.usefixtures(
        "polling_request_task",
        "non_async_request_task",
        "in_progress_polling_request_task",
    )
    @mock.patch("fides.api.service.async_dsr.async_dsr_service.requeue_polling_request")
    def test_only_matching_task_is_requeued(self, mock_requeue_polling_request):
        """Test that only the task that meets all criteria is requeued."""
        poll_async_tasks_status.apply().get()
        mock_requeue_polling_request.assert_called_once()
