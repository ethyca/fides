"""Celery tasks for DSR lifecycle notifications.

Two delivery paths (Option C — hybrid):

1. **Event-driven (primary):** The ``notify`` task is called directly by
   DSR lifecycle code when a state change occurs (e.g., request completed).
   It delivers the notification immediately via the registered handler.

2. **Sweep (secondary):** The ``sweep_notifications`` task runs on a
   scheduled interval via APScheduler.  It catches any notifications that
   were missed or failed on the primary path.

Both paths are no-ops until Fidesplus registers implementations.

The ``initiate_notification_task`` function adds the sweep job to the
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
# Lock auto-expires after this many seconds. If the registered sweep
# takes longer, another worker may acquire the lock and run concurrently.
# The implementation must complete within this window or be idempotent.
NOTIFICATION_LOCK_TIMEOUT = 600

# Set once at startup by Fidesplus via the register_* functions;
# only read thereafter by Celery workers.  Safe under CPython's GIL
# for threaded workers.  For forked workers (default), registration
# MUST occur at module import time (before fork) — see registration.py
# in fidesplus.
_sweep_fn: Callable[[Session], None] | None = None
_notify_fn: Callable[[Session, str, str], None] | None = None


def register_notification_sweep(fn: Callable[[Session], None]) -> None:
    """Register the sweep implementation (called by Fidesplus).

    The sweep function receives a DB session and should query for any
    pending unsent notifications and process them.
    """
    global _sweep_fn  # noqa: PLW0603
    _sweep_fn = fn
    logger.info("DSR notification sweep service registered")


def register_notification_handler(fn: Callable[[Session, str, str], None]) -> None:
    """Register the event-driven notification handler (called by Fidesplus).

    The handler receives a DB session, a privacy_request_id, and an
    event_type string (e.g. "request_completed", "request_approved").
    """
    global _notify_fn  # noqa: PLW0603
    _notify_fn = fn
    logger.info("DSR notification handler registered")


# No lock: concurrent execution is expected — each invocation targets a
# distinct privacy_request_id and these can legitimately run in parallel.
@celery_app.task(base=DatabaseTask, bind=True)
def send_dsr_notification(
    self: DatabaseTask, privacy_request_id: str, event_type: str
) -> None:
    """Send a notification for a specific DSR lifecycle event.

    Called directly by DSR lifecycle code (e.g. after a request is
    completed).  Delegates to the registered handler; if none is
    registered the task is a no-op.

    No Redis lock — concurrent execution is expected since each call
    targets a distinct privacy request.  The registered handler must be
    idempotent for a given (privacy_request_id, event_type) pair, as
    Celery's at-least-once delivery may dispatch the same call twice.
    """
    if _notify_fn is None:
        logger.debug(
            "DSR notification handler not registered, skipping notify "
            "for request={} event={}",
            privacy_request_id,
            event_type,
        )
        return

    with self.get_new_session() as db:
        _notify_fn(db, privacy_request_id, event_type)


@celery_app.task(base=DatabaseTask, bind=True)
def sweep_notifications(self: DatabaseTask) -> None:
    """Sweep for pending unsent notifications and process them.

    Runs on a scheduled interval as a catch-all for notifications that
    failed or were missed on the event-driven path.  Acquires a Redis
    lock to prevent concurrent execution.  Delegates to the registered
    sweep function; if none is registered the task is a no-op.
    """
    with redis_lock(NOTIFICATION_LOCK, NOTIFICATION_LOCK_TIMEOUT) as lock:
        if not lock:
            return

        if _sweep_fn is None:
            logger.debug("DSR notification sweep: no service registered, skipping")
            return

        with self.get_new_session() as db:
            _sweep_fn(db)


def initiate_notification_task() -> None:
    """Add the DSR notification sweep job to the APScheduler.

    Called during application startup from ``main.py``.  Skipped in
    test mode.
    """
    if CONFIG.test_mode:
        return

    if not scheduler.running:
        raise RuntimeError(
            "Scheduler is not running! Cannot add DSR notification sweep job."
        )

    logger.info("Initiating scheduler for DSR notification sweep")
    scheduler.add_job(
        func=sweep_notifications.delay,
        trigger="interval",
        id=NOTIFICATION_JOB,
        coalesce=True,
        replace_existing=True,
        minutes=CONFIG.execution.notification_interval_minutes,
    )
