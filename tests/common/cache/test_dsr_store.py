"""
Tests for DSRCacheStore using an in-memory RedisCacheManager (dict + set).
No real Redis required.
"""

import fnmatch
from typing import Any, Dict, List, Optional, Set, Union

import pytest

from fides.common.cache.dsr_store import DSRCacheStore

RedisValue = Union[bytes, float, int, str]


class InMemoryRedis:
    """Minimal Redis-like interface: get, set, delete, keys (glob pattern)."""

    def __init__(self) -> None:
        self._data: Dict[str, RedisValue] = {}

    def get(self, key: str) -> Optional[Union[str, bytes]]:
        val = self._data.get(key)
        if val is None:
            return None
        return val if isinstance(val, (str, bytes)) else str(val)

    def set(
        self,
        key: str,
        value: RedisValue,
        ex: Optional[int] = None,
    ) -> Optional[bool]:
        self._data[key] = value
        return True

        deleted_count = 0
        for key in keys:
            if key in self._data:
                del self._data[key]
                deleted_count += 1
        return deleted_count

    def keys(self, pattern: str) -> List[str]:
        """Glob-style: * matches any number of chars."""
        return [k for k in self._data if fnmatch.fnmatch(k, pattern)]

    def scan_iter(self, match: str = "*", count: Optional[int] = None):
        """SCAN-compatible iterator; yields keys matching pattern (count ignored in-memory)."""
        return iter(self.keys(match))


class InMemoryRedisCacheManager:
    """
    In-memory implementation of the RedisCacheManager interface: a dict for
    key -> value and a dict of index_prefix -> set of keys for set_with_index.
    """

    def __init__(self) -> None:
        self._redis = InMemoryRedis()
        self._index: Dict[str, Set[str]] = {}

    def add_key_to_index(self, index_prefix: str, key: str) -> None:
        self._index.setdefault(index_prefix, set()).add(key)

    def remove_key_from_index(self, index_prefix: str, key: str) -> None:
        s = self._index.get(index_prefix)
        if s is not None:
            s.discard(key)

    def get_keys_by_index(self, index_prefix: str) -> List[str]:
        return list(self._index.get(index_prefix, set()))

    def delete_index(self, index_prefix: str) -> None:
        self._index.pop(index_prefix, None)

    def set_with_index(
        self,
        key: str,
        value: RedisValue,
        index_prefix: str,
        expire_seconds: Optional[int] = None,
    ) -> Optional[bool]:
        result = self._redis.set(key, value, ex=expire_seconds)
        self.add_key_to_index(index_prefix, key)
        return result

    def delete_key_and_remove_from_index(
        self,
        key: str,
        index_prefix: str,
    ) -> None:
        self._redis.delete(key)
        self.remove_key_from_index(index_prefix, key)

    @property
    def redis(self) -> InMemoryRedis:
        return self._redis


@pytest.fixture
def in_memory_manager() -> InMemoryRedisCacheManager:
    return InMemoryRedisCacheManager()


@pytest.fixture
def dsr_store(in_memory_manager: InMemoryRedisCacheManager) -> DSRCacheStore:
    return DSRCacheStore(in_memory_manager)


