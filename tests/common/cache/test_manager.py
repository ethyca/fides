"""
Unit tests for RedisCacheManager pipeline operations.

MockRedis and MockPipeline are inline for easy updates when MockClient
lands upstream - replace with an import.
"""

import fnmatch

import pytest

from fides.common.cache.manager import RedisCacheManager

# --- Inline MockRedis (replace with MockClient import when available) ---


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
