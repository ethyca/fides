"""
Tests for DSRCacheStore DRP request body caching.

Focuses on service-layer methods for DRP data management, including:
- Writing DRP fields in new format
- Reading DRP fields from both new and legacy formats
- Automatic migration on read
"""

import pytest
import uuid
from typing import Dict, Any

from fides.common.cache.dsr_store import DSRCacheStore
from fides.common.cache.manager import RedisCacheManager
from tests.common.cache.mock_redis import MockRedis


@pytest.fixture
def mock_redis():
    """In-memory Redis mock for isolated testing."""
    return MockRedis()


@pytest.fixture
def dsr_store(mock_redis):
    """DSRCacheStore instance with mock Redis backend."""
    manager = RedisCacheManager(mock_redis)
    return DSRCacheStore(manager)


@pytest.fixture
def pr_id():
    """Generate unique privacy request ID for each test."""
    return f"test-pr-{uuid.uuid4()}"


class TestDSRCacheStoreDRP:
    """Test DSRCacheStore DRP request body methods."""

    def test_cache_drp_request_body_writes_all_fields(self, dsr_store, pr_id):
        """cache_drp_request_body writes all fields to new-format keys."""
        drp_body = {
            "meta": "metadata_value",
            "regime": "gdpr",
            "exercise": "access",
            "identity": '{"email": "user@example.com"}',
        }

        dsr_store.cache_drp_request_body(pr_id, drp_body, expire_seconds=3600)

        # Verify all fields written to new format
        assert dsr_store.get_drp(pr_id, "meta") == "metadata_value"
        assert dsr_store.get_drp(pr_id, "regime") == "gdpr"
        assert dsr_store.get_drp(pr_id, "exercise") == "access"
        assert dsr_store.get_drp(pr_id, "identity") == '{"email": "user@example.com"}'

    def test_cache_drp_request_body_skips_none_values(self, dsr_store, pr_id):
        """cache_drp_request_body skips None values."""
        drp_body = {
            "meta": "metadata_value",
            "regime": None,
            "exercise": "access",
        }

        dsr_store.cache_drp_request_body(pr_id, drp_body)

        # Only non-None fields should be written
        assert dsr_store.get_drp(pr_id, "meta") == "metadata_value"
        assert dsr_store.get_drp(pr_id, "regime") is None
        assert dsr_store.get_drp(pr_id, "exercise") == "access"

    def test_get_cached_drp_request_body_reads_all_fields(self, dsr_store, pr_id):
        """get_cached_drp_request_body reads all fields from new-format keys."""
        drp_body = {
            "meta": "metadata_value",
            "regime": "gdpr",
            "exercise": "access",
        }
        dsr_store.cache_drp_request_body(pr_id, drp_body)

        result = dsr_store.get_cached_drp_request_body(pr_id)

        assert result == {
            "meta": "metadata_value",
            "regime": "gdpr",
            "exercise": "access",
        }

    def test_get_cached_drp_request_body_migrates_legacy_keys(
        self, dsr_store, mock_redis, pr_id
    ):
        """get_cached_drp_request_body reads and migrates legacy keys on first access."""
        # Write legacy format directly
        mock_redis.set(f"id-{pr_id}-drp-meta", "legacy_metadata")
        mock_redis.set(f"id-{pr_id}-drp-regime", "ccpa")

        result = dsr_store.get_cached_drp_request_body(pr_id)

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
        self, dsr_store, mock_redis, pr_id
    ):
        """has_cached_drp_request_body detects DRP data in both legacy and new formats."""
        # Empty initially
        assert dsr_store.has_cached_drp_request_body(pr_id) is False

        # Write new format
        dsr_store.write_drp(pr_id, "meta", "metadata")
        assert dsr_store.has_cached_drp_request_body(pr_id) is True

        # Clear and test legacy format
        dsr_store.clear(pr_id)
        assert dsr_store.has_cached_drp_request_body(pr_id) is False

        mock_redis.set(f"id-{pr_id}-drp-regime", "gdpr")
        assert dsr_store.has_cached_drp_request_body(pr_id) is True

    def test_get_cached_drp_request_body_returns_empty_dict_when_no_data(
        self, dsr_store, pr_id
    ):
        """get_cached_drp_request_body returns empty dict when no DRP data cached."""
        result = dsr_store.get_cached_drp_request_body(pr_id)
        assert result == {}

    def test_drp_migration_then_new_writes(self, dsr_store, mock_redis, pr_id):
        """After migrating legacy keys, new writes use indexed format."""
        # Start with legacy keys
        mock_redis.set(f"id-{pr_id}-drp-meta", "legacy_metadata")

        # Read triggers migration
        result1 = dsr_store.get_cached_drp_request_body(pr_id)
        assert result1["meta"] == "legacy_metadata"

        # Now write new fields - should use indexed format
        dsr_store.write_drp(pr_id, "regime", "gdpr")
        dsr_store.write_drp(pr_id, "exercise", "access")

        # Read all - should get both migrated and new
        result2 = dsr_store.get_cached_drp_request_body(pr_id)
        assert result2["meta"] == "legacy_metadata"
        assert result2["regime"] == "gdpr"
        assert result2["exercise"] == "access"

        # Verify all keys are now indexed
        all_keys = dsr_store.get_all_keys(pr_id)
        assert f"dsr:{pr_id}:drp:meta" in all_keys
        assert f"dsr:{pr_id}:drp:regime" in all_keys
        assert f"dsr:{pr_id}:drp:exercise" in all_keys
