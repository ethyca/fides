"""Dispatch logic: walks the registry and enqueues a Celery task per subscriber.

This module is import-light intentionally — the dispatch path runs on every
session.commit() that has pending events, so it should not pull in heavy
modules at import time.
"""

from typing import Any

from loguru import logger

from fides.common.events.base import event_to_dict
from fides.common.events.registry import get_subscribers


def dispatch(event_id: str, event: Any) -> None:
    """Dispatch one event to every registered subscriber for its type.

    Each subscriber gets an independent Celery task. Failures during dispatch
    are logged but do not propagate — one broker hiccup shouldn't take out
    the rest of the events queued in the same transaction.

    The ``CONFIG.events.enabled`` kill switch is checked here. When False,
    the function logs and returns without dispatching. Pending events on the
    session are still drained by the publisher; the dispatcher just no-ops.
    """
    # Imported lazily so this module is safe to import before the config
    # has been initialized (e.g. during framework bootstrap).
    from fides.config import CONFIG

    if not CONFIG.events.enabled:
        logger.debug(
            "Event dispatch skipped (CONFIG.events.enabled=False): "
            "event_id={} event_type={}",
            event_id,
            type(event).__qualname__,
        )
        return

    # Lazy import for the same reason as above + to break a potential cycle
    # with the celery_app at module load time.
    from fides.api.tasks import celery_app

    subscribers = get_subscribers(type(event))

    if not subscribers:
        logger.warning(
            "Event published with no subscribers: event_id={} event_type={}",
            event_id,
            type(event).__qualname__,
        )
        return

    payload = event_to_dict(event)

    for subscriber in subscribers:
        logger.debug(
            "Dispatching event: event_id={} event_type={} subscriber={} queue={}",
            event_id,
            type(event).__qualname__,
            subscriber.task_name,
            subscriber.queue,
        )
        try:
            # Prefer apply_async on the registered task object: it runs
            # synchronously under task_always_eager (essential for testing)
            # and goes through the broker in production. send_task would
            # always go to the broker, bypassing eager mode.
            task = celery_app.tasks.get(subscriber.task_name)
            if task is not None:
                task.apply_async(
                    args=[payload, event_id],
                    queue=subscriber.queue,
                )
            else:
                # Fall back to send_task by name. Should not normally happen
                # — make_subscriber_task registers the task at import time.
                celery_app.send_task(
                    subscriber.task_name,
                    args=[payload, event_id],
                    queue=subscriber.queue,
                )
        except Exception:
            logger.exception(
                "Failed to dispatch event to subscriber: "
                "event_id={} event_type={} subscriber={}",
                event_id,
                type(event).__qualname__,
                subscriber.task_name,
            )
            # Continue — don't let one failure stop other events / subscribers.
