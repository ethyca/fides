"""
Utilities for storing and accessing request-scoped context that must be
accessible across the entire application stack (endpoints → services →
helpers → decorators) without having to thread additional parameters through
all call-sites.

Currently we only capture the authenticated `user_id` but additional fields
(e.g. correlation_id, locale, feature_flags) can be added in the future by
expanding the `RequestContext` dataclass.

A `contextvars.ContextVar` is used instead of a module-level global to ensure
that values are local to the current execution context (async task, thread or
Celery worker) and therefore safe for concurrent workloads.
"""

from __future__ import annotations

import contextvars
from dataclasses import dataclass
from typing import Optional, Dict, Any

__all__ = [
    "RequestContext",
    "get",
    "set",
    "reset",
]


@dataclass(slots=True)
class RequestContext:  # noqa: D101 – simple container
    user_id: Optional[str] = None
    # place-holder for arbitrary extra data
    extra: Dict[str, Any] | None = None


# A single ContextVar holding the current request context.
_ctx: contextvars.ContextVar[RequestContext] = contextvars.ContextVar(
    "request_context",
    default=RequestContext(),
)


def get() -> RequestContext:  # noqa: D401 – simple helper
    """Return the current :class:`RequestContext` for this request.

    • The context is populated during authentication by
      `extract_token_and_load_client()`, which calls
      `fides.api.request_context.set` with the authenticated
      `user_id`.
    • A `ContextVar` keeps the data isolated per request -
      each coroutine or thread sees its own copy and it is discarded at the
      end of the request.
    • The returned object is the live context; treat it as read-only and use
      `set` to mutate values.
    """
    return _ctx.get()


def set(**kwargs: Any) -> None:  # noqa: D401 – simple helper
    """Mutate the current context in place using `key=value` pairs."""
    ctx = _ctx.get()
    for key, value in kwargs.items():
        if hasattr(ctx, key):
            setattr(ctx, key, value)
        else:
            # Fallback: store unknown keys inside the `extra` mapping
            if ctx.extra is None:
                ctx.extra = {}
            ctx.extra[key] = value


def reset() -> None:
    """Remove all context - mainly for test clean-up."""
    _ctx.set(RequestContext())