@pytest.mark.unit
class TestDSRCacheStoreWithInMemoryManager:
    """DSRCacheStore behavior with an in-memory RedisCacheManager."""

    def test_set_and_get(self, dsr_store: DSRCacheStore) -> None:
        dsr_store.set("pr-1", "identity:email", "user@example.com")
        assert dsr_store.get("pr-1", "identity:email") == "user@example.com"

    def test_get_missing_returns_none(self, dsr_store: DSRCacheStore) -> None:
        assert dsr_store.get("pr-1", "identity:email") is None

    def test_set_with_index_registers_key_in_index(
        self, dsr_store: DSRCacheStore, in_memory_manager: InMemoryRedisCacheManager
    ) -> None:
        dsr_store.set("pr-1", "custom_field:foo", "bar")
        keys = in_memory_manager.get_keys_by_index("dsr:pr-1")
        assert "dsr:pr-1:custom_field:foo" in keys
        assert len(keys) == 1

    def test_get_all_keys_returns_indexed_keys(
        self, dsr_store: DSRCacheStore, in_memory_manager: InMemoryRedisCacheManager
    ) -> None:
        dsr_store.write_custom_field("pr-1", "f1", "v1")
        dsr_store.write_identity("pr-1", "email", "e@x.com")
        keys = dsr_store.get_all_keys("pr-1")
        assert set(keys) == {
            "dsr:pr-1:custom_field:f1",
            "dsr:pr-1:identity:email",
        }

    def test_clear_removes_all_keys_and_index(
        self, dsr_store: DSRCacheStore, in_memory_manager: InMemoryRedisCacheManager
    ) -> None:
        dsr_store.write_custom_field("pr-1", "f1", "v1")
        dsr_store.write_identity("pr-1", "email", "e@x.com")
        dsr_store.clear("pr-1")
        assert dsr_store.get_all_keys("pr-1") == []
        assert dsr_store.get("pr-1", "custom_field:f1") is None
        assert dsr_store.get("pr-1", "identity:email") is None

    def test_delete_removes_key_and_index_entry(
        self, dsr_store: DSRCacheStore, in_memory_manager: InMemoryRedisCacheManager
    ) -> None:
        dsr_store.set("pr-1", "identity:email", "e@x.com")
        dsr_store.delete("pr-1", "identity:email")
        assert dsr_store.get("pr-1", "identity:email") is None
        assert "dsr:pr-1:identity:email" not in dsr_store.get_all_keys("pr-1")

    def test_get_with_legacy_reads_new_key_first(
        self, dsr_store: DSRCacheStore, in_memory_manager: InMemoryRedisCacheManager
    ) -> None:
        dsr_store.write_identity("pr-1", "email", "new@example.com")
        # Legacy key not set; should still get from new key
        assert dsr_store.get_identity("pr-1", "email") == "new@example.com"

    def test_get_with_legacy_migrates_from_legacy_key(
        self, dsr_store: DSRCacheStore, in_memory_manager: InMemoryRedisCacheManager
    ) -> None:
        # Simulate legacy data only (no new key)
        in_memory_manager.redis.set("id-pr-1-identity-email", "legacy@example.com")
        result = dsr_store.get_identity("pr-1", "email")
        assert result == "legacy@example.com"
        # After migrate: new key should exist and legacy should be gone
        assert dsr_store.get("pr-1", "identity:email") == "legacy@example.com"
        assert in_memory_manager.redis.get("id-pr-1-identity-email") is None

    def test_write_custom_field_and_get_custom_field(
        self, dsr_store: DSRCacheStore
    ) -> None:
        dsr_store.write_custom_field("pr-1", "my_field", "my_value")
        assert dsr_store.get_custom_field("pr-1", "my_field") == "my_value"

    def test_convenience_async_execution(self, dsr_store: DSRCacheStore) -> None:
        dsr_store.write_async_execution("pr-1", "celery-task-id-xyz")
        assert dsr_store.get_async_execution("pr-1") == "celery-task-id-xyz"

    def test_retry_count(
        self, dsr_store: DSRCacheStore, in_memory_manager: InMemoryRedisCacheManager
    ) -> None:
        """Mirrors cache.py get/increment/reset_privacy_request_retry_count."""
        assert dsr_store.get_retry_count("pr-1") is None
        dsr_store.write_retry_count("pr-1", "3", expire_seconds=86400)
        assert dsr_store.get_retry_count("pr-1") == "3"
        dsr_store.delete("pr-1", "retry_count")
        assert dsr_store.get_retry_count("pr-1") is None
        # Legacy key migration
        in_memory_manager.redis.set("id-pr-2-privacy-request-retry-count", "1")
        assert dsr_store.get_retry_count("pr-2") == "1"
        assert (
            in_memory_manager.redis.get("id-pr-2-privacy-request-retry-count") is None
        )

    def test_drp(
        self, dsr_store: DSRCacheStore, in_memory_manager: InMemoryRedisCacheManager
    ) -> None:
        """Mirrors privacy_request.py DRP body cache (get_drp_request_body_cache_key)."""
        dsr_store.write_drp("pr-1", "address", "encrypted-body", expire_seconds=300)
        assert dsr_store.get_drp("pr-1", "address") == "encrypted-body"
        assert dsr_store.get_drp("pr-1", "email") is None
        # Legacy key migration
        in_memory_manager.redis.set("id-pr-2-drp-email", "legacy-drp")
        assert dsr_store.get_drp("pr-2", "email") == "legacy-drp"
        assert in_memory_manager.redis.get("id-pr-2-drp-email") is None

    def test_encryption(
        self, dsr_store: DSRCacheStore, in_memory_manager: InMemoryRedisCacheManager
    ) -> None:
        """Mirrors privacy_request.py / encryption_utils.py encryption key cache."""
        dsr_store.write_encryption("pr-1", "key", "enc-key-123", expire_seconds=3600)
        assert dsr_store.get_encryption("pr-1", "key") == "enc-key-123"
        assert dsr_store.get_encryption("pr-1", "other") is None
        # Legacy key migration
        in_memory_manager.redis.set("id-pr-2-encryption-key", "legacy-enc")
        assert dsr_store.get_encryption("pr-2", "key") == "legacy-enc"
        assert in_memory_manager.redis.get("id-pr-2-encryption-key") is None

    def test_masking_secret(
        self, dsr_store: DSRCacheStore, in_memory_manager: InMemoryRedisCacheManager
    ) -> None:
        """Mirrors secrets_util.get_masking_secret cache read (and write path)."""
        dsr_store.write_masking_secret(
            "pr-1", "hash", "salt", "encoded-secret", expire_seconds=600
        )
        assert dsr_store.get_masking_secret("pr-1", "hash", "salt") == "encoded-secret"
        assert dsr_store.get_masking_secret("pr-1", "hash", "other") is None
        # Legacy key migration
        in_memory_manager.redis.set(
            "id-pr-2-masking-secret-hash-pepper", "legacy-masking"
        )
        assert (
            dsr_store.get_masking_secret("pr-2", "hash", "pepper") == "legacy-masking"
        )
        assert in_memory_manager.redis.get("id-pr-2-masking-secret-hash-pepper") is None
