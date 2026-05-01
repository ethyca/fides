"""
Utilities for storing and accessing request-scoped context that must be
accessible across the entire application stack (endpoints -> services ->
helpers -> decorators) without having to thread additional parameters through
all call-sites.

Currently we capture the authenticated `user_id` and an optional `request_id`
for log correlation. Additional fields (e.g. locale, feature_flags) can be
added in the future by expanding the `RequestContext` dataclass.

A `contextvars.ContextVar` is used instead of a module-level global to ensure
that values are local to the current execution context (async task, thread or
Celery worker) and therefore safe for concurrent workloads.
"""

from __future__ import annotations

import contextvars
from dataclasses import asdict, dataclass
from typing import Any, Optional

__all__ = [
    "get_client_id",
    "get_request_id",
    "get_user_id",
    "reset_request_context",
    "set_client_id",
    "set_request_id",
    "set_user_id",
]


@dataclass
class RequestContext:
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    client_id: Optional[str] = None


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
    """Set fields on the request context for the current execution context.

    Creates a new ``RequestContext`` (copying existing values) and stores it
    via ``_ctx.set()`` so the update is scoped to this coroutine/thread
    rather than mutating a shared default object.
    """
    ctx = _ctx.get()
    current = asdict(ctx)
    for key, value in kwargs.items():
        if key in current:
            current[key] = value
    _ctx.set(RequestContext(**current))


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


def get_request_id() -> Optional[str]:
    """Return the request_id from the current request context."""
    ctx = get_request_context()
    return ctx.request_id


def set_request_id(request_id: Optional[str] = None) -> None:
    """Set or clear the request_id in the current request context."""
    set_request_context(request_id=request_id)


def get_client_id() -> Optional[str]:
    """Return the client_id from the current request context.

    Set when the authenticated actor is a non-user-linked API client.
    Mutually exclusive with user_id — only one will be non-None per request.
    """
    ctx = get_request_context()
    return ctx.client_id


def set_client_id(client_id: str) -> None:
    """Set the client_id in the current request context."""
    set_request_context(client_id=client_id)
