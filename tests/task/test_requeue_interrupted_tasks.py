import uuid
from datetime import datetime, timedelta
from unittest import mock

import pytest

from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import ExecutionLogStatus, PrivacyRequestStatus
from fides.api.service.privacy_request.request_service import (
    REQUEUE_INTERRUPTED_TASKS_LOCK,
    requeue_interrupted_tasks,
)
from fides.api.util.cache import cache_task_tracking_key, get_cache


@pytest.fixture
def in_progress_privacy_request(db, policy):
    """Create a privacy request in the in_processing state"""
    # Create the privacy request
    privacy_request = PrivacyRequest.create(
        db=db,
        data={
            "external_id": f"ext-{str(uuid.uuid4())}",
            "started_processing_at": datetime.utcnow(),
            "requested_at": datetime.utcnow() - timedelta(days=1),
            "status": PrivacyRequestStatus.in_processing,
            "origin": "https://example.com/testing",
            "policy_id": policy.id,
            "client_id": policy.client_id,
        },
    )

    # Cache the task ID for the privacy request
    cache_task_tracking_key(privacy_request.id, "privacy_request_task_id")

    yield privacy_request

    # Clean up
    privacy_request.delete(db)


@pytest.fixture
def in_progress_request_task(db, in_progress_privacy_request):
    """Create a request task in the in_processing state for an existing privacy request"""
    # Create a single request task for the privacy request
    request_task = RequestTask.create(
        db,
        data={
            "action_type": ActionType.access,
            "status": ExecutionLogStatus.in_processing,
            "privacy_request_id": in_progress_privacy_request.id,
            "collection_address": "test_dataset:customer",
            "dataset_name": "test_dataset",
            "collection_name": "customer",
            "upstream_tasks": [],
            "downstream_tasks": [],
        },
    )

    # Cache the task ID for the request task
    cache_task_tracking_key(request_task.id, "request_task_id")

    yield request_task

    # Clean up
    request_task.delete(db)


