"""publish_after_commit: queue an event for dispatch on session.commit().

The publisher API is the only way correctness-sensitive code emits events.
It is deliberately session-scoped so transactional safety holds: events
queued on a session that rolls back are discarded; events on a session
that commits are dispatched once the commit completes.
"""

from typing import Any, List, Tuple
from uuid import uuid4

from loguru import logger
from sqlalchemy import event as sa_event
from sqlalchemy.orm import Session

from fides.common.events.dispatcher import dispatch

# Key used in `session.info` to hold pending events for that session.
_PENDING_EVENTS_KEY = "_fides_pending_events"

# Key used in `session.info` to mark that callbacks have been wired on this
# session. Prevents duplicate registration for the same session.
_CALLBACKS_INSTALLED_KEY = "_fides_event_callbacks_installed"


def publish_after_commit(session: Session, event: Any) -> str:
    """Queue ``event`` for dispatch when ``session`` next commits.

    Args:
        session: The active SQLAlchemy session that owns the transaction
            this event is tied to. Detached / sessionless publishing is not
            supported — the framework relies on after_commit semantics.
        event: An instance of a frozen dataclass that has been validated
            via @subscribes_to or @publishes (or, generally, a class that
            satisfies validate_event_class).

    Returns:
        The generated ``event_id`` (UUID hex string), shared by all
        subscribers when this event is later dispatched.

    Behavior:
    - Generates a new event_id (UUID4 hex).
    - Appends ``(event_id, event)`` to ``session.info["_fides_pending_events"]``.
    - On first call per session, registers ``after_commit`` and
      ``after_rollback`` callbacks. Subsequent calls reuse those callbacks.
    - The callbacks are session-instance-bound: an event published on
      session A does not fire when session B commits.
    """
    event_id = uuid4().hex

    pending: List[Tuple[str, Any]] = session.info.setdefault(_PENDING_EVENTS_KEY, [])
    pending.append((event_id, event))

    if not session.info.get(_CALLBACKS_INSTALLED_KEY):
        sa_event.listen(session, "after_commit", _on_after_commit)
        sa_event.listen(session, "after_rollback", _on_after_rollback)
        session.info[_CALLBACKS_INSTALLED_KEY] = True

    logger.debug(
        "Event queued for dispatch on commit: event_id={} event_type={}",
        event_id,
        type(event).__qualname__,
    )

    return event_id


def get_pending_events(session: Session) -> List[Tuple[str, Any]]:
    """Return a copy of the events currently queued on ``session``."""
    return list(session.info.get(_PENDING_EVENTS_KEY, []))


def _on_after_commit(session: Session) -> None:
    """Drain the session's pending events and dispatch each one.

    Failures from individual dispatch calls are logged inside ``dispatch``;
    they don't propagate here, so one bad event doesn't poison the rest.
    """
    pending = session.info.pop(_PENDING_EVENTS_KEY, None)
    session.info.pop(_CALLBACKS_INSTALLED_KEY, None)
    if not pending:
        return

    for event_id, event in pending:
        dispatch(event_id, event)


def _on_after_rollback(session: Session) -> None:
    """Discard the session's pending events without dispatching."""
    pending = session.info.pop(_PENDING_EVENTS_KEY, None)
    session.info.pop(_CALLBACKS_INSTALLED_KEY, None)
    if pending:
        logger.debug("Discarded {} pending event(s) due to rollback", len(pending))
