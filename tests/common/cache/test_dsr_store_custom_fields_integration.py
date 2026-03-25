"""
Tests for custom fields and encryption cache operations in DSRCacheStore.

Tests the service layer directly with MockRedis - no patching needed.
"""

import json

import pytest

from fides.common.cache.dsr_store import DSRCacheStore

# Mark all tests as unit tests
pytestmark = pytest.mark.unit

_TTL = 3600  # Test TTL


class TestDSRCacheStoreCustomFields:
    """Test custom fields cache operations in DSRCacheStore."""

    def test_cache_custom_fields_writes_all_fields(self, manager, mock_redis, pr_id):
        """cache_custom_fields writes all fields to new-format keys."""
        store = DSRCacheStore(pr_id, manager)
        custom_fields = {
            "department": json.dumps("Engineering"),
            "employee_id": json.dumps("E12345"),
        }

        store.cache_custom_fields(custom_fields, expire_seconds=3600)

        # All keys written in new format
        assert mock_redis.get(f"dsr:{pr_id}:custom_field:department") == json.dumps(
            "Engineering"
        )
        assert mock_redis.get(f"dsr:{pr_id}:custom_field:employee_id") == json.dumps(
            "E12345"
        )

        # Legacy keys do NOT exist
        assert (
            mock_redis.get(f"id-{pr_id}-custom-privacy-request-field-department")
            is None
        )

    def test_get_cached_custom_fields_reads_all_fields(self, manager, pr_id):
        """get_cached_custom_fields reads all fields from new-format keys."""
        store = DSRCacheStore(pr_id, manager)
        custom_fields = {
            "department": json.dumps("Engineering"),
            "employee_id": json.dumps("E12345"),
        }
        store.cache_custom_fields(custom_fields, _TTL)

        result = store.get_cached_custom_fields()

        assert result["department"] == json.dumps("Engineering")
        assert result["employee_id"] == json.dumps("E12345")

    def test_get_cached_custom_fields_migrates_legacy_keys(
        self, manager, mock_redis, pr_id
    ):
        """get_cached_custom_fields reads and migrates legacy keys on first access."""
        store = DSRCacheStore(pr_id, manager)
        # Write legacy format
        mock_redis.set(
            f"id-{pr_id}-custom-privacy-request-field-department",
            json.dumps("Engineering"),
        )
        mock_redis.set(
            f"id-{pr_id}-custom-privacy-request-field-employee_id", json.dumps("E12345")
        )

        result = store.get_cached_custom_fields()

        # Values are returned correctly
        assert result["department"] == json.dumps("Engineering")
        assert result["employee_id"] == json.dumps("E12345")

        # Legacy keys migrated to new format
        assert mock_redis.get(f"dsr:{pr_id}:custom_field:department") is not None
        assert (
            mock_redis.get(f"id-{pr_id}-custom-privacy-request-field-department")
            is None
        )

    def test_has_cached_custom_fields_detects_both_formats(
        self, manager, mock_redis, pr_id
    ):
        """has_cached_custom_fields detects fields in both legacy and new formats."""
        store = DSRCacheStore(pr_id, manager)
        # Empty initially
        assert store.has_cached_custom_fields() is False

        # Add legacy key
        mock_redis.set(
            f"id-{pr_id}-custom-privacy-request-field-department",
            json.dumps("Engineering"),
        )
        assert store.has_cached_custom_fields() is True

        # Clear and test new format
        store.clear()
        store.write_custom_field("department", json.dumps("Engineering"), _TTL)
        assert store.has_cached_custom_fields() is True


class TestDSRCacheStoreEncryption:
    """Test encryption key cache operations in DSRCacheStore."""

    def test_write_encryption_writes_key(self, manager, mock_redis, pr_id):
        """write_encryption writes encryption key to new-format key."""
        store = DSRCacheStore(pr_id, manager)
        store.write_encryption("key", "test-encryption-key-12345", expire_seconds=3600)

        assert (
            mock_redis.get(f"dsr:{pr_id}:encryption:key") == "test-encryption-key-12345"
        )

        # Legacy key does NOT exist
        assert mock_redis.get(f"id-{pr_id}-encryption-key") is None

    def test_get_encryption_migrates_legacy_key(self, manager, mock_redis, pr_id):
        """get_encryption reads and migrates legacy encryption keys."""
        store = DSRCacheStore(pr_id, manager)
        # Write legacy format
        mock_redis.set(f"id-{pr_id}-encryption-key", "test-encryption-key-12345")

        # Read via store
        value = store.get_encryption("key")

        assert value == "test-encryption-key-12345"

        # Legacy key migrated
        assert (
            mock_redis.get(f"dsr:{pr_id}:encryption:key") == "test-encryption-key-12345"
        )
        assert mock_redis.get(f"id-{pr_id}-encryption-key") is None
