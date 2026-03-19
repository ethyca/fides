"""
Tests for custom fields and encryption cache operations in DSRCacheStore.

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


# Mark all tests as unit tests
pytestmark = pytest.mark.unit


class TestDSRCacheStoreCustomFields:
    """Test custom fields cache operations in DSRCacheStore."""

    def test_cache_custom_fields_writes_all_fields(self, dsr_store, pr_id):
        """cache_custom_fields writes all fields to new-format keys."""
        custom_fields = {
            "department": json.dumps("Engineering"),
            "employee_id": json.dumps("E12345"),
        }

        dsr_store.cache_custom_fields(pr_id, custom_fields, expire_seconds=3600)

        # All keys written in new format
        assert dsr_store._redis.get(f"dsr:{pr_id}:custom_field:department") == json.dumps("Engineering")
        assert dsr_store._redis.get(f"dsr:{pr_id}:custom_field:employee_id") == json.dumps("E12345")
        
        # Legacy keys do NOT exist
        assert dsr_store._redis.get(f"id-{pr_id}-custom-privacy-request-field-department") is None

    def test_get_cached_custom_fields_reads_all_fields(self, dsr_store, pr_id):
        """get_cached_custom_fields reads all fields from new-format keys."""
        custom_fields = {
            "department": json.dumps("Engineering"),
            "employee_id": json.dumps("E12345"),
        }
        dsr_store.cache_custom_fields(pr_id, custom_fields)

        result = dsr_store.get_cached_custom_fields(pr_id)

        assert result["department"] == json.dumps("Engineering")
        assert result["employee_id"] == json.dumps("E12345")

    def test_get_cached_custom_fields_migrates_legacy_keys(self, dsr_store, mock_redis, pr_id):
        """get_cached_custom_fields reads and migrates legacy keys on first access."""
        # Write legacy format
        mock_redis.set(f"id-{pr_id}-custom-privacy-request-field-department", json.dumps("Engineering"))
        mock_redis.set(f"id-{pr_id}-custom-privacy-request-field-employee_id", json.dumps("E12345"))

        result = dsr_store.get_cached_custom_fields(pr_id)

        # Values are returned correctly
        assert result["department"] == json.dumps("Engineering")
        assert result["employee_id"] == json.dumps("E12345")

        # Legacy keys migrated to new format
        assert mock_redis.get(f"dsr:{pr_id}:custom_field:department") is not None
        assert mock_redis.get(f"id-{pr_id}-custom-privacy-request-field-department") is None

    def test_has_cached_custom_fields_detects_both_formats(self, dsr_store, mock_redis, pr_id):
        """has_cached_custom_fields detects fields in both legacy and new formats."""
        # Empty initially
        assert dsr_store.has_cached_custom_fields(pr_id) is False

        # Add legacy key
        mock_redis.set(f"id-{pr_id}-custom-privacy-request-field-department", json.dumps("Engineering"))
        assert dsr_store.has_cached_custom_fields(pr_id) is True

        # Clear and test new format
        mock_redis._data.clear()
        dsr_store.write_custom_field(pr_id, "department", json.dumps("Engineering"))
        assert dsr_store.has_cached_custom_fields(pr_id) is True


class TestDSRCacheStoreEncryption:
    """Test encryption key cache operations in DSRCacheStore."""

    def test_write_encryption_writes_key(self, dsr_store, pr_id):
        """write_encryption writes encryption key to new-format key."""
        dsr_store.write_encryption(pr_id, "key", "test-encryption-key-12345", expire_seconds=3600)

        assert dsr_store._redis.get(f"dsr:{pr_id}:encryption:key") == "test-encryption-key-12345"
        
        # Legacy key does NOT exist
        assert dsr_store._redis.get(f"id-{pr_id}-encryption-key") is None

    def test_get_encryption_migrates_legacy_key(self, dsr_store, mock_redis, pr_id):
        """get_encryption reads and migrates legacy encryption keys."""
        # Write legacy format
        mock_redis.set(f"id-{pr_id}-encryption-key", "test-encryption-key-12345")

        # Read via store
        value = dsr_store.get_encryption(pr_id, "key")

        assert value == "test-encryption-key-12345"

        # Legacy key migrated
        assert mock_redis.get(f"dsr:{pr_id}:encryption:key") == "test-encryption-key-12345"
        assert mock_redis.get(f"id-{pr_id}-encryption-key") is None
