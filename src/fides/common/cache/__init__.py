"""
Shared Redis cache utilities and the RedisCacheManager.

RedisCacheManager provides modern Redis patterns such as key indexes.
"""

from fides.common.cache.manager import (
    INDEX_KEY_PREFIX,
    RedisCacheManager,
)

__all__ = [
    "INDEX_KEY_PREFIX",
    "RedisCacheManager",
]
