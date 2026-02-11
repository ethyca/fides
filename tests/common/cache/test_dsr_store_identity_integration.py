"""
Tests for identity cache operations integration with DSRCacheStore.

Verifies cache_identity, get_cached_identity_data, and verify_cache_for_identity_data
work correctly with both legacy and new cache keys.
"""

import json
import uuid
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

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


@contextmanager
def patch_get_cache(mock_redis):
    """Context manager to patch get_cache with mock Redis."""
    with patch("fides.api.util.cache.get_cache", return_value=mock_redis):
        with patch("fides.api.util.cache.CONFIG.redis.default_ttl_seconds", 3600):
            yield


def create_mock_privacy_request(pr_id):
    """Create mock PrivacyRequest with given ID."""
    pr = MagicMock()
    pr.id = pr_id
    return pr


# Mark all tests as unit tests that don't require full test infrastructure
pytestmark = pytest.mark.unit


class TestIdentityCacheOperations:
    """Test identity cache operations with DSR store."""

    def test_cache_identity_writes_new_format_only(self, mock_redis, pr_id, identity_data):
        """cache_identity writes only new-format keys."""
        pr = create_mock_privacy_request(pr_id)

        with patch_get_cache(mock_redis):
            from fides.api.models.privacy_request.privacy_request import PrivacyRequest
            from fides.api.schemas.redis_cache import Identity

            identity = Identity(**identity_data)
            PrivacyRequest.cache_identity(pr, identity)

        # New keys exist
        assert mock_redis.get(f"dsr:{pr_id}:identity:email") is not None
        assert mock_redis.get(f"dsr:{pr_id}:identity:phone_number") is not None

        # Legacy keys do NOT exist
        assert mock_redis.get(f"id-{pr_id}-identity-email") is None
        assert mock_redis.get(f"id-{pr_id}-identity-phone_number") is None

    def test_store_cache_identity_data_service_method(self, dsr_store, pr_id):
        """DSRCacheStore.cache_identity_data writes all attributes."""
        identity_data = {
            "email": json.dumps("user@example.com"),
            "phone_number": json.dumps("+1234567890"),
        }

        dsr_store.cache_identity_data(pr_id, identity_data, expire_seconds=3600)

        # All keys written in new format
        assert dsr_store._redis.get(f"dsr:{pr_id}:identity:email") == json.dumps("user@example.com")
        assert dsr_store._redis.get(f"dsr:{pr_id}:identity:phone_number") == json.dumps("+1234567890")

    def test_get_cached_identity_data_reads_legacy_keys(self, mock_redis, pr_id, identity_data):
        """get_cached_identity_data reads legacy keys and migrates them."""
        # Write legacy format with JSON encoding
        for key, value in identity_data.items():
            mock_redis.set(f"id-{pr_id}-identity-{key}", json.dumps(value))

        pr = create_mock_privacy_request(pr_id)

        with patch_get_cache(mock_redis):
            from fides.api.models.privacy_request.privacy_request import PrivacyRequest

            result = PrivacyRequest.get_cached_identity_data(pr)

        # Values are returned correctly
        assert result["email"] == "user@example.com"
        assert result["phone_number"] == "+1234567890"

        # Legacy keys migrated to new format
        assert mock_redis.get(f"dsr:{pr_id}:identity:email") is not None
        assert mock_redis.get(f"id-{pr_id}-identity-email") is None

    def test_store_get_cached_identity_data_service_method(self, dsr_store, pr_id):
        """DSRCacheStore.get_cached_identity_data reads all attributes."""
        # Write some identity data
        identity_data = {
            "email": json.dumps("user@example.com"),
            "phone_number": json.dumps("+1234567890"),
        }
        dsr_store.cache_identity_data(pr_id, identity_data)

        # Read it back
        result = dsr_store.get_cached_identity_data(pr_id)

        assert result["email"] == json.dumps("user@example.com")
        assert result["phone_number"] == json.dumps("+1234567890")

    def test_get_cached_identity_data_reads_new_keys(self, dsr_store, mock_redis, pr_id, identity_data):
        """get_cached_identity_data reads new-format keys."""
        # Write via store
        for key, value in identity_data.items():
            dsr_store.write_identity(pr_id, key, json.dumps(value))

        pr = create_mock_privacy_request(pr_id)

        with patch_get_cache(mock_redis):
            from fides.api.models.privacy_request.privacy_request import PrivacyRequest

            result = PrivacyRequest.get_cached_identity_data(pr)

        assert result["email"] == "user@example.com"
        assert result["phone_number"] == "+1234567890"

    def test_verify_cache_for_identity_data_detects_legacy(self, mock_redis, pr_id):
        """verify_cache_for_identity_data returns True for legacy keys."""
        mock_redis.set(f"id-{pr_id}-identity-email", json.dumps("test@example.com"))

        pr = create_mock_privacy_request(pr_id)

        with patch_get_cache(mock_redis):
            from fides.api.models.privacy_request.privacy_request import PrivacyRequest

            has_cache = PrivacyRequest.verify_cache_for_identity_data(pr)

        assert has_cache is True

    def test_store_has_cached_identity_data_service_method(self, dsr_store, mock_redis, pr_id):
        """DSRCacheStore.has_cached_identity_data detects both formats."""
        # Empty initially
        assert dsr_store.has_cached_identity_data(pr_id) is False

        # Add legacy key
        mock_redis.set(f"id-{pr_id}-identity-email", json.dumps("test@example.com"))
        assert dsr_store.has_cached_identity_data(pr_id) is True

        # Clear and test new format
        mock_redis._data.clear()
        dsr_store.write_identity(pr_id, "email", json.dumps("test@example.com"))
        assert dsr_store.has_cached_identity_data(pr_id) is True

    def test_verify_cache_for_identity_data_detects_new(self, dsr_store, mock_redis, pr_id):
        """verify_cache_for_identity_data returns True for new keys."""
        dsr_store.write_identity(pr_id, "email", json.dumps("test@example.com"))

        pr = create_mock_privacy_request(pr_id)

        with patch_get_cache(mock_redis):
            from fides.api.models.privacy_request.privacy_request import PrivacyRequest

            has_cache = PrivacyRequest.verify_cache_for_identity_data(pr)

        assert has_cache is True

    def test_verify_cache_returns_false_when_empty(self, mock_redis, pr_id):
        """verify_cache_for_identity_data returns False when no cache exists."""
        pr = create_mock_privacy_request(pr_id)

        with patch_get_cache(mock_redis):
            from fides.api.models.privacy_request.privacy_request import PrivacyRequest

            has_cache = PrivacyRequest.verify_cache_for_identity_data(pr)

        assert has_cache is False


