import fnmatch

import pytest

from fides.common.cache.manager import INDEX_TTL_EXTRA_SECONDS, RedisCacheManager


class MockPipeline:
    """In-memory pipeline that batches commands and executes atomically."""

    def __init__(self, data: dict, sets: dict) -> None:
        self._data = data
        self._sets = sets
        self._commands: list = []

    def set(self, key: str, value, ex=None) -> "MockPipeline":
        self._commands.append(("set", (key, value, ex)))
        return self

    def sadd(self, key: str, member: str) -> "MockPipeline":
        self._commands.append(("sadd", (key, member)))
        return self

    def delete(self, *keys: str) -> "MockPipeline":
        self._commands.append(("delete", keys))
        return self

    def srem(self, key: str, member: str) -> "MockPipeline":
        self._commands.append(("srem", (key, member)))
        return self

    def execute(self) -> list:
        results = []
        for op, args in self._commands:
            if op == "set":
                key, value, _ = args
                self._data[key] = value
                results.append(True)
            elif op == "sadd":
                key, member = args
                if key not in self._sets:
                    self._sets[key] = set()
                self._sets[key].add(member)
                results.append(1)
            elif op == "delete":
                for k in args:
                    self._data.pop(k, None)
                    self._sets.pop(k, None)
                results.append(len(args))
            elif op == "srem":
                key, member = args
                if key in self._sets:
                    self._sets[key].discard(member)
                    if not self._sets[key]:
                        del self._sets[key]
                results.append(1)
        self._commands = []
        return results


class MockRedis:
    """In-memory Redis mock for RedisCacheManager tests."""

    def __init__(self) -> None:
        self._data: dict = {}
        self._sets: dict = {}
        self._ttl: dict = {}  # key -> seconds until expiry (simplified; no decay)

    def get(self, key: str):
        return self._data.get(key)

    def set(self, key: str, value, ex=None) -> bool:
        self._data[key] = value
        return True

    def delete(self, *keys: str) -> int:
        count = 0
        for k in keys:
            if k in self._data:
                del self._data[k]
                count += 1
            if k in self._sets:
                del self._sets[k]
                count += 1
            self._ttl.pop(k, None)
        return count

    def sadd(self, key: str, member: str) -> int:
        if key not in self._sets:
            self._sets[key] = set()
        self._sets[key].add(member)
        return 1

    def srem(self, key: str, member: str) -> int:
        if key in self._sets:
            self._sets[key].discard(member)
            if not self._sets[key]:
                del self._sets[key]
            return 1
        return 0

    def smembers(self, key: str) -> set:
        return self._sets.get(key, set()).copy()

    def keys(self, pattern: str = "*") -> list:
        all_keys = set(self._data) | set(self._sets)
        return [k for k in all_keys if fnmatch.fnmatch(k, pattern)]

    def ttl(self, key: str) -> int:
        if key not in self._data and key not in self._sets:
            return -2
        return self._ttl.get(key, -1)

    def expire(self, key: str, seconds: int) -> bool:
        if key in self._data or key in self._sets:
            self._ttl[key] = seconds
            return True
        return False

    def pipeline(self) -> MockPipeline:
        return MockPipeline(self._data, self._sets)


# --- Fixtures ---


@pytest.fixture
def mock_redis() -> MockRedis:
    return MockRedis()


@pytest.fixture
def manager(mock_redis: MockRedis) -> RedisCacheManager:
    return RedisCacheManager(mock_redis)


# --- Tests ---


