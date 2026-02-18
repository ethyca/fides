"""Caching decorator that uses a Redis version counter for cross-server invalidation.

Instead of querying the database on every call, this decorator checks a
lightweight integer counter in Redis.  When a write
operation occurs the caller invokes ``bump_version()`` which increments the
counter and clears the local in-memory cache.  Other servers detect the
version change on their next read and reload from the database.

This is ideal for data that is loaded eagerly at startup and changes
infrequently (e.g. connector templates), where the per-request staleness
check must be as cheap as possible.
"""

from functools import wraps
from threading import Lock
from typing import Any, Callable, Dict, Optional, TypeVar

from loguru import logger

from fides.api.util.cache import get_cache

R = TypeVar("R")

_cache_store: Dict[str, Dict[str, Any]] = {}
_cache_lock = Lock()
_UNVERIFIED = object()


def _get_redis_version(redis_key: str) -> Optional[str]:
    """Read the current version counter from Redis.

    Returns the string value of the key, or ``None`` if the key does not
    exist.  Raises on connection failure so the caller can decide how to
    handle it.
    """
    cache = get_cache()
    return cache.get(redis_key)


def _bump_redis_version(redis_key: str) -> None:
    """Increment the version counter in Redis.

    If the key does not exist yet, ``INCR`` creates it with value ``1``.
    """
    cache = get_cache()
    cache.incr(redis_key)


def redis_version_cached(
    redis_key: str,
    cache_key: str,
) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """Caching decorator that invalidates via a Redis version counter.

    On each call, reads a single Redis key (``GET <redis_key>``) and
    compares its value to the version stored alongside the last cached
    result.  If they match the cached result is returned immediately;
    otherwise the decorated function is called and its result is cached
    with the new version.

    The decorator attaches two helpers to the wrapper:

    * ``cache_clear()`` - clears only the **local** in-memory cache entry
      (useful in tests and for manual invalidation on the current server).
    * ``bump_version()`` - increments the Redis version counter **and**
      clears the local cache.  Call this after a write operation so that
      all servers detect the change.

    If Redis is unreachable and a stale cached value exists, the stale
    value is returned.  If no cached value exists (e.g. cold start with
    Redis down), the underlying function is called directly.

    Args:
        redis_key: The Redis key that holds the version counter.
        cache_key: A unique string identifying this local cache entry.
    """

    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> R:
            # Read the current version from Redis
            try:
                current_version = _get_redis_version(redis_key)
            except Exception:
                # Redis is down – prefer stale data over a DB round-trip
                with _cache_lock:
                    cached = _cache_store.get(cache_key)
                    if cached is not None:
                        cached["version"] = _UNVERIFIED
                        logger.debug(
                            "redis_version_cache '{}': Redis unavailable, returning stale cached value",
                            cache_key,
                        )
                        return cached["value"]
                logger.debug(
                    "redis_version_cache '{}': Redis unavailable and no cached value, calling function directly",
                    cache_key,
                )
                value = func(*args, **kwargs)

                with _cache_lock:
                    _cache_store[cache_key] = {
                        "version": _UNVERIFIED,
                        "value": value,
                    }

                return value

            with _cache_lock:
                cached = _cache_store.get(cache_key)
                if cached is not None and cached["version"] == current_version:
                    return cached["value"]

            # Cache miss or stale – call the underlying function
            logger.debug(
                "redis_version_cache '{}': cache miss, reloading",
                cache_key,
            )
            value = func(*args, **kwargs)

            with _cache_lock:
                _cache_store[cache_key] = {
                    "version": current_version,
                    "value": value,
                }

            return value

        def cache_clear() -> None:
            """Manually clear this local cache entry."""
            with _cache_lock:
                _cache_store.pop(cache_key, None)

        def bump_version() -> None:
            """Increment the Redis version counter and clear the local cache.

            Call this after writes (save / delete) so every server
            detects the change on its next read.
            """
            try:
                _bump_redis_version(redis_key)
            except Exception:
                logger.warning(
                    "redis_version_cache '{}': unable to bump Redis version for key '{}'",
                    cache_key,
                    redis_key,
                )
            cache_clear()

        wrapper.cache_clear = cache_clear  # type: ignore[attr-defined]
        wrapper.bump_version = bump_version  # type: ignore[attr-defined]
        return wrapper

    return decorator