class TestRequeueInterruptedTasks:
    @pytest.mark.usefixtures("in_progress_privacy_request", "in_progress_request_task")
    @mock.patch(
        "fides.service.privacy_request.privacy_request_service._requeue_privacy_request"
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_service._get_task_ids_from_dsr_queue",
        return_value=[],
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_service.celery_tasks_in_flight",
        return_value=True,
    )
    def test_active_request_task_is_not_requeued(
        self,
        mock_celery_tasks_in_flight,
        mock_get_task_ids_from_dsr_queue,
        mock_requeue_privacy_request,
    ):
        """Test that active request tasks are not requeued.

        When a privacy request task is active (in flight), even if not in the queue,
        the privacy request should not be requeued.
        """
        requeue_interrupted_tasks.apply().get()
        mock_requeue_privacy_request.assert_not_called()

    @pytest.mark.usefixtures("in_progress_privacy_request")
    @mock.patch(
        "fides.service.privacy_request.privacy_request_service._requeue_privacy_request"
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_service._get_task_ids_from_dsr_queue",
        return_value=[],
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_service.celery_tasks_in_flight",
        return_value=False,
    )
    def test_interrupted_privacy_request_with_no_request_tasks_is_requeued(
        self,
        mock_celery_tasks_in_flight,
        mock_get_task_ids_from_dsr_queue,
        mock_requeue_privacy_request,
    ):
        """Test that interrupted privacy requests with no request tasks are requeued.

        When a privacy request has been interrupted and has no request tasks,
        it should be requeued.
        """
        requeue_interrupted_tasks.apply().get()
        mock_requeue_privacy_request.assert_called_once()

    @pytest.mark.usefixtures("in_progress_privacy_request", "in_progress_request_task")
    @mock.patch(
        "fides.service.privacy_request.privacy_request_service._requeue_privacy_request"
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_service._get_task_ids_from_dsr_queue",
        return_value=[],
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_service.celery_tasks_in_flight"
    )
    def test_interrupted_privacy_request_with_active_request_tasks_is_not_requeued(
        self,
        mock_celery_tasks_in_flight,
        mock_get_task_ids_from_dsr_queue,
        mock_requeue_privacy_request,
    ):
        """Test that interrupted privacy requests with active request tasks are not requeued.

        When a privacy request has been interrupted but its request tasks are still active,
        the privacy request should not be requeued.
        """
        # Main task is not active, but the subtask is active
        mock_celery_tasks_in_flight.side_effect = [False, True]

        requeue_interrupted_tasks.apply().get()
        mock_requeue_privacy_request.assert_not_called()

    @pytest.mark.usefixtures("in_progress_privacy_request", "in_progress_request_task")
    @mock.patch(
        "fides.service.privacy_request.privacy_request_service._requeue_privacy_request"
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_service._get_task_ids_from_dsr_queue",
        return_value=[],
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_service.celery_tasks_in_flight"
    )
    def test_interrupted_privacy_request_with_inactive_request_tasks_is_requeued(
        self,
        mock_celery_tasks_in_flight,
        mock_get_task_ids_from_dsr_queue,
        mock_requeue_privacy_request,
    ):
        """Test that interrupted privacy requests with inactive request tasks are requeued.

        When both the privacy request and its request tasks have been interrupted,
        the privacy request should be requeued.
        """
        # Both main task and subtask are not active
        mock_celery_tasks_in_flight.side_effect = [False, False]

        requeue_interrupted_tasks.apply().get()
        mock_requeue_privacy_request.assert_called_once()

    @pytest.mark.usefixtures("in_progress_privacy_request")
    @mock.patch(
        "fides.service.privacy_request.privacy_request_service._requeue_privacy_request"
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_service.get_cached_task_id",
        return_value=None,
    )
    def test_privacy_request_with_no_cached_task_id_is_skipped(
        self, mock_get_cached_task_id, mock_requeue_privacy_request
    ):
        """Test that privacy requests with no cached task ID are skipped.

        When a privacy request has no cached task ID, we can't determine if it's active,
        so it should be skipped (not requeued).
        """
        requeue_interrupted_tasks.apply().get()
        mock_requeue_privacy_request.assert_not_called()

    @pytest.mark.usefixtures("in_progress_privacy_request", "in_progress_request_task")
    @mock.patch(
        "fides.service.privacy_request.privacy_request_service._requeue_privacy_request"
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_service._get_task_ids_from_dsr_queue"
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_service.celery_tasks_in_flight",
        return_value=False,
    )
    def test_request_task_with_no_cached_subtask_id_is_skipped(
        self,
        mock_celery_tasks_in_flight,
        mock_get_task_ids_from_dsr_queue,
        mock_requeue_privacy_request,
    ):
        """Test that request tasks with no cached subtask ID are skipped.

        When a privacy request's main task is inactive but its request task has no cached subtask ID,
        we can't determine if the subtask is active, so the privacy request should not be requeued.
        """
        mock_get_task_ids_from_dsr_queue.return_value = []

        # Return None for the subtask ID, but a valid ID for the main task
        with mock.patch(
            "fides.api.service.privacy_request.request_service.get_cached_task_id",
            side_effect=["privacy_request_task_id", None],
        ):
            requeue_interrupted_tasks.apply().get()
            mock_requeue_privacy_request.assert_not_called()

    @pytest.mark.usefixtures("in_progress_privacy_request")
    @mock.patch(
        "fides.service.privacy_request.privacy_request_service._requeue_privacy_request"
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_service._get_task_ids_from_dsr_queue"
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_service.celery_tasks_in_flight",
        return_value=False,
    )
    def test_task_in_queue_is_not_requeued(
        self,
        mock_celery_tasks_in_flight,
        mock_get_task_ids_from_dsr_queue,
        mock_requeue_privacy_request,
    ):
        """Test that tasks present in the queue are not requeued.

        When a privacy request's task ID is found in the queue,
        the privacy request should not be requeued, regardless of in-flight status.
        """
        # The task is in the queue
        mock_get_task_ids_from_dsr_queue.return_value = ["privacy_request_task_id"]

        requeue_interrupted_tasks.apply().get()
        mock_requeue_privacy_request.assert_not_called()

    def test_aquired_locks_prevent_duplicate_runs(self, loguru_caplog):
        """Test that multiple instances of the task do not run simultaneously.

        When the task is already running, another instance should not acquire the lock.
        """

        redis_conn = get_cache()
        lock = redis_conn.lock(REQUEUE_INTERRUPTED_TASKS_LOCK, timeout=600)
        lock.acquire(blocking=False)

        requeue_interrupted_tasks.apply().get()
        assert (
            "Another instance of requeue_interrupted_tasks is already running. Skipping this execution."
            in loguru_caplog.text
        )
        lock.release()

    def test_lock_is_released_after_execution(self):
        """Test that the lock is released after the task is executed.

        When the task is executed, the lock should be released.
        """
        redis_conn = get_cache()
        lock = redis_conn.lock(REQUEUE_INTERRUPTED_TASKS_LOCK, timeout=600)

        requeue_interrupted_tasks.apply().get()
        assert not lock.owned()
