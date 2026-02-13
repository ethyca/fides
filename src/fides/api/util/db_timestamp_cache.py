"""Caching decorator that invalidates based on database table state.

Checks MAX(updated_at) and COUNT(*) from a model's table to determine
if the cached result is still valid. This is efficient for tables with
infrequent writes where you want to avoid reloading data on every call.

When a caller already holds an open DB session it can be forwarded via
the ``db`` keyword argument of the decorated function, avoiding the
overhead of creating (and tearing down) a standalone session for the
staleness check.
"""

from datetime import datetime
from functools import wraps
from threading import Lock
from typing import Any, Callable, Dict, Optional, Tuple, Type, TypeVar

from loguru import logger
from sqlalchemy import func as sa_func
from sqlalchemy import select
from sqlalchemy.orm import Session

from fides.api.api.deps import get_readonly_autoclose_db_session
from fides.api.db.base_class import Base

R = TypeVar("R")

_cache_store: Dict[str, Dict[str, Any]] = {}
_cache_lock = Lock()


def _get_table_state(
    model: Type[Base],
    db: Optional[Session] = None,
) -> Tuple[Optional[datetime], int]:
    """Query the current MAX(updated_at) and COUNT(*) for a model's table.

    If *db* is provided the query runs on that session (no extra overhead).
    Otherwise a readonly auto-closing session is created on the fly.
    """
    stmt = select(
        sa_func.max(model.updated_at),
        sa_func.count(model.id),
    )

    if db is not None:
        result = db.execute(stmt).first()
    else:
        with get_readonly_autoclose_db_session() as fallback_db:
            result = fallback_db.execute(stmt).first()

    if result:
        return result[0], result[1]
    return None, 0


def db_timestamp_cached(
    model: Type[Base],
    cache_key: str,
) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """Caching decorator that invalidates when the underlying DB table changes.

    On each call, runs a lightweight aggregate query to check
    ``MAX(updated_at)`` and ``COUNT(*)`` on the given *model*'s table.
    If either value differs from what was stored at the last cache fill,
    the decorated function is called and its result is cached.  Otherwise
    the cached result is returned immediately.

    **Session reuse**: if the decorated function is called with a ``db``
    keyword argument the staleness check reuses that session instead of
    creating a new one.  This eliminates connection-checkout overhead
    when the caller already has an open session (e.g. inside an API
    request handler).  The ``db`` kwarg is consumed by the decorator and
    **not** forwarded to the wrapped function.

    The decorator attaches a ``cache_clear()`` helper to the wrapper so
    callers can force invalidation after writes (e.g. save / delete).

    Args:
        model: The SQLAlchemy model class whose table state is monitored.
        cache_key: A unique string identifying this cache entry.
    """

    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> R:
            # Extract the optional db session before forwarding kwargs.
            db: Optional[Session] = kwargs.pop("db", None)

            current_max_updated, current_count = _get_table_state(model, db=db)

            with _cache_lock:
                cached = _cache_store.get(cache_key)
                if cached is not None:
                    if (
                        cached["max_updated_at"] == current_max_updated
                        and cached["count"] == current_count
                    ):
                        return cached["value"]

            # Cache miss or stale – call the underlying function
            logger.debug(
                "db_timestamp_cache '{}': cache miss, reloading from database",
                cache_key,
            )
            value = func(*args, **kwargs)

            with _cache_lock:
                _cache_store[cache_key] = {
                    "max_updated_at": current_max_updated,
                    "count": current_count,
                    "value": value,
                }

            return value

        def cache_clear() -> None:
            """Manually clear this cache entry."""
            with _cache_lock:
                _cache_store.pop(cache_key, None)

        wrapper.cache_clear = cache_clear  # type: ignore[attr-defined]
        return wrapper

    return decorator
