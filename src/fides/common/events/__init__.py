"""In-application event framework for asynchronous reactive work.

See ``docs/fides/docs/event-framework/01-design.md`` for the design.

Public API:
- ``publish_after_commit(session, event)`` — queue an event for dispatch.
- ``@subscribes_to(EventType, queue=...)`` — register an event handler.
- ``@publishes(EventType, ...)`` — optional marker on publisher methods.
- Test helpers: ``assert_event_published``, ``published_events``,
  ``clear_pending_events``.

Subscriber module hygiene: subscriber modules are imported on both
webserver and worker processes. Keep module-level imports minimal and
side-effect-free; defer expensive setup to inside the handler. Same rule
that already applies to Celery task modules.
"""

from fides.common.events.context import (
    get_current_event_id,
    set_current_event_id,
)
from fides.common.events.decorators import publishes, subscribes_to
from fides.common.events.publisher import publish_after_commit
from fides.common.events.testing import (
    assert_event_published,
    clear_pending_events,
    published_events,
)

__all__ = [
    "publish_after_commit",
    "subscribes_to",
    "publishes",
    "assert_event_published",
    "published_events",
    "clear_pending_events",
    "get_current_event_id",
    "set_current_event_id",
]
