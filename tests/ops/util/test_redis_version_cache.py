"""Tests for fides.api.util.redis_version_cache.

Covers:
- Cache miss behavior (first call, after clear, after version change)
- Cache hit behavior (unchanged Redis version)
- Invalidation via version change
- Manual cache_clear() forcing reload
- bump_version() incrementing Redis and clearing local cache
- Graceful fallback when Redis is unavailable
"""

from unittest.mock import MagicMock, patch

import pytest

from fides.api.util.redis_version_cache import _cache_store, redis_version_cached

CACHE_KEY = "test_cache"
REDIS_KEY = "test_redis_key"


@pytest.fixture(autouse=True)
def clear_cache():
    """Ensure each test starts with a clean cache and cleans up after."""
    _cache_store.pop(CACHE_KEY, None)
    yield
    _cache_store.pop(CACHE_KEY, None)


@pytest.fixture
def mock_get_redis_version():
    """Patch _get_redis_version so no real Redis connection is needed."""
    with patch("fides.api.util.redis_version_cache._get_redis_version") as mock:
        yield mock


@pytest.fixture
def mock_bump_redis_version():
    """Patch _bump_redis_version so no real Redis connection is needed."""
    with patch("fides.api.util.redis_version_cache._bump_redis_version") as mock:
        yield mock


class TestCacheMissBehavior:
    """First call or stale cache should invoke the decorated function."""

    def test_first_call_invokes_function_and_caches_result(
        self, mock_get_redis_version
    ):
        """On a cold cache the decorated function must be called and its
        return value cached."""
        mock_get_redis_version.return_value = "1"

        inner = MagicMock(return_value={"a": 1})

        decorated = redis_version_cached(redis_key=REDIS_KEY, cache_key=CACHE_KEY)(
            inner
        )
        result = decorated()

        assert result == {"a": 1}
        inner.assert_called_once()

    def test_function_return_value_is_preserved_exactly(self, mock_get_redis_version):
        """The decorator must not alter the return value."""
        mock_get_redis_version.return_value = None
        expected = [{"key": "val"}, 42, None]

        decorated = redis_version_cached(redis_key=REDIS_KEY, cache_key=CACHE_KEY)(
            lambda: expected
        )

        assert decorated() is expected

    def test_redis_key_none_treated_as_valid_version(self, mock_get_redis_version):
        """When the Redis key does not exist (returns None), the decorator
        should still cache with version=None and return cached on the next
        call with the same version."""
        mock_get_redis_version.return_value = None

        call_count = 0

        def counting_fn():
            nonlocal call_count
            call_count += 1
            return {"data": call_count}

        decorated = redis_version_cached(redis_key=REDIS_KEY, cache_key=CACHE_KEY)(
            counting_fn
        )

        first = decorated()
        second = decorated()

        assert first == {"data": 1}
        assert second == {"data": 1}
        assert call_count == 1


class TestCacheHitBehavior:
    """When Redis version is unchanged the cached value is returned without
    re-calling the function."""

    def test_second_call_returns_cached_value_without_calling_function(
        self, mock_get_redis_version
    ):
        mock_get_redis_version.return_value = "5"

        call_count = 0

        def counting_fn():
            nonlocal call_count
            call_count += 1
            return {"data": call_count}

        decorated = redis_version_cached(redis_key=REDIS_KEY, cache_key=CACHE_KEY)(
            counting_fn
        )

        first = decorated()
        second = decorated()

        assert first == {"data": 1}
        assert second == {"data": 1}  # same cached value
        assert call_count == 1  # function only called once


class TestInvalidationByVersionChange:
    """A change in the Redis version counter must trigger a reload."""

    def test_version_change_triggers_reload(self, mock_get_redis_version):
        call_count = 0

        def counting_fn():
            nonlocal call_count
            call_count += 1
            return f"version_{call_count}"

        decorated = redis_version_cached(redis_key=REDIS_KEY, cache_key=CACHE_KEY)(
            counting_fn
        )

        # First call: version "1"
        mock_get_redis_version.return_value = "1"
        assert decorated() == "version_1"

        # Second call: version changed to "2"
        mock_get_redis_version.return_value = "2"
        assert decorated() == "version_2"
        assert call_count == 2

    def test_version_change_from_none_to_value(self, mock_get_redis_version):
        """When the Redis key transitions from non-existent (None) to having
        a value, the cache must be invalidated."""
        call_count = 0

        def counting_fn():
            nonlocal call_count
            call_count += 1
            return call_count

        decorated = redis_version_cached(redis_key=REDIS_KEY, cache_key=CACHE_KEY)(
            counting_fn
        )

        # Key doesn't exist yet
        mock_get_redis_version.return_value = None
        assert decorated() == 1

        # Key now has a value (first bump_version)
        mock_get_redis_version.return_value = "1"
        assert decorated() == 2
        assert call_count == 2


