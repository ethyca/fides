"""
Tests for identity cache operations in DSRCacheStore.

Tests the service layer directly with MockRedis - no patching needed.
"""

import json

import pytest

from fides.common.cache.dsr_store import DSRCacheStore


@pytest.fixture
def identity_data():
    """Sample identity data for tests."""
    return {
        "email": "user@example.com",
        "phone_number": "+1234567890",
    }


# Mark all tests as unit tests
pytestmark = pytest.mark.unit

_TTL = 3600  # Test TTL


class TestDSRCacheStoreIdentity:
    """Test identity cache operations in DSRCacheStore."""

    def test_cache_identity_data_writes_all_attributes(
        self, manager, mock_redis, pr_id
    ):
        """cache_identity_data writes all identity attributes to new-format keys."""
        store = DSRCacheStore(pr_id, manager)
        identity_data = {
            "email": json.dumps("user@example.com"),
            "phone_number": json.dumps("+1234567890"),
        }

        store.cache_identity_data(identity_data, expire_seconds=3600)

        # All keys written in new format
        assert mock_redis.get(f"dsr:{pr_id}:identity:email") == json.dumps(
            "user@example.com"
        )
        assert mock_redis.get(f"dsr:{pr_id}:identity:phone_number") == json.dumps(
            "+1234567890"
        )

        # Legacy keys do NOT exist
        assert mock_redis.get(f"id-{pr_id}-identity-email") is None

    def test_get_cached_identity_data_reads_all_attributes(
        self, manager, pr_id, identity_data
    ):
        """get_cached_identity_data reads all identity attributes from new-format keys."""
        store = DSRCacheStore(pr_id, manager)
        # Write via store
        encoded_data = {k: json.dumps(v) for k, v in identity_data.items()}
        store.cache_identity_data(encoded_data, _TTL)

        result = store.get_cached_identity_data()

        assert result["email"] == json.dumps("user@example.com")
        assert result["phone_number"] == json.dumps("+1234567890")

    def test_get_cached_identity_data_migrates_legacy_keys(
        self, manager, mock_redis, pr_id, identity_data
    ):
        """get_cached_identity_data reads and migrates legacy keys on first access."""
        store = DSRCacheStore(pr_id, manager)
        # Write legacy format with JSON encoding
        for key, value in identity_data.items():
            mock_redis.set(f"id-{pr_id}-identity-{key}", json.dumps(value))

        result = store.get_cached_identity_data()

        # Values are returned correctly
        assert result["email"] == json.dumps("user@example.com")
        assert result["phone_number"] == json.dumps("+1234567890")

        # Legacy keys migrated to new format
        assert mock_redis.get(f"dsr:{pr_id}:identity:email") is not None
        assert mock_redis.get(f"id-{pr_id}-identity-email") is None

    def test_has_cached_identity_data_detects_both_formats(
        self, manager, mock_redis, pr_id
    ):
        """has_cached_identity_data detects identity data in both legacy and new formats."""
        store = DSRCacheStore(pr_id, manager)
        # Empty initially
        assert store.has_cached_identity_data() is False

        # Add legacy key
        mock_redis.set(f"id-{pr_id}-identity-email", json.dumps("test@example.com"))
        assert store.has_cached_identity_data() is True

        # Clear and test new format
        store.clear()
        store.write_identity("email", json.dumps("test@example.com"), _TTL)
        assert store.has_cached_identity_data() is True
