"""Celery task and scheduler wiring for reply mailbox polling.

The ``poll_reply_mailbox`` task acquires a Redis lock, then delegates to
a registered polling service callable.  Until Fidesplus registers an
implementation, the task is a no-op.

The ``initiate_reply_polling`` function adds the task to the APScheduler
on application startup.
"""

from collections.abc import Callable

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.tasks import DatabaseTask, celery_app
from fides.api.tasks.scheduled.scheduler import scheduler
from fides.api.util.lock import redis_lock
from fides.config import CONFIG

REPLY_POLLING_JOB = "reply_mailbox_polling"
REPLY_POLLING_LOCK = "reply_mailbox_polling_lock"
# Lock auto-expires after this many seconds. If the registered service
# takes longer, another worker may acquire the lock and run concurrently.
# The implementation must complete within this window or be idempotent.
REPLY_POLLING_LOCK_TIMEOUT = 600

# Set once at startup by Fidesplus via register_reply_poll_service();
# only read thereafter by Celery workers.  Safe under CPython's GIL
# for threaded workers.  For forked workers (default), registration
# MUST occur at module import time (before fork) — see
# reply_polling_registration.py in fidesplus.
_service_fn: Callable[[Session], None] | None = None


def register_reply_poll_service(fn: Callable[[Session], None]) -> None:
    """Register the actual polling implementation (called by Fidesplus)."""
    global _service_fn  # noqa: PLW0603
    _service_fn = fn
    logger.info("Reply mailbox polling service registered")


@celery_app.task(base=DatabaseTask, bind=True)
def poll_reply_mailbox(self: DatabaseTask) -> None:
    """Poll an IMAP mailbox for DSR reply messages.

    Acquires a Redis lock to prevent concurrent execution.  Delegates to
    the registered polling service; if none is registered the task is a
    no-op.
    """
    with redis_lock(REPLY_POLLING_LOCK, REPLY_POLLING_LOCK_TIMEOUT) as lock:
        if not lock:
            return

        if _service_fn is None:
            logger.debug("Reply mailbox polling: no service registered, skipping")
            return

        with self.get_new_session() as db:
            _service_fn(db)


def initiate_reply_polling() -> None:
    """Add the reply mailbox polling job to the APScheduler.

    Called during application startup from ``main.py``.  Skipped in
    test mode.
    """
    if CONFIG.test_mode:
        return

    if not scheduler.running:
        raise RuntimeError(
            "Scheduler is not running! Cannot add reply mailbox polling job."
        )

    logger.info("Initiating scheduler for reply mailbox polling")
    scheduler.add_job(
        func=poll_reply_mailbox.delay,
        trigger="interval",
        id=REPLY_POLLING_JOB,
        coalesce=True,
        replace_existing=True,
        minutes=CONFIG.execution.reply_polling_interval_minutes,
    )
