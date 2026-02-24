"""
RedisCacheManager: Redis client wrapper with key-index support.

Key indexes allow listing and deleting keys by a logical prefix without
using Redis KEYS or SCAN. Each index is stored as a Redis SET at
__idx:{index_prefix}; members are the actual cache key names.
"""

from typing import List, Optional, Union

from redis import Redis

# Redis key prefix for index sets. Index key = INDEX_KEY_PREFIX + index_prefix.
INDEX_KEY_PREFIX = "__idx:"

# Default additional TTL for index sets when set_with_index is used with index_ttl_enabled=True
INDEX_TTL_EXTRA_SECONDS = 60 * 60 * 24  # 24 hours

# Value types supported by Redis SET and basic ops
RedisValue = Union[bytes, float, int, str]


class RedisCacheManager:
    """
    Wraps a Redis client and adds key-index operations.

    Use key indexes when you need to list or delete keys by a logical
    prefix (e.g. all keys for a privacy request) without scanning the
    key space. Call add_key_to_index when you set a key, and
    remove_key_from_index when you delete it (or use the combined
    set/delete helpers).
    """

    def __init__(self, redis_client: Redis) -> None:
        """
        Args:
            redis_client: Any Redis client (e.g. FidesopsRedis from get_cache()).
        """
        self._redis = redis_client

    def _index_key(self, index_prefix: str) -> str:
        """Return the Redis key used to store the set of keys for this index."""
        return f"{INDEX_KEY_PREFIX}{index_prefix}"

    def add_key_to_index(self, index_prefix: str, key: str) -> None:
        """Register a key under an index prefix so it can be listed by prefix."""
        self._redis.sadd(self._index_key(index_prefix), key)

    def remove_key_from_index(self, index_prefix: str, key: str) -> None:
        """Unregister a key from an index prefix."""
        self._redis.srem(self._index_key(index_prefix), key)

    def get_keys_by_index(self, index_prefix: str) -> List[str]:
        """
        Return all keys registered under this index prefix.
        O(set size), no key-space scan.
        """
        members = self._redis.smembers(self._index_key(index_prefix))
        # Convert bytes to strings for consistent return type
        return [m.decode('utf-8') if isinstance(m, bytes) else m for m in members] if members else []

    def delete_index(self, index_prefix: str) -> None:
        """Remove the index set. Does not delete the data keys themselves."""
        self._redis.delete(self._index_key(index_prefix))

    def delete_keys_by_index(
        self,
        index_prefix: str,
    ) -> None:
        """
        Delete every key in the index and then remove the index set.
        Use this instead of KEYS/SCAN when you have been maintaining an index.
        """
        keys = self.get_keys_by_index(index_prefix)
        idx_key = self._index_key(index_prefix)
        if keys:
            pipe = self._redis.pipeline()
            for k in keys:
                pipe.delete(k)
            pipe.delete(idx_key)
            pipe.execute()
        else:
            self._redis.delete(idx_key)

    def set_with_index(
        self,
        key: str,
        value: RedisValue,
        index_prefix: str,
        expire_seconds: Optional[int] = None,
        *,
        index_ttl_enabled: bool = False,
    ) -> Optional[bool]:
        """
        Set a key and add it to an index in one step.
        If expire_seconds is set, the key will expire after that many seconds.
        Returns the result of SET (e.g. True).

        Index TTL (opt-in safety): When index_ttl_enabled=True and expire_seconds is set,
        the index set will be given a TTL. If the key's TTL is farther out than the
        index's current TTL, the index TTL is extended. Disabled by default.
        """
        pipe = self._redis.pipeline()
        if expire_seconds is not None:
            pipe.set(key, value, ex=expire_seconds)
        else:
            pipe.set(key, value)
        pipe.sadd(self._index_key(index_prefix), key)
        results = pipe.execute()
        if index_ttl_enabled and expire_seconds is not None:
            idx_key = self._index_key(index_prefix)
            current_ttl = self._redis.ttl(idx_key)
            proposed_index_ttl = expire_seconds + INDEX_TTL_EXTRA_SECONDS
            if current_ttl < 0 or proposed_index_ttl > current_ttl:
                self._redis.expire(idx_key, proposed_index_ttl)
        return results[0]

    def delete_key_and_remove_from_index(
        self,
        key: str,
        index_prefix: str,
    ) -> None:
        """Delete a key and remove it from its index."""
        pipe = self._redis.pipeline()
        pipe.delete(key)
        pipe.srem(self._index_key(index_prefix), key)
        pipe.execute()

    @property
    def redis(self) -> Redis:
        """Access the underlying Redis client for operations not on the manager."""
        return self._redis
