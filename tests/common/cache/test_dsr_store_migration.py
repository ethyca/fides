"""
Tests for DSRCacheStore migration behavior with legacy keys.

Verifies existing cached data (legacy format) is correctly read, migrated, and cleared.
"""

import fnmatch
import uuid
from typing import Dict, List, Optional, Set, Union

import pytest

from fides.common.cache.dsr_store import DSRCacheStore
from fides.common.cache.manager import RedisCacheManager

RedisValue = Union[bytes, float, int, str]


class MockRedis:
    """Mock Redis with minimal interface for DSRCacheStore."""

    def __init__(self) -> None:
        self._data: Dict[str, RedisValue] = {}
        self._sets: Dict[str, Set[Union[str, bytes]]] = {}

    def get(self, key: str) -> Optional[Union[str, bytes]]:
        val = self._data.get(key)
        return val if isinstance(val, (str, bytes)) else str(val) if val else None

    def set(self, key: str, value: RedisValue, ex: Optional[int] = None) -> bool:
        self._data[key] = value
        return True

    def delete(self, *keys: str) -> int:
        deleted = sum(1 for k in keys if self._data.pop(k, None) or self._sets.pop(k, None))
        return deleted

    def keys(self, pattern: str) -> List[str]:
        return [k for k in self._data if fnmatch.fnmatch(k, pattern)]

    def scan_iter(self, match: str = "*", count: Optional[int] = None):
        return iter(self.keys(match))

    def sadd(self, key: str, *members: Union[str, bytes]) -> int:
        s = self._sets.setdefault(key, set())
        before = len(s)
        s.update(members)
        return len(s) - before

    def srem(self, key: str, *members: Union[str, bytes]) -> int:
        if key not in self._sets:
            return 0
        before = len(self._sets[key])
        self._sets[key].difference_update(members)
        return before - len(self._sets[key])

    def smembers(self, key: str) -> Set[Union[str, bytes]]:
        return self._sets.get(key, set()).copy()


# Test data factories
def make_dsr_id() -> str:
    """Generate unique DSR ID."""
    return f"test-pr-{uuid.uuid4()}"


def make_legacy_key(dsr_id: str, field_type: str, field_name: str = "") -> str:
    """Build legacy key format."""
    if field_name:
        return f"id-{dsr_id}-{field_type}-{field_name}"
    return f"id-{dsr_id}-{field_type}"


def make_new_key(dsr_id: str, part: str) -> str:
    """Build new DSR key format."""
    return f"dsr:{dsr_id}:{part}"


@pytest.fixture
def mock_redis():
    return MockRedis()


@pytest.fixture
def dsr_store(mock_redis):
    return DSRCacheStore(RedisCacheManager(mock_redis))


@pytest.fixture
def dsr_id():
    return make_dsr_id()


@pytest.mark.unit
class TestLegacyKeyMigration:
    """Test legacy key formats are readable and migrated correctly."""

    @pytest.mark.parametrize("field_type,getter,field_key,value", [
        ("identity", "get_identity", "email", "user@example.com"),
        ("custom-privacy-request-field", "get_custom_field", "dept", "Engineering"),
        ("encryption", "get_encryption", "key", "encryption-key-123"),
        ("async-execution", "get_async_execution", "", "celery-task-123"),
        ("privacy-request-retry-count", "get_retry_count", "", "3"),
        ("drp", "get_drp", "email", "drp@example.com"),
        ("masking-secret-hash", "get_masking_secret", "salt", "secret-123"),
    ])
    def test_legacy_keys_readable(
        self, mock_redis, dsr_store, dsr_id, field_type, getter, field_key, value
    ):
        """Legacy keys are readable via store convenience methods."""
        legacy_key = make_legacy_key(dsr_id, field_type, field_key)
        mock_redis.set(legacy_key, value)

        # Call appropriate getter
        if getter == "get_masking_secret":
            result = dsr_store.get_masking_secret(dsr_id, "hash", field_key)
        elif field_key:
            result = getattr(dsr_store, getter)(dsr_id, field_key)
        else:
            result = getattr(dsr_store, getter)(dsr_id)

        assert result == value

    def test_legacy_key_migrated_on_read(self, mock_redis, dsr_store, dsr_id):
        """Legacy key is migrated to new format on first read."""
        mock_redis.set(make_legacy_key(dsr_id, "identity", "email"), "migrate@test.com")

        email = dsr_store.get_identity(dsr_id, "email")
        assert email == "migrate@test.com"

        # New key exists, legacy deleted, index updated
        assert mock_redis.get(make_new_key(dsr_id, "identity:email")) == "migrate@test.com"
        assert mock_redis.get(make_legacy_key(dsr_id, "identity", "email")) is None
        assert make_new_key(dsr_id, "identity:email") in mock_redis.smembers(f"__idx:dsr:{dsr_id}")

    def test_new_writes_create_indexed_keys_only(self, mock_redis, dsr_store, dsr_id):
        """New writes create new-format keys and index them; no legacy keys written."""
        dsr_store.write_identity(dsr_id, "email", "new@example.com")
        dsr_store.write_custom_field(dsr_id, "department", "Sales")

        assert mock_redis.get(make_new_key(dsr_id, "identity:email")) == "new@example.com"
        assert mock_redis.get(make_new_key(dsr_id, "custom_field:department")) == "Sales"
        assert mock_redis.get(make_legacy_key(dsr_id, "identity", "email")) is None
        assert mock_redis.get(make_legacy_key(dsr_id, "custom-privacy-request-field", "department")) is None

    def test_clear_removes_mixed_keys(self, mock_redis, dsr_store, dsr_id):
        """clear() removes both legacy and new keys using SCAN."""
        mock_redis.set(make_legacy_key(dsr_id, "identity", "email"), "legacy@test.com")
        mock_redis.set(make_legacy_key(dsr_id, "encryption", "key"), "legacy-key")
        dsr_store.write_identity(dsr_id, "phone_number", "+1234567890")
        dsr_store.write_custom_field(dsr_id, "department", "Engineering")

        dsr_store.clear(dsr_id)

        assert len(mock_redis.keys(f"*{dsr_id}*")) == 0

    def test_index_backfill(self, mock_redis, dsr_id):
        """Legacy keys are backfilled into index when enabled."""
        mock_redis.set(make_legacy_key(dsr_id, "identity", "email"), "test@example.com")
        mock_redis.set(make_legacy_key(dsr_id, "identity", "phone_number"), "+1234567890")

        store = DSRCacheStore(RedisCacheManager(mock_redis), backfill_index_on_legacy_read=True)
        keys = store.get_all_keys(dsr_id)

        assert len(keys) == 2
        assert len(mock_redis.smembers(f"__idx:dsr:{dsr_id}")) == 2


