"""
Tests for identity cache operations in DSRCacheStore.

Tests the service layer directly with MockRedis - no patching needed.
"""

import json
import uuid

import pytest

from fides.common.cache.dsr_store import DSRCacheStore
from fides.common.cache.manager import RedisCacheManager

from tests.common.cache.mock_redis import MockRedis


@pytest.fixture
def mock_redis():
    """Shared MockRedis instance."""
    return MockRedis()


@pytest.fixture
def dsr_store(mock_redis):
    """DSRCacheStore backed by MockRedis."""
    return DSRCacheStore(RedisCacheManager(mock_redis))


@pytest.fixture
def pr_id():
    """Generate unique privacy request ID."""
    return f"test-pr-{uuid.uuid4()}"


@pytest.fixture
def identity_data():
    """Sample identity data for tests."""
    return {
        "email": "user@example.com",
        "phone_number": "+1234567890",
    }


# Mark all tests as unit tests
pytestmark = pytest.mark.unit


class TestDSRCacheStoreIdentity:
    """Test identity cache operations in DSRCacheStore."""

    def test_cache_identity_data_writes_all_attributes(self, dsr_store, pr_id):
        """cache_identity_data writes all identity attributes to new-format keys."""
        identity_data = {
            "email": json.dumps("user@example.com"),
            "phone_number": json.dumps("+1234567890"),
        }

        dsr_store.cache_identity_data(pr_id, identity_data, expire_seconds=3600)

        # All keys written in new format
        assert dsr_store._redis.get(f"dsr:{pr_id}:identity:email") == json.dumps("user@example.com")
        assert dsr_store._redis.get(f"dsr:{pr_id}:identity:phone_number") == json.dumps("+1234567890")
        
        # Legacy keys do NOT exist
        assert dsr_store._redis.get(f"id-{pr_id}-identity-email") is None

    def test_get_cached_identity_data_reads_all_attributes(self, dsr_store, pr_id, identity_data):
        """get_cached_identity_data reads all identity attributes from new-format keys."""
        # Write via store
        encoded_data = {k: json.dumps(v) for k, v in identity_data.items()}
        dsr_store.cache_identity_data(pr_id, encoded_data)

        result = dsr_store.get_cached_identity_data(pr_id)

        assert result["email"] == json.dumps("user@example.com")
        assert result["phone_number"] == json.dumps("+1234567890")

    def test_get_cached_identity_data_migrates_legacy_keys(self, dsr_store, mock_redis, pr_id, identity_data):
        """get_cached_identity_data reads and migrates legacy keys on first access."""
        # Write legacy format with JSON encoding
        for key, value in identity_data.items():
            mock_redis.set(f"id-{pr_id}-identity-{key}", json.dumps(value))

        result = dsr_store.get_cached_identity_data(pr_id)

        # Values are returned correctly
        assert result["email"] == json.dumps("user@example.com")
        assert result["phone_number"] == json.dumps("+1234567890")

        # Legacy keys migrated to new format
        assert mock_redis.get(f"dsr:{pr_id}:identity:email") is not None
        assert mock_redis.get(f"id-{pr_id}-identity-email") is None

    def test_has_cached_identity_data_detects_both_formats(self, dsr_store, mock_redis, pr_id):
        """has_cached_identity_data detects identity data in both legacy and new formats."""
        # Empty initially
        assert dsr_store.has_cached_identity_data(pr_id) is False

        # Add legacy key
        mock_redis.set(f"id-{pr_id}-identity-email", json.dumps("test@example.com"))
        assert dsr_store.has_cached_identity_data(pr_id) is True

        # Clear and test new format
        mock_redis._data.clear()
        dsr_store.write_identity(pr_id, "email", json.dumps("test@example.com"))
        assert dsr_store.has_cached_identity_data(pr_id) is True
