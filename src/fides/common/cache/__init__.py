"""
Shared Redis cache utilities and the RedisCacheManager.

RedisCacheManager provides modern Redis patterns such as key indexes.
DSRCacheStore wraps that with DSR-specific key naming (dsr:{id}:{part})
and index-backed list/clear with lazy migration for legacy keys.

Usage:
    with get_dsr_cache_store() as store:
        store.write_identity(privacy_request_id, "email", "user@example.com")
        store.clear(privacy_request_id)
"""

from contextlib import contextmanager
from typing import Iterator

from fides.common.cache.dsr_store import (
    DSR_KEY_PREFIX,
    DSRCacheStore,
)
from fides.common.cache.manager import (
    INDEX_KEY_PREFIX,
    RedisCacheManager,
)


from fides.api.util.cache import get_cache

@contextmanager
def get_dsr_cache_store(
    *,
    backfill_index_on_legacy_read: bool = True,
    migrate_legacy_on_read: bool = True,
) -> Iterator[DSRCacheStore]:
    """
    Context manager that yields a DSRCacheStore backed by the application Redis connection.

    The store handles both new-format keys (dsr:{id}:{part}) and legacy keys
    (id-{id}-{field}-{attr}) with automatic migration on read when migrate_legacy_on_read=True.

    Args:
        backfill_index_on_legacy_read: When listing keys and falling back to SCAN for
            legacy keys, add those keys to the index. Default True.
        migrate_legacy_on_read: When a get finds value in legacy key only, write to
            new key, delete legacy key, add new key to index. Default True.

    Yields:
        DSRCacheStore instance ready for use

    Usage:
        with get_dsr_cache_store() as store:
            store.clear(privacy_request_id)

        with get_dsr_cache_store() as store:
            store.write_identity(pr_id, "email", "user@example.com")
            value = store.get_identity(pr_id, "email")
    """
    redis_client = get_cache()
    manager = RedisCacheManager(redis_client)
    store = DSRCacheStore(
        manager,
        backfill_index_on_legacy_read=backfill_index_on_legacy_read,
        migrate_legacy_on_read=migrate_legacy_on_read,
    )
    yield store
    # No cleanup needed; store doesn't own the Redis connection


__all__ = [
    "DSR_KEY_PREFIX",
    "DSRCacheStore",
    "INDEX_KEY_PREFIX",
    "RedisCacheManager",
    "get_dsr_cache_store",
]