@pytest.mark.unit
class TestMultipleRequestIsolation:
    """Test DSR IDs don't interfere with each other."""

    def test_mixed_dsr_states(self, mock_redis):
        """Operations on one DSR don't affect others (legacy, new, mixed)."""
        dsr1, dsr2, dsr3 = make_dsr_id(), make_dsr_id(), make_dsr_id()
        store = DSRCacheStore(RedisCacheManager(mock_redis))

        # DSR1: legacy, DSR2: new, DSR3: mixed
        mock_redis.set(make_legacy_key(dsr1, "identity", "email"), "dsr1@test.com")
        store.write_identity(dsr2, "email", "dsr2@test.com")
        mock_redis.set(make_legacy_key(dsr3, "identity", "email"), "dsr3@test.com")
        store.write_identity(dsr3, "phone_number", "+1234567890")

        # Verify all readable
        assert store.get_identity(dsr1, "email") == "dsr1@test.com"
        assert store.get_identity(dsr2, "email") == "dsr2@test.com"
        assert store.get_identity(dsr3, "email") == "dsr3@test.com"
        assert store.get_identity(dsr3, "phone_number") == "+1234567890"

        # Clear DSR2 doesn't affect others
        store.clear(dsr2)
        assert store.get_identity(dsr1, "email") == "dsr1@test.com"
        assert store.get_identity(dsr3, "email") == "dsr3@test.com"
        assert store.get_identity(dsr2, "email") is None
        assert store.get_all_keys(dsr2) == []

    def test_clear_isolation(self, mock_redis):
        """Clearing one DSR doesn't delete another's keys."""
        dsr1, dsr2 = make_dsr_id(), make_dsr_id()
        store = DSRCacheStore(RedisCacheManager(mock_redis))

        store.write_identity(dsr1, "email", "dsr1@test.com")
        store.write_identity(dsr2, "email", "dsr2@test.com")

        store.clear(dsr1)

        assert mock_redis.get(make_new_key(dsr1, "identity:email")) is None
        assert mock_redis.get(make_new_key(dsr2, "identity:email")) == "dsr2@test.com"


def _run_standalone_tests() -> None:
    """Run tests standalone without pytest."""
    def setup():
        redis, dsr_id = MockRedis(), make_dsr_id()
        store = DSRCacheStore(RedisCacheManager(redis))
        return redis, store, dsr_id

    # Test each scenario
    test_cases = [
        ("identity", "email", "user@test.com"),
        ("encryption", "key", "test-key"),
        ("async-execution", "", "task-123"),
    ]
    
    for field_type, field_key, value in test_cases:
        redis, store, dsr_id = setup()
        redis.set(make_legacy_key(dsr_id, field_type, field_key), value)
        getter = {
            "identity": lambda: store.get_identity(dsr_id, field_key),
            "encryption": lambda: store.get_encryption(dsr_id, field_key),
            "async-execution": lambda: store.get_async_execution(dsr_id),
        }[field_type]
        assert getter() == value

    # Migration test
    redis, store, dsr_id = setup()
    redis.set(make_legacy_key(dsr_id, "identity", "email"), "migrate@test.com")
    assert store.get_identity(dsr_id, "email") == "migrate@test.com"
    assert redis.get(make_new_key(dsr_id, "identity:email")) == "migrate@test.com"
    assert redis.get(make_legacy_key(dsr_id, "identity", "email")) is None

    # Clear test
    redis, store, dsr_id = setup()
    redis.set(make_legacy_key(dsr_id, "identity", "email"), "test@test.com")
    store.write_identity(dsr_id, "phone", "+123")
    store.clear(dsr_id)
    assert len(redis.keys(f"*{dsr_id}*")) == 0

    # Isolation test
    redis = MockRedis()
    store = DSRCacheStore(RedisCacheManager(redis))
    dsr1, dsr2 = make_dsr_id(), make_dsr_id()
    store.write_identity(dsr1, "email", "dsr1@test.com")
    store.write_identity(dsr2, "email", "dsr2@test.com")
    store.clear(dsr1)
    assert redis.get(make_new_key(dsr2, "identity:email")) == "dsr2@test.com"

    print("All DSR store migration tests passed.")


if __name__ == "__main__":
    _run_standalone_tests()
