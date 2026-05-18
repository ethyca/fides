"""
Tests for DSRCacheStore migration behavior with legacy keys.

Verifies existing cached data (legacy format) is correctly read, migrated, and cleared.
"""

import uuid

import pytest

from fides.common.cache.dsr_store import DSRCacheStore
from fides.common.cache.manager import RedisCacheManager

_TTL = 3600  # Test TTL


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


@pytest.mark.unit
class TestLegacyKeyMigration:
    """Test legacy key formats are readable and migrated correctly."""

    @pytest.mark.parametrize(
        "field_type,getter,field_key,value",
        [
            ("identity", "get_identity", "email", "user@example.com"),
            ("custom-privacy-request-field", "get_custom_field", "dept", "Engineering"),
            ("encryption", "get_encryption", "key", "encryption-key-123"),
            ("async-execution", "get_async_execution", "", "celery-task-123"),
            ("privacy-request-retry-count", "get_retry_count", "", "3"),
            ("drp", "get_drp", "email", "drp@example.com"),
            ("masking-secret-hash", "get_masking_secret", "salt", "secret-123"),
        ],
    )
    def test_legacy_keys_readable(
        self, mock_redis, manager, dsr_id, field_type, getter, field_key, value
    ):
        """Legacy keys are readable via store convenience methods."""
        store = DSRCacheStore(dsr_id, manager)
        legacy_key = make_legacy_key(dsr_id, field_type, field_key)
        mock_redis.set(legacy_key, value)

        # Call appropriate getter
        if getter == "get_masking_secret":
            result = store.get_masking_secret("hash", field_key)
        elif field_key:
            result = getattr(store, getter)(field_key)
        else:
            result = getattr(store, getter)()

        assert result == value

    def test_legacy_key_migrated_on_read(self, mock_redis, manager, dsr_id):
        """Legacy key is migrated to new format on first read."""
        store = DSRCacheStore(dsr_id, manager)
        mock_redis.set(make_legacy_key(dsr_id, "identity", "email"), "migrate@test.com")

        email = store.get_identity("email")
        assert email == "migrate@test.com"

        # New key exists, legacy deleted, index updated
        assert (
            mock_redis.get(make_new_key(dsr_id, "identity:email")) == "migrate@test.com"
        )
        assert mock_redis.get(make_legacy_key(dsr_id, "identity", "email")) is None
        assert make_new_key(dsr_id, "identity:email") in mock_redis.smembers(
            f"__idx:dsr:{dsr_id}"
        )

    def test_new_writes_create_indexed_keys_only(self, mock_redis, manager, dsr_id):
        """New writes create new-format keys and index them; no legacy keys written."""
        store = DSRCacheStore(dsr_id, manager)
        store.write_identity("email", "new@example.com", _TTL)
        store.write_custom_field("department", "Sales", _TTL)

        assert (
            mock_redis.get(make_new_key(dsr_id, "identity:email")) == "new@example.com"
        )
        assert (
            mock_redis.get(make_new_key(dsr_id, "custom_field:department")) == "Sales"
        )
        assert mock_redis.get(make_legacy_key(dsr_id, "identity", "email")) is None
        assert (
            mock_redis.get(
                make_legacy_key(dsr_id, "custom-privacy-request-field", "department")
            )
            is None
        )

    def test_clear_removes_mixed_keys(self, mock_redis, manager, dsr_id):
        """clear() removes both legacy and new keys using SCAN."""
        store = DSRCacheStore(dsr_id, manager)
        mock_redis.set(make_legacy_key(dsr_id, "identity", "email"), "legacy@test.com")
        mock_redis.set(make_legacy_key(dsr_id, "encryption", "key"), "legacy-key")
        store.write_identity("phone_number", "+1234567890", _TTL)
        store.write_custom_field("department", "Engineering", _TTL)

        store.clear()

        assert len(mock_redis.keys(f"*{dsr_id}*")) == 0

    def test_index_backfill(self, mock_redis, dsr_id):
        """Legacy keys are backfilled into index when enabled."""
        mock_redis.set(make_legacy_key(dsr_id, "identity", "email"), "test@example.com")
        mock_redis.set(
            make_legacy_key(dsr_id, "identity", "phone_number"), "+1234567890"
        )

        store = DSRCacheStore(
            dsr_id,
            RedisCacheManager(mock_redis),
            backfill_index_on_legacy_read=True,
        )
        keys = store.get_all_keys()

        assert len(keys) == 2
        assert len(mock_redis.smembers(f"__idx:dsr:{dsr_id}")) == 2


@pytest.mark.unit
class TestMultipleRequestIsolation:
    """Test DSR IDs don't interfere with each other."""

    def test_mixed_dsr_states(self, mock_redis):
        """Operations on one DSR don't affect others (legacy, new, mixed)."""
        dsr1, dsr2, dsr3 = make_dsr_id(), make_dsr_id(), make_dsr_id()
        mgr = RedisCacheManager(mock_redis)
        store1 = DSRCacheStore(dsr1, mgr)
        store2 = DSRCacheStore(dsr2, mgr)
        store3 = DSRCacheStore(dsr3, mgr)

        # DSR1: legacy, DSR2: new, DSR3: mixed
        mock_redis.set(make_legacy_key(dsr1, "identity", "email"), "dsr1@test.com")
        store2.write_identity("email", "dsr2@test.com", _TTL)
        mock_redis.set(make_legacy_key(dsr3, "identity", "email"), "dsr3@test.com")
        store3.write_identity("phone_number", "+1234567890", _TTL)

        # Verify all readable
        assert store1.get_identity("email") == "dsr1@test.com"
        assert store2.get_identity("email") == "dsr2@test.com"
        assert store3.get_identity("email") == "dsr3@test.com"
        assert store3.get_identity("phone_number") == "+1234567890"

        # Clear DSR2 doesn't affect others
        store2.clear()
        assert store1.get_identity("email") == "dsr1@test.com"
        assert store3.get_identity("email") == "dsr3@test.com"
        assert store2.get_identity("email") is None
        assert store2.get_all_keys() == []

    def test_clear_isolation(self, mock_redis):
        """Clearing one DSR doesn't delete another's keys."""
        dsr1, dsr2 = make_dsr_id(), make_dsr_id()
        mgr = RedisCacheManager(mock_redis)
        store1 = DSRCacheStore(dsr1, mgr)
        store2 = DSRCacheStore(dsr2, mgr)

        store1.write_identity("email", "dsr1@test.com", _TTL)
        store2.write_identity("email", "dsr2@test.com", _TTL)

        store1.clear()

        assert mock_redis.get(make_new_key(dsr1, "identity:email")) is None
        assert mock_redis.get(make_new_key(dsr2, "identity:email")) == "dsr2@test.com"
