"""
Tests for DSRCacheStore DRP request body caching.

Focuses on service-layer methods for DRP data management, including:
- Writing DRP fields in new format
- Reading DRP fields from both new and legacy formats
- Automatic migration on read
"""

import pytest

from fides.common.cache.dsr_store import DSRCacheStore

# Mark all tests as unit tests
pytestmark = pytest.mark.unit

_TTL = 3600  # Test TTL


class TestDSRCacheStoreDRP:
    """Test DSRCacheStore DRP request body methods."""

    def test_cache_drp_request_body_writes_all_fields(self, manager, pr_id):
        """cache_drp_request_body writes all fields to new-format keys."""
        store = DSRCacheStore(pr_id, manager)
        drp_body = {
            "meta": "metadata_value",
            "regime": "gdpr",
            "exercise": "access",
            "identity": '{"email": "user@example.com"}',
        }

        store.cache_drp_request_body(drp_body, expire_seconds=3600)

        # Verify all fields written to new format
        assert store.get_drp("meta") == "metadata_value"
        assert store.get_drp("regime") == "gdpr"
        assert store.get_drp("exercise") == "access"
        assert store.get_drp("identity") == '{"email": "user@example.com"}'

    def test_cache_drp_request_body_skips_none_values(self, manager, pr_id):
        """cache_drp_request_body skips None values."""
        store = DSRCacheStore(pr_id, manager)
        drp_body = {
            "meta": "metadata_value",
            "regime": None,
            "exercise": "access",
        }

        store.cache_drp_request_body(drp_body, _TTL)

        # Only non-None fields should be written
        assert store.get_drp("meta") == "metadata_value"
        assert store.get_drp("regime") is None
        assert store.get_drp("exercise") == "access"

    def test_get_cached_drp_request_body_reads_all_fields(self, manager, pr_id):
        """get_cached_drp_request_body reads all fields from new-format keys."""
        store = DSRCacheStore(pr_id, manager)
        drp_body = {
            "meta": "metadata_value",
            "regime": "gdpr",
            "exercise": "access",
        }
        store.cache_drp_request_body(drp_body, _TTL)

        result = store.get_cached_drp_request_body()

        assert result == {
            "meta": "metadata_value",
            "regime": "gdpr",
            "exercise": "access",
        }

    def test_get_cached_drp_request_body_migrates_legacy_keys(
        self, manager, mock_redis, pr_id
    ):
        """get_cached_drp_request_body reads and migrates legacy keys on first access."""
        store = DSRCacheStore(pr_id, manager)
        # Write legacy format directly
        mock_redis.set(f"id-{pr_id}-drp-meta", "legacy_metadata")
        mock_redis.set(f"id-{pr_id}-drp-regime", "ccpa")

        result = store.get_cached_drp_request_body()

        assert result == {
            "meta": "legacy_metadata",
            "regime": "ccpa",
        }

        # Verify migration happened (new keys exist, legacy keys deleted)
        assert mock_redis.get(f"dsr:{pr_id}:drp:meta") == "legacy_metadata"
        assert mock_redis.get(f"dsr:{pr_id}:drp:regime") == "ccpa"
        assert mock_redis.get(f"id-{pr_id}-drp-meta") is None
        assert mock_redis.get(f"id-{pr_id}-drp-regime") is None

    def test_has_cached_drp_request_body_detects_both_formats(
        self, manager, mock_redis, pr_id
    ):
        """has_cached_drp_request_body detects DRP data in both legacy and new formats."""
        store = DSRCacheStore(pr_id, manager)
        # Empty initially
        assert store.has_cached_drp_request_body() is False

        # Write new format
        store.write_drp("meta", "metadata", _TTL)
        assert store.has_cached_drp_request_body() is True

        # Clear and test legacy format
        store.clear()
        assert store.has_cached_drp_request_body() is False

        mock_redis.set(f"id-{pr_id}-drp-regime", "gdpr")
        assert store.has_cached_drp_request_body() is True

    def test_get_cached_drp_request_body_returns_empty_dict_when_no_data(
        self, manager, pr_id
    ):
        """get_cached_drp_request_body returns empty dict when no DRP data cached."""
        store = DSRCacheStore(pr_id, manager)
        result = store.get_cached_drp_request_body()
        assert result == {}

    def test_drp_migration_then_new_writes(self, manager, mock_redis, pr_id):
        """After migrating legacy keys, new writes use indexed format."""
        store = DSRCacheStore(pr_id, manager)
        # Start with legacy keys
        mock_redis.set(f"id-{pr_id}-drp-meta", "legacy_metadata")

        # Read triggers migration
        result1 = store.get_cached_drp_request_body()
        assert result1["meta"] == "legacy_metadata"

        # Now write new fields - should use indexed format
        store.write_drp("regime", "gdpr", _TTL)
        store.write_drp("exercise", "access", _TTL)

        # Read all - should get both migrated and new
        result2 = store.get_cached_drp_request_body()
        assert result2["meta"] == "legacy_metadata"
        assert result2["regime"] == "gdpr"
        assert result2["exercise"] == "access"

        # Verify all keys are now indexed
        all_keys = store.get_all_keys()
        assert f"dsr:{pr_id}:drp:meta" in all_keys
        assert f"dsr:{pr_id}:drp:regime" in all_keys
        assert f"dsr:{pr_id}:drp:exercise" in all_keys
