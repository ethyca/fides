"""ContextVar for the current event_id during dispatch + handling.

A separate ContextVar keeps the framework's propagation independent of
``fides.api.request_context``. Subscribers can read the current event_id
via ``get_current_event_id()`` for logging or correlation.
"""

import contextvars
from typing import Optional

_event_id_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "fides_event_id",
    default=None,
)


def get_current_event_id() -> Optional[str]:
    """Return the event_id for the event currently being dispatched / handled,
    or None if no event is in scope."""
    return _event_id_ctx.get()


def set_current_event_id(event_id: Optional[str]) -> None:
    """Set the event_id in the current execution context. Pass None to clear."""
    _event_id_ctx.set(event_id)
