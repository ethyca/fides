"""
Tests for privacy_request.clear_cached_values() integration with DSRCacheStore.

Verifies that clearing uses the store and handles both legacy and new cache keys.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest

from fides.api.models.privacy_request.privacy_request import PrivacyRequest
from fides.common.cache.dsr_store import DSRCacheStore
from fides.common.cache.manager import RedisCacheManager
from tests.common.cache.mock_redis import create_mock_redis

_TTL = 3600  # Test TTL


@pytest.mark.unit
class TestPrivacyRequestClearCachedValues:
    """Test clear_cached_values() with DSR store."""

    def test_clear_removes_legacy_keys(self):
        """clear_cached_values removes legacy cache keys."""
        mock_redis = create_mock_redis()
        pr_id = f"test-pr-{uuid.uuid4()}"

        # Simulate legacy cached data
        mock_redis.set(f"id-{pr_id}-identity-email", "test@example.com")
        mock_redis.set(f"id-{pr_id}-identity-phone_number", "+1234567890")
        mock_redis.set(f"id-{pr_id}-encryption-key", "encryption-key")

        # Mock privacy request
        pr = MagicMock()
        pr.id = pr_id

        # Patch get_cache in the api.util.cache module where get_dsr_cache_store calls it
        with patch("fides.api.util.cache.get_cache", return_value=mock_redis):
            # Import here to avoid app initialization
            PrivacyRequest.clear_cached_values(pr)

        # Verify all keys deleted
        assert len(mock_redis.keys(f"*{pr_id}*")) == 0

    def test_clear_removes_new_keys(self):
        """clear_cached_values removes new-format cache keys."""
        mock_redis = create_mock_redis()
        pr_id = f"test-pr-{uuid.uuid4()}"

        # Simulate new cached data via store
        manager = RedisCacheManager(mock_redis)
        store = DSRCacheStore(pr_id, manager)
        store.write_identity("email", "test@example.com", _TTL)
        store.write_encryption("key", "encryption-key", _TTL)

        pr = MagicMock()
        pr.id = pr_id

        with patch("fides.api.util.cache.get_cache", return_value=mock_redis):
            PrivacyRequest.clear_cached_values(pr)

        assert len(mock_redis.keys(f"*{pr_id}*")) == 0

    def test_clear_removes_mixed_keys(self):
        """clear_cached_values removes both legacy and new keys."""
        mock_redis = create_mock_redis()
        pr_id = f"test-pr-{uuid.uuid4()}"

        # Mixed: legacy identity, new encryption
        mock_redis.set(f"id-{pr_id}-identity-email", "legacy@example.com")
        mock_redis.set(f"id-{pr_id}-custom-privacy-request-field-dept", "Engineering")

        manager = RedisCacheManager(mock_redis)
        store = DSRCacheStore(pr_id, manager)
        store.write_encryption("key", "new-encryption-key", _TTL)
        store.write_async_execution("task-123", _TTL)

        pr = MagicMock()
        pr.id = pr_id

        with patch("fides.api.util.cache.get_cache", return_value=mock_redis):
            PrivacyRequest.clear_cached_values(pr)

        assert len(mock_redis.keys(f"*{pr_id}*")) == 0

    def test_clear_removes_index(self):
        """clear_cached_values removes the DSR index."""
        mock_redis = create_mock_redis()
        pr_id = f"test-pr-{uuid.uuid4()}"

        manager = RedisCacheManager(mock_redis)
        store = DSRCacheStore(pr_id, manager)
        store.write_identity("email", "test@example.com", _TTL)

        # Verify index exists
        assert len(mock_redis.smembers(f"__idx:dsr:{pr_id}")) > 0

        pr = MagicMock()
        pr.id = pr_id

        with patch("fides.api.util.cache.get_cache", return_value=mock_redis):
            PrivacyRequest.clear_cached_values(pr)

        # Index should be deleted
        assert len(mock_redis.smembers(f"__idx:dsr:{pr_id}")) == 0
