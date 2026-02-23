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

__all__ = ["INDEX_KEY_PREFIX", "RedisCacheManager", "DSR_KEY_PREFIX", "DSRCacheStore"]
