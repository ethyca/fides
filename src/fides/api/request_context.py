"""
Utilities for storing and accessing request-scoped context that must be
accessible across the entire application stack (endpoints -> services ->
helpers -> decorators) without having to thread additional parameters through
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
from typing import Any, Optional

__all__ = [
    "get_user_id",
    "set_user_id",
    "reset_request_context",
]


@dataclass
class RequestContext:
    user_id: Optional[str] = None


# A single ContextVar holding the current request context.
_ctx: contextvars.ContextVar[RequestContext] = contextvars.ContextVar(
    "request_context",
    default=RequestContext(),
)


def get_request_context() -> RequestContext:
    """Return the current `RequestContext` for this request.

    - The context is populated during authentication by `extract_token_and_load_client()`,
      which calls `fides.api.request_context.set_request_context` with
      the authenticated `user_id`.
    - A `ContextVar` keeps the data isolated per request. Each coroutine
      or thread sees its own copy and it is discarded at the end of the request.
    - The returned object is the live context; treat it as read-only and use
      `set_request_context` to mutate values.
    """
    return _ctx.get()


def set_request_context(**kwargs: Any) -> None:
    """Mutate the current context in place using `key=value` pairs."""
    ctx = _ctx.get()
    for key, value in kwargs.items():
        if hasattr(ctx, key):
            setattr(ctx, key, value)


def reset_request_context() -> None:
    """Remove all context, mainly for test clean-up."""
    _ctx.set(RequestContext())


def get_user_id() -> Optional[str]:
    """Return the user_id from the current request context."""
    ctx = get_request_context()
    return ctx.user_id


def set_user_id(user_id: str) -> None:
    """Set the user_id in the current request context."""
    set_request_context(user_id=user_id)
