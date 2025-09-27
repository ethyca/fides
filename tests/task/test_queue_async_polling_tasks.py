from unittest import mock

import pytest

from fides.api.service.privacy_request.request_service import requeue_polling_tasks


class TestPollAsyncTasksStatus:

    @mock.patch("fides.api.task.execute_request_tasks.queue_request_task")
    def test_polling_task_is_requeued(
        self,
        mock_execute_polling_task,
        polling_request_task,
        in_processing_privacy_request,
    ):
        """Test that a task awaiting processing and marked as a polling task is requeued."""
        requeue_polling_tasks.apply().get()
        mock_execute_polling_task.assert_called_once_with(
            mock.ANY, privacy_request_proceed=True
        )

    @pytest.mark.usefixtures("non_async_request_task")
    @mock.patch("fides.api.task.execute_request_tasks.queue_request_task")
    def test_non_polling_task_is_not_requeued(self, mock_execute_polling_task):
        """Test that a task awaiting processing but not a polling task is not requeued."""
        requeue_polling_tasks.apply().get()
        mock_execute_polling_task.assert_not_called()

    @pytest.mark.usefixtures("in_progress_polling_request_task")
    @mock.patch("fides.api.task.execute_request_tasks.queue_request_task")
    def test_in_progress_polling_task_is_not_requeued(self, mock_execute_polling_task):
        """Test that a polling task not awaiting processing is not requeued."""
        requeue_polling_tasks.apply().get()
        mock_execute_polling_task.assert_not_called()

    @pytest.mark.usefixtures(
        "non_async_request_task", "in_progress_polling_request_task"
    )
    @mock.patch("fides.api.task.execute_request_tasks.queue_request_task")
    def test_no_matching_tasks_are_not_requeued(self, mock_execute_polling_task):
        """Test that no tasks are requeued when none meet the criteria."""
        requeue_polling_tasks.apply().get()
        mock_execute_polling_task.assert_not_called()

    @mock.patch("fides.api.task.execute_request_tasks.queue_request_task")
    def test_only_matching_task_is_requeued(
        self,
        mock_execute_polling_task,
        polling_request_task,
        non_async_request_task,
        in_progress_polling_request_task,
        in_processing_privacy_request,
    ):
        """Test that only the task that meets all criteria is requeued."""
        requeue_polling_tasks.apply().get()
        mock_execute_polling_task.assert_called_once_with(
            mock.ANY, privacy_request_proceed=True
        )
