"""Celery task and scheduler wiring for DSR lifecycle notifications.

The ``send_notifications`` task acquires a Redis lock, then delegates to
a registered notification service callable.  Until Fidesplus registers an
implementation, the task is a no-op.

The ``initiate_notification_task`` function adds the task to the
APScheduler on application startup.
"""

from collections.abc import Callable

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.tasks import DatabaseTask, celery_app
from fides.api.tasks.scheduled.scheduler import scheduler
from fides.api.util.lock import redis_lock
from fides.config import CONFIG

NOTIFICATION_JOB = "dsr_notifications"
NOTIFICATION_LOCK = "dsr_notifications_lock"
NOTIFICATION_LOCK_TIMEOUT = 600

_service_fn: Callable[[Session], None] | None = None


def register_notification_service(fn: Callable[[Session], None]) -> None:
    """Register the actual notification implementation (called by Fidesplus)."""
    global _service_fn  # noqa: PLW0603
    _service_fn = fn
    logger.info("DSR notification service registered")


@celery_app.task(base=DatabaseTask, bind=True)
def send_notifications(self: DatabaseTask) -> None:
    """Process and send pending DSR lifecycle notifications.

    Acquires a Redis lock to prevent concurrent execution.  Delegates to
    the registered notification service; if none is registered the task is a
    no-op.
    """
    with redis_lock(NOTIFICATION_LOCK, NOTIFICATION_LOCK_TIMEOUT) as lock:
        if not lock:
            return

        if _service_fn is None:
            logger.debug("DSR notifications: no service registered, skipping")
            return

        with self.get_new_session() as db:
            _service_fn(db)


def initiate_notification_task() -> None:
    """Add the DSR notification job to the APScheduler.

    Called during application startup from ``main.py``.  Skipped in
    test mode.
    """
    if CONFIG.test_mode:
        return

    if not scheduler.running:
        raise RuntimeError("Scheduler is not running! Cannot add DSR notification job.")

    logger.info("Initiating scheduler for DSR notifications")
    scheduler.add_job(
        func=send_notifications.delay,
        trigger="interval",
        id=NOTIFICATION_JOB,
        coalesce=True,
        replace_existing=True,
        minutes=CONFIG.execution.notification_interval_minutes,
    )
