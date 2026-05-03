"""Test helpers for the event framework.

These helpers are exposed in the public API so subscribers and publishers
across the codebase can write expressive assertions without reaching into
session internals.
"""

from typing import Any, List, Optional

from sqlalchemy.orm import Session

from fides.common.events.publisher import (
    _CALLBACKS_INSTALLED_KEY,
    _PENDING_EVENTS_KEY,
    get_pending_events,
)


def published_events(session: Session) -> List[Any]:
    """Return the event instances currently queued on ``session`` (pre-commit).

    Use this for asserting that a publisher emitted what you expected,
    without needing to commit and observe the dispatched side effect.
    """
    return [event for _, event in get_pending_events(session)]


def assert_event_published(
    session: Session,
    event_type: type,
    *,
    count: Optional[int] = None,
) -> List[Any]:
    """Assert that at least one event of ``event_type`` is queued on ``session``.

    Args:
        session: The session the publisher emitted to.
        event_type: The event class to filter on.
        count: If supplied, asserts exactly this many events of the type.
            If None, asserts at least one.

    Returns:
        The matching event instances, in queue order.

    Raises:
        AssertionError: If the count constraint is not met.
    """
    matches = [e for e in published_events(session) if isinstance(e, event_type)]

    if count is None:
        assert matches, (
            f"Expected at least one {event_type.__qualname__} event on "
            f"the session, but found none."
        )
    else:
        assert len(matches) == count, (
            f"Expected {count} {event_type.__qualname__} event(s) on the "
            f"session, but found {len(matches)}."
        )

    return matches


def clear_pending_events(session: Session) -> None:
    """Drop all pending events on ``session`` without dispatching.

    Cleanup helper for tests that publish events but do not want them to
    fire (e.g. tests that assert on the queued state alone).
    """
    session.info.pop(_PENDING_EVENTS_KEY, None)
    session.info.pop(_CALLBACKS_INSTALLED_KEY, None)
