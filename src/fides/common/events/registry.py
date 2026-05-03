"""In-process registry of event subscribers and @publishes markers.

The registry is module-level singleton state, populated at import time as
@subscribes_to and @publishes decorators run. Both webserver and worker
processes import subscriber modules so both populate the same registry shape;
see design doc §6.3 (Subscriber module hygiene).
"""

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class Subscriber:
    """Registry entry describing a single subscriber binding."""

    func: Callable[[Any], None]
    event_type: type
    task_name: str
    queue: str


# event type -> list of subscribers
_SUBSCRIBERS: dict[type, list[Subscriber]] = {}

# repository/service method -> list of event types it claims to publish
_PUBLISHES_MARKERS: dict[Callable, list[type]] = {}


def register_subscriber(subscriber: Subscriber) -> None:
    """Add a subscriber to the registry. Multiple subscribers per event are allowed."""
    _SUBSCRIBERS.setdefault(subscriber.event_type, []).append(subscriber)


def get_subscribers(event_type: type) -> list[Subscriber]:
    """Return the registered subscribers for ``event_type`` (empty if none)."""
    return list(_SUBSCRIBERS.get(event_type, []))


def all_event_types() -> set[type]:
    """Return every event type with at least one subscriber."""
    return set(_SUBSCRIBERS.keys())


def all_subscribers() -> list[Subscriber]:
    """Return every registered subscriber, flattened."""
    return [s for subs in _SUBSCRIBERS.values() for s in subs]


def register_publishes_marker(func: Callable, event_types: list[type]) -> None:
    """Record a @publishes marker for test-time introspection."""
    existing = _PUBLISHES_MARKERS.setdefault(func, [])
    for et in event_types:
        if et not in existing:
            existing.append(et)


def get_publishes_markers() -> dict[Callable, list[type]]:
    """Return a copy of the @publishes marker registry."""
    return {k: list(v) for k, v in _PUBLISHES_MARKERS.items()}


def _reset_for_tests() -> None:
    """Clear all registry state. Tests use this between cases."""
    _SUBSCRIBERS.clear()
    _PUBLISHES_MARKERS.clear()