def _run_standalone_tests():
    """Run tests standalone."""
    # Create shared fixtures manually for standalone execution
    mock_redis = MockRedis()
    dsr_store = DSRCacheStore(RedisCacheManager(mock_redis))
    
    tests = TestIdentityCacheOperations()
    pr_id = f"test-pr-{uuid.uuid4()}"
    identity_data = {"email": "user@example.com", "phone_number": "+1234567890"}
    
    tests.test_cache_identity_writes_new_format_only(mock_redis, pr_id, identity_data)
    
    pr_id = f"test-pr-{uuid.uuid4()}"
    tests.test_store_cache_identity_data_service_method(dsr_store, pr_id)
    
    mock_redis = MockRedis()
    dsr_store = DSRCacheStore(RedisCacheManager(mock_redis))
    pr_id = f"test-pr-{uuid.uuid4()}"
    tests.test_get_cached_identity_data_reads_legacy_keys(mock_redis, pr_id, identity_data)
    
    pr_id = f"test-pr-{uuid.uuid4()}"
    tests.test_store_get_cached_identity_data_service_method(dsr_store, pr_id)
    
    mock_redis = MockRedis()
    dsr_store = DSRCacheStore(RedisCacheManager(mock_redis))
    pr_id = f"test-pr-{uuid.uuid4()}"
    tests.test_get_cached_identity_data_reads_new_keys(dsr_store, mock_redis, pr_id, identity_data)
    
    mock_redis = MockRedis()
    pr_id = f"test-pr-{uuid.uuid4()}"
    tests.test_verify_cache_for_identity_data_detects_legacy(mock_redis, pr_id)
    
    mock_redis = MockRedis()
    dsr_store = DSRCacheStore(RedisCacheManager(mock_redis))
    pr_id = f"test-pr-{uuid.uuid4()}"
    tests.test_store_has_cached_identity_data_service_method(dsr_store, mock_redis, pr_id)
    
    mock_redis = MockRedis()
    dsr_store = DSRCacheStore(RedisCacheManager(mock_redis))
    pr_id = f"test-pr-{uuid.uuid4()}"
    tests.test_verify_cache_for_identity_data_detects_new(dsr_store, mock_redis, pr_id)
    
    mock_redis = MockRedis()
    pr_id = f"test-pr-{uuid.uuid4()}"
    tests.test_verify_cache_returns_false_when_empty(mock_redis, pr_id)
    
    print("All identity cache integration tests passed.")


if __name__ == "__main__":
    _run_standalone_tests()