@pytest.mark.unit
class TestRedisCacheManagerPipeline:
    """Tests for RedisCacheManager pipeline-based index operations."""

    def test_set_with_index_uses_pipeline_and_returns_set_result(
        self, manager: RedisCacheManager, mock_redis: MockRedis
    ) -> None:
        """set_with_index stores key, adds to index, and returns SET result."""
        result = manager.set_with_index("k1", "v1", "idx1")

        assert result is True
        assert mock_redis.get("k1") == "v1"
        assert "k1" in mock_redis.smembers("__idx:idx1")

    def test_set_with_index_with_expiry(
        self, manager: RedisCacheManager, mock_redis: MockRedis
    ) -> None:
        """set_with_index with expire_seconds stores value and adds to index."""
        result = manager.set_with_index("k2", "v2", "idx2", expire_seconds=60)

        assert result is True
        assert mock_redis.get("k2") == "v2"
        assert "k2" in mock_redis.smembers("__idx:idx2")

    def test_delete_key_and_remove_from_index_atomic(
        self, manager: RedisCacheManager, mock_redis: MockRedis
    ) -> None:
        """delete_key_and_remove_from_index removes key and index entry atomically."""
        manager.set_with_index("k3", "v3", "idx3")
        assert mock_redis.get("k3") == "v3"
        assert "k3" in mock_redis.smembers("__idx:idx3")

        manager.delete_key_and_remove_from_index("k3", "idx3")

        assert mock_redis.get("k3") is None
        assert "k3" not in mock_redis.smembers("__idx:idx3")

    def test_delete_keys_by_index_batches_deletes(
        self, manager: RedisCacheManager, mock_redis: MockRedis
    ) -> None:
        """delete_keys_by_index removes all indexed keys and the index in one pipeline."""
        manager.set_with_index("k4a", "v4a", "idx4")
        manager.set_with_index("k4b", "v4b", "idx4")
        manager.set_with_index("k4c", "v4c", "idx4")

        manager.delete_keys_by_index("idx4")

        assert mock_redis.get("k4a") is None
        assert mock_redis.get("k4b") is None
        assert mock_redis.get("k4c") is None
        assert mock_redis.smembers("__idx:idx4") == set()

    def test_delete_keys_by_index_empty_index(
        self, manager: RedisCacheManager, mock_redis: MockRedis
    ) -> None:
        """delete_keys_by_index on empty index deletes index set without error."""
        manager.delete_keys_by_index("idx5")

        assert mock_redis.smembers("__idx:idx5") == set()


@pytest.mark.unit
class TestRedisCacheManagerIndexOperations:
    """Tests for add_key_to_index, remove_key_from_index, get_keys_by_index, delete_index."""

    def test_add_key_to_index_registers_key(
        self, manager: RedisCacheManager, mock_redis: MockRedis
    ) -> None:
        """Ensure that add_key_to_index adds the key and creates the index set if it doesn't exist."""
        manager.add_key_to_index("myidx", "cache_key_1")

        assert "cache_key_1" in mock_redis.smembers("__idx:myidx")

    def test_add_key_to_index_multiple_keys(
        self, manager: RedisCacheManager, mock_redis: MockRedis
    ) -> None:
        """Ensure that add_key_to_index can add multiple keys to the same index."""
        manager.add_key_to_index("idx6", "key_a")
        manager.add_key_to_index("idx6", "key_b")
        manager.add_key_to_index("idx6", "key_c")

        members = mock_redis.smembers("__idx:idx6")
        assert members == {"key_a", "key_b", "key_c"}

    def test_remove_key_from_index_idempotent(
        self, manager: RedisCacheManager, mock_redis: MockRedis
    ) -> None:
        """Ensure that remove_key_from_index is idempotent and does not error when the specified key is not in the index."""
        manager.set_with_index("key_a", "value_a", "idx6")
        manager.set_with_index("key_b", "value_b", "idx6")

        manager.remove_key_from_index("idx6", "key_a")

        # Should not remove other keys when the key is in the index and does not remove the key from the cache
        assert mock_redis.smembers("__idx:idx6") == {"key_b"}
        assert mock_redis.get("key_a") == "value_a"
        assert mock_redis.get("key_b") == "value_b"

        # Should not error when the key is not in the index and does not remove other keys
        manager.remove_key_from_index("idx6", "key_a")

        assert mock_redis.smembers("__idx:idx6") == {"key_b"}
        assert mock_redis.get("key_a") == "value_a"
        assert mock_redis.get("key_b") == "value_b"

    def test_remove_key_from_index_unregisters_key(
        self, manager: RedisCacheManager, mock_redis: MockRedis
    ) -> None:
        """Ensure that remove_key_from_index removes a key from the index and does not remove other keys."""
        manager.add_key_to_index("idx7", "keep")
        manager.add_key_to_index("idx7", "remove_me")

        manager.remove_key_from_index("idx7", "remove_me")

        assert mock_redis.smembers("__idx:idx7") == {"keep"}

    def test_remove_key_from_index_does_not_error_when_missing(
        self, manager: RedisCacheManager, mock_redis: MockRedis
    ) -> None:
        """Ensure that remove_key_from_index does not error when the specified key is not in the index, and does not remove other keys."""
        manager.add_key_to_index("idx8", "existing")

        manager.remove_key_from_index("idx8", "nonexistent")

        assert mock_redis.smembers("__idx:idx8") == {"existing"}

    def test_get_keys_by_index_returns_empty_for_missing_index(
        self, manager: RedisCacheManager, mock_redis: MockRedis
    ) -> None:
        """Ensure that get_keys_by_index returns an empty list when the specified index does not exist."""
        keys = manager.get_keys_by_index("never_used")

        assert keys == []

    def test_get_keys_by_index_returns_registered_keys(
        self, manager: RedisCacheManager, mock_redis: MockRedis
    ) -> None:
        """Ensure get_keys_by_index returns all the keys in the index."""
        manager.add_key_to_index("idx9", "k1")
        manager.add_key_to_index("idx9", "k2")

        keys = manager.get_keys_by_index("idx9")

        assert set(keys) == {"k1", "k2"}
        assert len(keys) == 2

    def test_delete_index_removes_index_set_only(
        self, manager: RedisCacheManager, mock_redis: MockRedis
    ) -> None:
        """Ensure that delete_index removes the index set but NOT the data keys that are still in the cache."""
        mock_redis.set("data_key_1", "value1")
        manager.add_key_to_index("idx10", "data_key_1")

        manager.delete_index("idx10")

        assert mock_redis.smembers("__idx:idx10") == set()
        assert mock_redis.get("data_key_1") == "value1"

    def test_delete_index_does_not_error_when_empty(
        self, manager: RedisCacheManager, mock_redis: MockRedis
    ) -> None:
        """Ensure that delete_index does not error when the specified  index does not exist."""
        manager.delete_index("nonexistent_idx")


