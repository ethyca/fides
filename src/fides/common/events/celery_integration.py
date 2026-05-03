"""Celery task wrapper factory.

Each registered subscriber gets its own Celery task whose name is derived
deterministically from the event class and the handler function, so the
dispatcher (in the publisher process) and the task itself (in the worker
process) agree on routing without any shared registry on the wire.

event_id is passed as an explicit task argument rather than through Celery
headers. Headers don't propagate through ``apply_async`` in eager mode (used
in tests), so passing via args keeps behavior consistent across modes.
"""

from typing import Any, Callable, Dict

from celery import Task
from loguru import logger

from fides.common.events.base import dict_to_event
from fides.common.events.context import set_current_event_id
from fides.common.events.registry import Subscriber

# A registry of (subscriber_id -> Celery task) for boot-time validation in tests.
_REGISTERED_TASKS: Dict[str, Task] = {}


def task_name_for(event_type: type, func: Callable) -> str:
    """Build the deterministic Celery task name for a (event, subscriber) pair.

    Format: ``events.{event_module}.{EventClass}.{subscriber_module}.{subscriber_qualname}``.
    """
    event_qualname = f"{event_type.__module__}.{event_type.__qualname__}"
    func_qualname = f"{func.__module__}.{func.__qualname__}"
    return f"events.{event_qualname}.{func_qualname}"


def make_subscriber_task(subscriber: Subscriber) -> Task:
    """Create and register the Celery task wrapper for ``subscriber``.

    The wrapper:
    - Sets the event_id ContextVar (so subscribers can read it via
      ``get_current_event_id()`` during handling).
    - Deserializes the dict payload back into an event instance.
    - Calls the underlying handler.
    - Clears the event_id ContextVar on the way out, so a long-lived worker
      process doesn't leak event_id across task invocations.

    The Celery app is imported lazily so this module remains importable
    independently of ``fides.api.tasks``.
    """
    # Lazy import to avoid a circular dependency at framework import time.
    from fides.api.tasks import celery_app

    def _task_body(payload: Dict[str, Any], event_id: str) -> None:
        set_current_event_id(event_id)
        try:
            event = dict_to_event(subscriber.event_type, payload)
            subscriber.func(event)
        except Exception:
            logger.exception(
                "Event subscriber raised: subscriber={} event_type={} event_id={}",
                subscriber.task_name,
                subscriber.event_type.__qualname__,
                event_id,
            )
            raise
        finally:
            set_current_event_id(None)

    task = celery_app.task(name=subscriber.task_name, queue=subscriber.queue)(
        _task_body
    )
    _REGISTERED_TASKS[subscriber.task_name] = task
    return task


def is_subscriber_task_registered(task_name: str) -> bool:
    """Return True if a Celery task is registered for the given subscriber name."""
    return task_name in _REGISTERED_TASKS


def _reset_registered_tasks_for_tests() -> None:
    """Clear the boot-time validation registry. Tests use this between cases."""
    _REGISTERED_TASKS.clear()
