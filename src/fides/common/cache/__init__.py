"""
Shared Redis cache utilities and the RedisCacheManager.

RedisCacheManager provides modern Redis patterns such as key indexes.

DSRCacheStore wraps that with DSR-specific key naming (dsr:{id}:{part})
and index-backed list/clear with lazy migration for legacy keys.

"""

from fides.common.cache.dsr_store import (
    DSR_KEY_PREFIX,
    DSRCacheStore,
)
from fides.common.cache.manager import (
    INDEX_KEY_PREFIX,
    RedisCacheManager,
)

__all__ = ["INDEX_KEY_PREFIX", "RedisCacheManager", "DSR_KEY_PREFIX", "DSRCacheStore"]