@pytest.mark.unit
class TestRedisCacheManagerIndexTTL:
    """Tests for optional index TTL (index_ttl_enabled)."""

    def test_index_ttl_disabled_by_default(
        self, manager: RedisCacheManager, mock_redis: MockRedis
    ) -> None:
        """Without index_ttl_enabled, index has no TTL."""
        manager.set_with_index("k", "v", "idx", expire_seconds=60)

        assert mock_redis.ttl("__idx:idx") == -1

    def test_index_ttl_applied_when_enabled(
        self, manager: RedisCacheManager, mock_redis: MockRedis
    ) -> None:
        """With index_ttl_enabled, index gets TTL matching key."""
        manager.set_with_index(
            "k", "v", "idx", expire_seconds=120, index_ttl_enabled=True
        )

        assert mock_redis.ttl("__idx:idx") == 120 + INDEX_TTL_EXTRA_SECONDS

    def test_index_ttl_extended_when_key_ttl_farther_out(
        self, manager: RedisCacheManager, mock_redis: MockRedis
    ) -> None:
        """Index TTL is pushed out when adding key with longer TTL."""
        manager.set_with_index(
            "k1", "v1", "idx", expire_seconds=60, index_ttl_enabled=True
        )
        assert mock_redis.ttl("__idx:idx") == 60 + INDEX_TTL_EXTRA_SECONDS

        manager.set_with_index(
            "k2", "v2", "idx", expire_seconds=300, index_ttl_enabled=True
        )

        assert mock_redis.ttl("__idx:idx") == 300 + INDEX_TTL_EXTRA_SECONDS

    def test_index_ttl_not_shortened_when_key_ttl_shorter(
        self, manager: RedisCacheManager, mock_redis: MockRedis
    ) -> None:
        """Index TTL is NOT shortened when adding key with shorter TTL."""
        manager.set_with_index(
            "k1", "v1", "idx", expire_seconds=300, index_ttl_enabled=True
        )
        assert mock_redis.ttl("__idx:idx") == 300 + INDEX_TTL_EXTRA_SECONDS

        manager.set_with_index(
            "k2", "v2", "idx", expire_seconds=60, index_ttl_enabled=True
        )

        assert mock_redis.ttl("__idx:idx") == 300 + INDEX_TTL_EXTRA_SECONDS

    def test_index_ttl_ignored_when_no_expire_seconds(
        self, manager: RedisCacheManager, mock_redis: MockRedis
    ) -> None:
        """index_ttl_enabled has no effect when expire_seconds is not set."""
        manager.set_with_index("k", "v", "idx", index_ttl_enabled=True)

        assert mock_redis.ttl("__idx:idx") == -1
