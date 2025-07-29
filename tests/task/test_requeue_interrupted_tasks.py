import uuid
from datetime import datetime, timedelta
from unittest import mock

import pytest

from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import PrivacyRequestStatus
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
        """Test that interrupted privacy requests without request tasks are requeued.

        When a privacy request has no request tasks but has a cached task ID,
        indicating it was interrupted, it should be requeued.
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
        "fides.api.service.privacy_request.request_service.celery_tasks_in_flight",
        return_value=False,
    )
    def test_interrupted_privacy_request_with_active_request_tasks_is_not_requeued(
        self,
        mock_celery_tasks_in_flight,
        mock_get_task_ids_from_dsr_queue,
        mock_requeue_privacy_request,
    ):
        """Test that interrupted privacy requests with active request tasks are not requeued.

        When a privacy request has request tasks that are active,
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
    def test_interrupted_privacy_request_with_inactive_request_tasks_is_requeued(
        self,
        mock_celery_tasks_in_flight,
        mock_get_task_ids_from_dsr_queue,
        mock_requeue_privacy_request,
        db,
        policy,
    ):
        """Test that interrupted privacy requests with inactive request tasks are requeued.

        When a privacy request has request tasks that are no longer active,
        the privacy request should be requeued.
        """
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

        # Create a request task that is not active (not in in_processing status)
        request_task = RequestTask.create(
            db,
            data={
                "action_type": ActionType.access,
                "status": ExecutionLogStatus.pending,  # Not in_processing
                "privacy_request_id": privacy_request.id,
                "collection_address": "test_dataset:customer",
                "dataset_name": "test_dataset",
                "collection_name": "customer",
                "upstream_tasks": [],
                "downstream_tasks": [],
            },
        )

        # Cache the task ID for the request task
        cache_task_tracking_key(request_task.id, "request_task_id")

        try:
            requeue_interrupted_tasks.apply().get()
            mock_requeue_privacy_request.assert_called_once()
        finally:
            # Clean up
            request_task.delete(db)
            privacy_request.delete(db)

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
    def test_privacy_request_with_no_cached_task_id_is_skipped(
        self,
        mock_celery_tasks_in_flight,
        mock_get_task_ids_from_dsr_queue,
        mock_requeue_privacy_request,
        db,
        policy,
    ):
        """Test that privacy requests without cached task IDs are skipped.

        When a privacy request doesn't have a cached task ID, it should be skipped.
        """
        # Create a privacy request without caching a task ID
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

        try:
            requeue_interrupted_tasks.apply().get()
            mock_requeue_privacy_request.assert_not_called()
        finally:
            # Clean up
            privacy_request.delete(db)

    @pytest.mark.usefixtures("in_progress_privacy_request", "in_progress_request_task")
    @mock.patch(
        "fides.service.privacy_request.privacy_request_service._requeue_privacy_request"
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_service.celery_tasks_in_flight",
        return_value=False,
    )
    def test_request_task_with_no_cached_subtask_id_is_skipped(
        self,
        mock_celery_tasks_in_flight,
        mock_requeue_privacy_request,
        db,
        policy,
    ):
        """Test that request tasks without cached subtask IDs are skipped.

        When a request task doesn't have a cached subtask ID, it should be skipped.
        """
        # Create a privacy request and request task without caching subtask IDs
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

        request_task = RequestTask.create(
            db,
            data={
                "action_type": ActionType.access,
                "status": ExecutionLogStatus.in_processing,
                "privacy_request_id": privacy_request.id,
                "collection_address": "test_dataset:customer",
                "dataset_name": "test_dataset",
                "collection_name": "customer",
                "upstream_tasks": [],
                "downstream_tasks": [],
            },
        )
        # Do NOT cache the subtask ID for the request task

        try:
            requeue_interrupted_tasks.apply().get()
            mock_requeue_privacy_request.assert_not_called()
        finally:
            # Clean up
            request_task.delete(db)
            privacy_request.delete(db)

    @pytest.mark.usefixtures("in_progress_privacy_request", "in_progress_request_task")
    @mock.patch(
        "fides.service.privacy_request.privacy_request_service._requeue_privacy_request"
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_service.celery_tasks_in_flight",
        return_value=False,
    )
    def test_task_in_queue_is_not_requeued(
        self,
        mock_celery_tasks_in_flight,
        mock_requeue_privacy_request,
        mock_get_task_ids_from_dsr_queue,
    ):
        """Test that tasks already in the queue are not requeued.

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
            "Another process is already running for lock 'requeue_interrupted_tasks_lock'. Skipping this execution."
            in loguru_caplog.text
        )

        # Only release if we still own the lock
        if lock.owned():
            lock.release()

    def test_lock_is_released_after_execution(self):
        """Test that the lock is released after the task is executed.

        When the task is executed, the lock should be released.
        """
        redis_conn = get_cache()
        lock = redis_conn.lock(REQUEUE_INTERRUPTED_TASKS_LOCK, timeout=600)

        requeue_interrupted_tasks.apply().get()
        assert not lock.owned()


class TestEnhancedRequeueInterruptedTasks:
    """Test the enhanced requeue functionality with retry limits and cancellation."""

    @pytest.fixture
    def privacy_request_with_high_retry_count(self, db, policy):
        """Create a privacy request that has already been retried multiple times."""
        from fides.api.util.cache import increment_privacy_request_retry_count

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
        cache_task_tracking_key(privacy_request.id, "high_retry_task_id")

        # Increment retry count to near the limit (2 is near limit of 3)
        for _ in range(2):  # Set to 2, limit is 3
            increment_privacy_request_retry_count(privacy_request.id)

        yield privacy_request

        # Clean up
        privacy_request.delete(db)

    @pytest.fixture
    def privacy_request_over_retry_limit(self, db, policy):
        """Create a privacy request that has exceeded the retry limit."""
        from fides.api.util.cache import increment_privacy_request_retry_count

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
        cache_task_tracking_key(privacy_request.id, "over_limit_task_id")

        # Increment retry count beyond the limit (4 is over limit of 3)
        for _ in range(4):  # Set to 4, limit is 3
            increment_privacy_request_retry_count(privacy_request.id)

        yield privacy_request

        # Clean up
        privacy_request.delete(db)

    @pytest.fixture
    def false_completion_privacy_request(self, db, policy):
        """Create a privacy request that appears falsely completed."""
        # Create the privacy request as completed
        privacy_request = PrivacyRequest.create(
            db=db,
            data={
                "external_id": f"ext-{str(uuid.uuid4())}",
                "started_processing_at": datetime.utcnow() - timedelta(minutes=15),
                "finished_processing_at": datetime.utcnow() - timedelta(minutes=5),
                "requested_at": datetime.utcnow() - timedelta(days=1),
                "status": PrivacyRequestStatus.complete,
                "origin": "https://example.com/testing",
                "policy_id": policy.id,
                "client_id": policy.client_id,
            },
        )

        # Create incomplete request task (this makes it a false completion)
        request_task = RequestTask.create(
            db,
            data={
                "action_type": ActionType.access,
                "status": ExecutionLogStatus.in_processing,  # Still in processing
                "privacy_request_id": privacy_request.id,
                "collection_address": "test_dataset:customer",
                "dataset_name": "test_dataset",
                "collection_name": "customer",
                "upstream_tasks": [],
                "downstream_tasks": [],
            },
        )

        # Cache the task ID
        cache_task_tracking_key(privacy_request.id, "false_complete_task_id")

        yield privacy_request

        # Clean up
        request_task.delete(db)
        privacy_request.delete(db)

    @pytest.mark.usefixtures("privacy_request_with_high_retry_count")
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
    @mock.patch(
        "fides.api.service.privacy_request.request_service._detect_false_completions",
        return_value=[],
    )
    def test_privacy_request_near_retry_limit_is_requeued(
        self,
        mock_detect_false_completions,
        mock_celery_tasks_in_flight,
        mock_get_task_ids_from_dsr_queue,
        mock_requeue_privacy_request,
    ):
        """Test that privacy requests near but not over the retry limit are still requeued."""
        requeue_interrupted_tasks.apply().get()
        mock_requeue_privacy_request.assert_called_once()

    @pytest.mark.usefixtures("privacy_request_over_retry_limit")
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
    @mock.patch(
        "fides.api.service.privacy_request.request_service._detect_false_completions",
        return_value=[],
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_service._cancel_interrupted_tasks_and_error_privacy_request"
    )
    def test_privacy_request_over_retry_limit_is_canceled(
        self,
        mock_cancel_interrupted_tasks,
        mock_detect_false_completions,
        mock_celery_tasks_in_flight,
        mock_get_task_ids_from_dsr_queue,
        mock_requeue_privacy_request,
    ):
        """Test that privacy requests over the retry limit are canceled instead of requeued."""
        requeue_interrupted_tasks.apply().get()

        # Should not requeue
        mock_requeue_privacy_request.assert_not_called()

        # Should cancel the tasks and error the request
        mock_cancel_interrupted_tasks.assert_called_once()

    @pytest.mark.usefixtures("false_completion_privacy_request")
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
    @mock.patch(
        "fides.api.service.privacy_request.request_service.get_cached_task_id",
        return_value="false_complete_task_id",
    )
    def test_false_completion_is_requeued(
        self,
        mock_get_cached_task_id,
        mock_celery_tasks_in_flight,
        mock_get_task_ids_from_dsr_queue,
        mock_requeue_privacy_request,
    ):
        """Test that false completions are detected and requeued."""
        requeue_interrupted_tasks.apply().get()

        # Should requeue the falsely completed request
        mock_requeue_privacy_request.assert_called_once()

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
    @mock.patch(
        "fides.api.service.privacy_request.request_service._detect_false_completions"
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_service._cancel_interrupted_tasks_and_error_privacy_request"
    )
    def test_false_completion_over_retry_limit_is_canceled(
        self,
        mock_cancel_interrupted_tasks,
        mock_detect_false_completions,
        mock_celery_tasks_in_flight,
        mock_get_task_ids_from_dsr_queue,
        mock_requeue_privacy_request,
        false_completion_privacy_request,
    ):
        """Test that false completions over retry limit are canceled instead of requeued."""
        from fides.api.util.cache import increment_privacy_request_retry_count

        # Set up false completion that's over retry limit
        privacy_request = false_completion_privacy_request

        # Increment retry count beyond the limit
        for _ in range(6):  # Set to 6, limit is 5
            increment_privacy_request_retry_count(privacy_request.id)

        # Mock false completion detection to return this request
        mock_detect_false_completions.return_value = [privacy_request]

        requeue_interrupted_tasks.apply().get()

        # Should not requeue
        mock_requeue_privacy_request.assert_not_called()

        # Should cancel the tasks and error the request
        mock_cancel_interrupted_tasks.assert_called_once()

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
    @mock.patch(
        "fides.api.service.privacy_request.request_service._detect_false_completions",
        return_value=[],
    )
    @mock.patch(
        "fides.api.util.cache.get_privacy_request_retry_count",
        side_effect=Exception("Cache error"),
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_service._cancel_interrupted_tasks_and_error_privacy_request"
    )
    def test_cache_error_during_retry_count_check_causes_cancellation(
        self,
        mock_cancel_interrupted_tasks,
        mock_get_retry_count,
        mock_detect_false_completions,
        mock_celery_tasks_in_flight,
        mock_get_task_ids_from_dsr_queue,
        mock_requeue_privacy_request,
    ):
        """Test that cache errors during retry count check cause cancellation instead of requeue."""
        requeue_interrupted_tasks.apply().get()

        # Should not requeue due to cache error
        mock_requeue_privacy_request.assert_not_called()

        # Should cancel due to inability to check retry count
        mock_cancel_interrupted_tasks.assert_called_once()

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
    @mock.patch(
        "fides.api.service.privacy_request.request_service._detect_false_completions",
        return_value=[],
    )
    @mock.patch(
        "fides.api.util.cache.increment_privacy_request_retry_count",
        side_effect=Exception("Cache error"),
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_service._cancel_interrupted_tasks_and_error_privacy_request"
    )
    def test_cache_error_during_retry_increment_causes_cancellation(
        self,
        mock_cancel_interrupted_tasks,
        mock_increment_retry_count,
        mock_detect_false_completions,
        mock_celery_tasks_in_flight,
        mock_get_task_ids_from_dsr_queue,
        mock_requeue_privacy_request,
    ):
        """Test that cache errors during retry increment cause cancellation instead of requeue."""
        requeue_interrupted_tasks.apply().get()

        # Should not requeue due to cache error
        mock_requeue_privacy_request.assert_not_called()

        # Should cancel due to inability to increment retry count
        mock_cancel_interrupted_tasks.assert_called_once()

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
    @mock.patch(
        "fides.api.service.privacy_request.request_service._detect_false_completions",
        return_value=[],
    )
    @mock.patch("fides.api.util.cache.reset_privacy_request_retry_count")
    def test_successful_requeue_resets_retry_count(
        self,
        mock_reset_retry_count,
        mock_detect_false_completions,
        mock_celery_tasks_in_flight,
        mock_get_task_ids_from_dsr_queue,
        mock_requeue_privacy_request,
    ):
        """Test that successful requeue resets the retry count."""
        requeue_interrupted_tasks.apply().get()

        # Should requeue the request
        mock_requeue_privacy_request.assert_called_once()

        # Should reset retry count after successful requeue
        mock_reset_retry_count.assert_called()

    @pytest.mark.usefixtures("in_progress_privacy_request")
    @mock.patch("fides.api.service.privacy_request.request_service.logger")
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
    @mock.patch(
        "fides.api.service.privacy_request.request_service._detect_false_completions",
        return_value=[],
    )
    def test_requeue_with_retry_count_logging(
        self,
        mock_detect_false_completions,
        mock_celery_tasks_in_flight,
        mock_get_task_ids_from_dsr_queue,
        mock_requeue_privacy_request,
        mock_logger,
    ):
        """Test that retry count is logged during requeue operations."""
        requeue_interrupted_tasks.apply().get()

        # Should log retry count information
        info_calls = [call.args[0] for call in mock_logger.info.call_args_list]
        retry_log_found = any("retry count" in str(call).lower() for call in info_calls)
        assert retry_log_found, "Expected retry count to be logged"

    def test_retry_limit_configuration(self):
        """Test that retry limit configuration changes are respected."""
        from fides.config import CONFIG

        # Test default value
        original_value = CONFIG.execution.privacy_request_requeue_retry_count
        assert original_value == 3

        # Test that we can change the configuration
        try:
            # Temporarily change the config value
            CONFIG.execution.privacy_request_requeue_retry_count = 5
            assert CONFIG.execution.privacy_request_requeue_retry_count == 5

            # Change it again to verify it's truly configurable
            CONFIG.execution.privacy_request_requeue_retry_count = 1
            assert CONFIG.execution.privacy_request_requeue_retry_count == 1

        finally:
            # Always restore the original value
            CONFIG.execution.privacy_request_requeue_retry_count = original_value

    def test_integration_privacy_request_retry_workflow(self, db, policy):
        """Test the complete workflow of privacy request retry management."""
        from fides.api.util.cache import (
            get_privacy_request_retry_count,
            increment_privacy_request_retry_count,
            reset_privacy_request_retry_count,
        )

        # Create a privacy request
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

        try:
            # Test initial state
            assert get_privacy_request_retry_count(privacy_request.id) == 0

            # Test incrementing
            count = increment_privacy_request_retry_count(privacy_request.id)
            assert count == 1
            assert get_privacy_request_retry_count(privacy_request.id) == 1

            # Test multiple increments up to limit
            for i in range(2, 4):  # Increment to 3 (the limit)
                count = increment_privacy_request_retry_count(privacy_request.id)
                assert count == i

            # Test reset
            reset_privacy_request_retry_count(privacy_request.id)
            assert get_privacy_request_retry_count(privacy_request.id) == 0

        finally:
            # Clean up
            privacy_request.delete(db)
