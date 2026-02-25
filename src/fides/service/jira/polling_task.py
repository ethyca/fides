"""Celery task and scheduler wiring for Jira ticket polling.

The ``poll_jira_tickets`` task acquires a Redis lock, then delegates to
a registered polling service callable.  Until Fidesplus Slice 4 registers
an implementation, the task is a no-op.

The ``initiate_jira_ticket_polling`` function adds the task to the
APScheduler on application startup.
"""

from typing import Callable, Optional

from loguru import logger

from fides.api.tasks import DatabaseTask, celery_app
from fides.api.tasks.scheduled.scheduler import scheduler
from fides.api.util.lock import redis_lock
from fides.config import CONFIG

JIRA_TICKET_POLLING_JOB = "jira_ticket_polling"
JIRA_TICKET_POLLING_LOCK = "jira_ticket_polling_lock"
JIRA_TICKET_POLLING_LOCK_TIMEOUT = 600

_poll_service_fn: Optional[Callable] = None


def register_poll_service(fn: Callable) -> None:
    """Register the actual polling implementation (called by Fidesplus Slice 4)."""
    global _poll_service_fn  # noqa: PLW0603
    _poll_service_fn = fn
    logger.info("Jira ticket polling service registered")


@celery_app.task(base=DatabaseTask, bind=True)
def poll_jira_tickets(self: DatabaseTask) -> None:
    """Poll open Jira tickets and update their statuses.

    Acquires a Redis lock to prevent concurrent execution.  Delegates to
    the registered polling service; if none is registered the task is a
    no-op.
    """
    with redis_lock(JIRA_TICKET_POLLING_LOCK, JIRA_TICKET_POLLING_LOCK_TIMEOUT) as lock:
        if not lock:
            return

        if _poll_service_fn is None:
            logger.debug("Jira ticket polling: no service registered, skipping")
            return

        with self.get_new_session() as db:
            _poll_service_fn(db)


def initiate_jira_ticket_polling() -> None:
    """Add the Jira ticket polling job to the APScheduler.

    Called during application startup from ``main.py``.  Skipped in
    test mode.
    """
    if CONFIG.test_mode:
        return

    assert scheduler.running, (
        "Scheduler is not running! Cannot add Jira ticket polling job."
    )

    logger.info("Initiating scheduler for Jira ticket polling")
    scheduler.add_job(
        func=poll_jira_tickets,
        trigger="interval",
        kwargs={},
        id=JIRA_TICKET_POLLING_JOB,
        coalesce=True,
        replace_existing=True,
        minutes=CONFIG.execution.jira_polling_interval_minutes,
    )
