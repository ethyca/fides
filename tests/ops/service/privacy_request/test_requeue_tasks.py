"""Tests for requeuing interrupted tasks functionality"""

from fides.api.models.privacy_request import ExecutionLogStatus
from fides.api.service.privacy_request.request_service import requeue_interrupted_tasks
from fides.api.util.cache import cache_task_tracking_key, celery_tasks_in_flight


def test_requeue_interrupted_tasks(
    celery_session_app,
    celery_session_worker,
    db,
    privacy_request,
    request_task,
):
    """Test requeuing interrupted tasks with various scenarios using real Celery workers"""
    # Setup: Create a task that appears to be interrupted
    request_task.status = ExecutionLogStatus.in_processing
    request_task.save(db)
    cache_task_tracking_key(request_task.id, "test_task_id")

    # Verify task appears interrupted (not in flight)
    assert not celery_tasks_in_flight([request_task.get_cached_task_id()])

    # Test requeuing
    results = requeue_interrupted_tasks.delay().get(timeout=10)

    # Verify task was requeued
    assert request_task.id in results["requeued_tasks"]
    assert request_task.id in results["state_cleaned"]

    # Verify task is now running
    db.refresh(request_task)
    assert request_task.get_cached_task_id() is not None
    assert (
        request_task.get_cached_task_id() != "test_task_id"
    )  # Should have new task ID


def test_requeue_interrupted_tasks_with_upstream_dependencies(
    celery_session_app,
    celery_session_worker,
    db,
    privacy_request,
    request_task,
):
    """Test that we don't requeue tasks with incomplete upstream dependencies using real Celery workers"""
    # Setup: Create a task that appears to be interrupted but has incomplete upstream tasks
    request_task.status = ExecutionLogStatus.in_processing
    request_task.save(db)
    cache_task_tracking_key(request_task.id, "test_task_id")

    # Mock upstream tasks incomplete by setting upstream task to pending
    root_task = privacy_request.get_root_task_by_action(request_task.action_type)
    root_task.status = ExecutionLogStatus.pending
    root_task.save(db)

    # Verify task appears interrupted
    assert not celery_tasks_in_flight([request_task.get_cached_task_id()])

    # Test requeuing
    results = requeue_interrupted_tasks.delay().get(timeout=10)

    # Verify task was cleaned but not requeued due to upstream dependencies
    assert request_task.id not in results["requeued_tasks"]
    assert request_task.id in results["state_cleaned"]

    # Verify task was not requeued (should have same task ID)
    db.refresh(request_task)
    assert request_task.get_cached_task_id() is None  # Cache should be cleared


def test_requeue_interrupted_tasks_still_running(
    celery_session_app,
    celery_session_worker,
    db,
    privacy_request,
    request_task,
    monkeypatch,
):
    """Test that we don't requeue tasks that are still running"""
    # Setup: Create a task that is still running
    request_task.status = ExecutionLogStatus.in_processing
    request_task.save(db)
    task_id = "running_task_id"
    cache_task_tracking_key(request_task.id, task_id)

    # Mock celery_tasks_in_flight to indicate task is still running
    def mock_tasks_in_flight(task_ids):
        assert task_id in task_ids  # Verify we're checking the right task
        return True  # Indicate task is running

    monkeypatch.setattr(
        "fides.api.service.privacy_request.request_service.celery_tasks_in_flight",
        mock_tasks_in_flight,
    )

    # Test requeuing
    results = requeue_interrupted_tasks.delay().get(timeout=10)

    # Verify task was not requeued or cleaned since it's still running
    assert request_task.id not in results["requeued_tasks"]
    assert request_task.id not in results["state_cleaned"]

    # Verify task ID remains unchanged
    db.refresh(request_task)
    assert request_task.get_cached_task_id() == task_id
