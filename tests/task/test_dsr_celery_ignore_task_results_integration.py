"""Integration tests: DSR ignore_result avoids Celery result-backend Redis keys.

Uses the same Redis connection as ``get_cache()`` (aligned with Celery's configured
``result_backend`` in typical deployments) and the session Celery worker.
"""

from __future__ import annotations

import time
import uuid
from typing import Optional, Union

import pytest

from fides.api.models.privacy_request import RequestTask
from fides.api.task.execute_request_tasks import queue_request_task
from fides.api.util.cache import get_cache, get_dsr_cache_store
from fides.config import CONFIG
from fides.service.privacy_request.privacy_request_service import queue_privacy_request


def _celery_result_meta_key(task_id: str) -> str:
    return f"celery-task-meta-{task_id}"


def _decode_redis_value(value: Optional[Union[str, bytes]]) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return str(value)


def _wait_until(
    predicate,
    *,
    timeout_seconds: float = 45.0,
    poll_seconds: float = 0.25,
) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(poll_seconds)
    return False


def _delete_celery_meta_if_present(cache, task_id: str) -> None:
    key = _celery_result_meta_key(task_id)
    if cache.exists(key):
        cache.delete(key)


@pytest.fixture
def restore_ignore_dsr_celery_task_results():
    original = CONFIG.execution.ignore_dsr_celery_task_results
    yield
    CONFIG.execution.ignore_dsr_celery_task_results = original


def _skip_if_redis_cluster_session_eager() -> None:
    if CONFIG.redis.cluster_enabled:
        pytest.skip(
            "Redis cluster test sessions run Celery eagerly; result-backend key "
            "assertions are not reliable here."
        )


@pytest.mark.integration
@pytest.mark.usefixtures(
    "cache",
    "restore_ignore_dsr_celery_task_results",
    "enable_celery_worker",
)
def test_queue_privacy_request_with_ignore_flag_does_not_write_celery_result_meta_key() -> (
    None
):
    """When enabled, queued run_privacy_request should not create celery-task-meta-* in Redis."""
    _skip_if_redis_cluster_session_eager()

    CONFIG.execution.ignore_dsr_celery_task_results = True
    cache = get_cache()
    privacy_request_id = str(uuid.uuid4())
    celery_task_id = queue_privacy_request(
        privacy_request_id, from_webhook_id=None, from_step=None
    )
    assert celery_task_id

    try:
        # Give the worker time to finish (task may error for a random PR id).
        time.sleep(3.0)
        assert not bool(cache.exists(_celery_result_meta_key(celery_task_id)))
        # And it should stay absent while polling (no late meta write).
        assert not _wait_until(
            lambda: bool(cache.exists(_celery_result_meta_key(celery_task_id))),
            timeout_seconds=20.0,
        )
    finally:
        _delete_celery_meta_if_present(cache, celery_task_id)
        get_dsr_cache_store(privacy_request_id).clear()


@pytest.mark.integration
@pytest.mark.integration_postgres
@pytest.mark.usefixtures(
    "cache",
    "restore_ignore_dsr_celery_task_results",
    "enable_celery_worker",
)
def test_queue_request_task_with_ignore_flag_does_not_write_celery_result_meta_key(
    request_task: RequestTask,
) -> None:
    """When enabled, queued run_*_node should not create celery-task-meta-* in Redis."""
    _skip_if_redis_cluster_session_eager()

    CONFIG.execution.ignore_dsr_celery_task_results = True
    cache = get_cache()

    store = get_dsr_cache_store(request_task.id)
    celery_task_id: Optional[str] = None
    try:
        queue_request_task(request_task, privacy_request_proceed=True)
        celery_task_id = _decode_redis_value(store.get_async_execution())
        assert celery_task_id

        time.sleep(3.0)
        assert not bool(cache.exists(_celery_result_meta_key(celery_task_id)))
        # Late writes should not appear after the worker settles.
        assert not _wait_until(
            lambda: bool(cache.exists(_celery_result_meta_key(celery_task_id))),
            timeout_seconds=20.0,
        )
    finally:
        if celery_task_id:
            _delete_celery_meta_if_present(cache, celery_task_id)
        store.clear()
