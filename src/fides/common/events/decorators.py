"""Public decorator API: @subscribes_to and @publishes."""

from typing import Any, Callable, Optional

from fides.common.events.base import validate_event_class
from fides.common.events.celery_integration import (
    make_subscriber_task,
    task_name_for,
)
from fides.common.events.registry import (
    Subscriber,
    register_publishes_marker,
    register_subscriber,
)

DEFAULT_QUEUE = "fides"


def subscribes_to(
    event_type: type,
    *,
    queue: str = DEFAULT_QUEUE,
) -> Callable[[Callable[[Any], None]], Callable[[Any], None]]:
    """Register ``func`` as a subscriber for ``event_type``.

    Side effects (at import time):
    1. Validates ``event_type`` is a frozen dataclass with JSON-primitive fields.
    2. Adds a ``Subscriber`` entry to the in-process registry.
    3. Creates a Celery task wrapper around ``func`` so the dispatcher can
       enqueue it via ``celery.send_task``.

    The decorator returns the original function unchanged, so callers can
    still invoke it directly (in tests, for example).

    Args:
        event_type: The event dataclass this subscriber handles.
        queue: Celery queue the subscriber's task runs on. Defaults to
            ``"fides"``, which the existing "Other" worker picks up. Override
            only if the subscriber's load profile justifies a dedicated worker.
    """
    validate_event_class(event_type)

    def decorator(func: Callable[[Any], None]) -> Callable[[Any], None]:
        subscriber = Subscriber(
            func=func,
            event_type=event_type,
            task_name=task_name_for(event_type, func),
            queue=queue,
        )
        register_subscriber(subscriber)
        make_subscriber_task(subscriber)
        return func

    return decorator


def publishes(*event_types: type) -> Callable[[Callable], Callable]:
    """Optional marker recording that the decorated method publishes the given
    event types. See design doc §6.5.

    Has no runtime effect — it only populates a registry used by test-time
    coverage checks (the marker-coverage and registry-coverage tests).
    """
    for event_type in event_types:
        validate_event_class(event_type)

    def decorator(func: Callable) -> Callable:
        register_publishes_marker(func, list(event_types))
        return func

    return decorator
