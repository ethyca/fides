from unittest import mock

import pytest

from fides.api.service.privacy_request.request_service import poll_async_tasks_status
from fides.api.tasks import DSR_QUEUE_NAME


class TestPollAsyncTasksStatus:

    @mock.patch("fides.api.service.async_dsr.async_dsr_service.execute_polling_task")
    def test_polling_task_is_requeued(
        self,
        mock_execute_polling_task,
        polling_request_task,
        in_processing_privacy_request,
    ):
        """Test that a task awaiting processing and marked as a polling task is requeued."""
        poll_async_tasks_status.apply().get()
        mock_execute_polling_task.apply_async.assert_called_once_with(
            queue=DSR_QUEUE_NAME,
            kwargs={
                "polling_task_id": polling_request_task.id,
                "privacy_request_id": in_processing_privacy_request.id,
            },
        )

    @pytest.mark.usefixtures("non_async_request_task")
    @mock.patch("fides.api.service.async_dsr.async_dsr_service.execute_polling_task")
    def test_non_polling_task_is_not_requeued(self, mock_execute_polling_task):
        """Test that a task awaiting processing but not a polling task is not requeued."""
        poll_async_tasks_status.apply().get()
        mock_execute_polling_task.assert_not_called()

    @pytest.mark.usefixtures("in_progress_polling_request_task")
    @mock.patch("fides.api.service.async_dsr.async_dsr_service.execute_polling_task")
    def test_in_progress_polling_task_is_not_requeued(self, mock_execute_polling_task):
        """Test that a polling task not awaiting processing is not requeued."""
        poll_async_tasks_status.apply().get()
        mock_execute_polling_task.assert_not_called()

    @pytest.mark.usefixtures(
        "non_async_request_task", "in_progress_polling_request_task"
    )
    @mock.patch("fides.api.service.async_dsr.async_dsr_service.execute_polling_task")
    def test_no_matching_tasks_are_not_requeued(self, mock_execute_polling_task):
        """Test that no tasks are requeued when none meet the criteria."""
        poll_async_tasks_status.apply().get()
        mock_execute_polling_task.assert_not_called()

    @mock.patch("fides.api.service.async_dsr.async_dsr_service.execute_polling_task")
    def test_only_matching_task_is_requeued(
        self,
        mock_execute_polling_task,
        polling_request_task,
        non_async_request_task,
        in_progress_polling_request_task,
        in_processing_privacy_request,
    ):
        """Test that only the task that meets all criteria is requeued."""
        poll_async_tasks_status.apply().get()
        mock_execute_polling_task.apply_async.assert_called_once_with(
            queue=DSR_QUEUE_NAME,
            kwargs={
                "polling_task_id": polling_request_task.id,
                "privacy_request_id": in_processing_privacy_request.id,
            },
        )
