"""
Tests for privacy_request.clear_cached_values() integration with DSRCacheStore.

Verifies that clearing uses the store and handles both legacy and new cache keys.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest

from fides.common.cache.dsr_store import DSRCacheStore
from fides.common.cache.manager import RedisCacheManager


class MockRedis:
    """Minimal mock Redis for testing clear behavior."""

    def __init__(self):
        self._data = {}
        self._sets = {}

    def set(self, key, value, ex=None):
        self._data[key] = value
        return True

    def get(self, key):
        return self._data.get(key)

    def delete(self, *keys):
        return sum(1 for k in keys if self._data.pop(k, None) or self._sets.pop(k, None))

    def keys(self, pattern):
        import fnmatch
        return [k for k in self._data if fnmatch.fnmatch(k, pattern)]

    def scan_iter(self, match="*", count=None):
        return iter(self.keys(match))

    def sadd(self, key, *members):
        s = self._sets.setdefault(key, set())
        before = len(s)
        s.update(members)
        return len(s) - before

    def srem(self, key, *members):
        if key not in self._sets:
            return 0
        before = len(self._sets[key])
        self._sets[key].difference_update(members)
        return before - len(self._sets[key])

    def smembers(self, key):
        return self._sets.get(key, set()).copy()


@pytest.mark.unit
class TestPrivacyRequestClearCachedValues:
    """Test clear_cached_values() with DSR store."""

    def test_clear_removes_legacy_keys(self):
        """clear_cached_values removes legacy cache keys."""
        mock_redis = MockRedis()
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
            from fides.api.models.privacy_request.privacy_request import PrivacyRequest
            
            PrivacyRequest.clear_cached_values(pr)

        # Verify all keys deleted
        assert len(mock_redis.keys(f"*{pr_id}*")) == 0

    def test_clear_removes_new_keys(self):
        """clear_cached_values removes new-format cache keys."""
        mock_redis = MockRedis()
        pr_id = f"test-pr-{uuid.uuid4()}"
        
        # Simulate new cached data via store
        manager = RedisCacheManager(mock_redis)
        store = DSRCacheStore(manager)
        store.write_identity(pr_id, "email", "test@example.com")
        store.write_encryption(pr_id, "key", "encryption-key")

        pr = MagicMock()
        pr.id = pr_id

        with patch("fides.api.util.cache.get_cache", return_value=mock_redis):
            from fides.api.models.privacy_request.privacy_request import PrivacyRequest
            
            PrivacyRequest.clear_cached_values(pr)

        assert len(mock_redis.keys(f"*{pr_id}*")) == 0

    def test_clear_removes_mixed_keys(self):
        """clear_cached_values removes both legacy and new keys."""
        mock_redis = MockRedis()
        pr_id = f"test-pr-{uuid.uuid4()}"

        # Mixed: legacy identity, new encryption
        mock_redis.set(f"id-{pr_id}-identity-email", "legacy@example.com")
        mock_redis.set(f"id-{pr_id}-custom-privacy-request-field-dept", "Engineering")
        
        manager = RedisCacheManager(mock_redis)
        store = DSRCacheStore(manager)
        store.write_encryption(pr_id, "key", "new-encryption-key")
        store.write_async_execution(pr_id, "task-123")

        pr = MagicMock()
        pr.id = pr_id

        with patch("fides.api.util.cache.get_cache", return_value=mock_redis):
            from fides.api.models.privacy_request.privacy_request import PrivacyRequest
            
            PrivacyRequest.clear_cached_values(pr)

        assert len(mock_redis.keys(f"*{pr_id}*")) == 0

    def test_clear_removes_index(self):
        """clear_cached_values removes the DSR index."""
        mock_redis = MockRedis()
        pr_id = f"test-pr-{uuid.uuid4()}"

        manager = RedisCacheManager(mock_redis)
        store = DSRCacheStore(manager)
        store.write_identity(pr_id, "email", "test@example.com")
        
        # Verify index exists
        assert len(mock_redis.smembers(f"__idx:dsr:{pr_id}")) > 0

        pr = MagicMock()
        pr.id = pr_id

        with patch("fides.api.util.cache.get_cache", return_value=mock_redis):
            from fides.api.models.privacy_request.privacy_request import PrivacyRequest
            
            PrivacyRequest.clear_cached_values(pr)

        # Index should be deleted
        assert len(mock_redis.smembers(f"__idx:dsr:{pr_id}")) == 0

