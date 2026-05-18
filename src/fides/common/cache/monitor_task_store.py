"""
Cache store for monitor task stop flags.

Each stopped task gets a single Redis key that worker threads check
(sub-millisecond) before making LLM calls during classification.
"""

from typing import Any

from loguru import logger

TASK_STOPPED_KEY_PREFIX = "monitor_task_stopped:"
DEFAULT_TTL_SECONDS = 60 * 60  # 1 hour


class MonitorTaskCacheStore:
    """Redis-backed stop flag for monitor tasks."""

    def __init__(self, redis_client: Any, ttl_seconds: int = DEFAULT_TTL_SECONDS):
        self._redis = redis_client
        self._ttl = ttl_seconds

    def set_stopped(self, celery_id: str) -> None:
        """Set a stop flag for a task.

        One key per task. Raises if Redis is unavailable — the caller
        should fail the stop request since without the flag the worker
        won't know to stop.
        """
        self._redis.set(f"{TASK_STOPPED_KEY_PREFIX}{celery_id}", "1", ex=self._ttl)

    def is_stopped(self, celery_id: str) -> bool:
        """Check if a task has been stopped.

        Returns False if Redis is unavailable — the task continues as-is.
        """
        try:
            return self._redis.get(f"{TASK_STOPPED_KEY_PREFIX}{celery_id}") is not None
        except Exception:
            logger.warning(
                "Failed to check task stop flag in Redis, assuming not stopped",
                exc_info=True,
            )
            return False