class TestCacheClear:
    """Manual cache_clear() must force a reload on the next call."""

    def test_cache_clear_forces_reload(self, mock_get_redis_version):
        mock_get_redis_version.return_value = "1"

        call_count = 0

        def counting_fn():
            nonlocal call_count
            call_count += 1
            return call_count

        decorated = redis_version_cached(redis_key=REDIS_KEY, cache_key=CACHE_KEY)(
            counting_fn
        )

        assert decorated() == 1
        assert call_count == 1

        # Redis version unchanged, but we manually clear local cache
        decorated.cache_clear()

        assert decorated() == 2
        assert call_count == 2

    def test_cache_clear_is_idempotent(self, mock_get_redis_version):
        """Calling cache_clear() when the cache is already empty should not
        raise an error."""
        decorated = redis_version_cached(redis_key=REDIS_KEY, cache_key=CACHE_KEY)(
            lambda: None
        )

        # Clear on empty cache — should be a no-op
        decorated.cache_clear()
        decorated.cache_clear()


class TestBumpVersion:
    """bump_version() should increment Redis and clear the local cache."""

    def test_bump_version_increments_redis_and_clears_local_cache(
        self, mock_get_redis_version, mock_bump_redis_version
    ):
        mock_get_redis_version.return_value = "1"

        call_count = 0

        def counting_fn():
            nonlocal call_count
            call_count += 1
            return call_count

        decorated = redis_version_cached(redis_key=REDIS_KEY, cache_key=CACHE_KEY)(
            counting_fn
        )

        # Populate cache
        assert decorated() == 1
        assert call_count == 1

        # Bump version
        decorated.bump_version()

        # Verify Redis INCR was called
        mock_bump_redis_version.assert_called_once_with(REDIS_KEY)

        # Local cache was cleared, so next call is a miss
        mock_get_redis_version.return_value = "2"
        assert decorated() == 2
        assert call_count == 2

    def test_bump_version_handles_redis_failure_gracefully(
        self, mock_get_redis_version, mock_bump_redis_version
    ):
        """If Redis is unavailable during bump_version(), the local cache
        should still be cleared (best effort)."""
        mock_get_redis_version.return_value = "1"
        mock_bump_redis_version.side_effect = Exception("Redis down")

        call_count = 0

        def counting_fn():
            nonlocal call_count
            call_count += 1
            return call_count

        decorated = redis_version_cached(redis_key=REDIS_KEY, cache_key=CACHE_KEY)(
            counting_fn
        )

        # Populate cache
        assert decorated() == 1

        # Bump version fails on Redis but still clears local cache
        decorated.bump_version()

        # Local cache was cleared, so next call reloads
        assert decorated() == 2
        assert call_count == 2


class TestRedisUnavailable:
    """When Redis is unreachable the decorator should return stale cached
    data if available, or call the function directly as a last resort."""

    def test_redis_unavailable_with_no_cache_calls_function(
        self, mock_get_redis_version
    ):
        """If Redis is down and no cached value exists (cold start),
        the underlying function is called directly."""
        mock_get_redis_version.side_effect = Exception("Redis down")

        call_count = 0

        def counting_fn():
            nonlocal call_count
            call_count += 1
            return call_count

        decorated = redis_version_cached(redis_key=REDIS_KEY, cache_key=CACHE_KEY)(
            counting_fn
        )

        # No cached value, so function is called each time
        assert decorated() == 1
        assert decorated() == 2
        assert call_count == 2

    def test_redis_unavailable_with_stale_cache_returns_stale_value(
        self, mock_get_redis_version
    ):
        """If Redis goes down after the cache was populated, the stale
        cached value should be returned without calling the function."""
        call_count = 0

        def counting_fn():
            nonlocal call_count
            call_count += 1
            return call_count

        decorated = redis_version_cached(redis_key=REDIS_KEY, cache_key=CACHE_KEY)(
            counting_fn
        )

        # Populate cache while Redis is healthy
        mock_get_redis_version.return_value = "1"
        assert decorated() == 1
        assert call_count == 1

        # Redis goes down — stale cached value is returned
        mock_get_redis_version.side_effect = Exception("Redis down")
        assert decorated() == 1  # stale value, not 2
        assert decorated() == 1  # still stale
        assert call_count == 1  # function was never called again

    def test_redis_recovery_restores_caching(self, mock_get_redis_version):
        """After Redis recovers, caching should resume normally."""
        call_count = 0

        def counting_fn():
            nonlocal call_count
            call_count += 1
            return call_count

        decorated = redis_version_cached(redis_key=REDIS_KEY, cache_key=CACHE_KEY)(
            counting_fn
        )

        # Populate cache while Redis is healthy
        mock_get_redis_version.return_value = "1"
        assert decorated() == 1

        # Redis goes down — returns stale value
        mock_get_redis_version.side_effect = Exception("Redis down")
        assert decorated() == 1  # stale

        # Redis recovers with a new version
        mock_get_redis_version.side_effect = None
        mock_get_redis_version.return_value = "2"
        assert decorated() == 2  # cache miss (version changed)
        assert decorated() == 2  # cache hit
        assert call_count == 2
