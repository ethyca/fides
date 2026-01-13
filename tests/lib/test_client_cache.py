"""Tests for the OAuth client cache functionality."""

from datetime import datetime, timedelta, timezone

import pytest

from fides.api.oauth.client_cache import (
    CacheEntry,
    ClientCache,
    _client_cache,
    clear_client_cache,
    get_cached_client,
)
from fides.common.api.scope_registry import SCOPE_REGISTRY


class TestClientCache:
    """Tests for the ClientCache class."""

    @pytest.fixture(scope="function")
    def cache_enabled(self, config):
        """Fixture to enable client cache with 300 second TTL."""
        original_value = config.security.oauth_client_cache_ttl_seconds
        config.security.oauth_client_cache_ttl_seconds = 300
        yield config
        config.security.oauth_client_cache_ttl_seconds = original_value

    @pytest.fixture(scope="function")
    def cache_disabled(self, config):
        """Fixture to disable client cache (TTL=0)."""
        original_value = config.security.oauth_client_cache_ttl_seconds
        config.security.oauth_client_cache_ttl_seconds = 0
        yield config
        config.security.oauth_client_cache_ttl_seconds = original_value

    @pytest.mark.usefixtures("cache_enabled")
    def test_cache_set_and_get(self, oauth_client):
        """Test basic cache set and get operations."""
        cache = ClientCache()

        # Cache should be empty initially
        assert cache.get(oauth_client.id) is None

        # Set the client in cache
        cache.set(oauth_client.id, oauth_client)

        # Should be able to retrieve it
        cached = cache.get(oauth_client.id)
        assert cached is not None
        assert cached.id == oauth_client.id

    @pytest.mark.usefixtures("cache_enabled")
    def test_cache_expiration(self, oauth_client):
        """Test that cache entries expire after TTL."""
        cache = ClientCache()

        # Create a cache entry that has already expired
        expired_time = datetime.now(timezone.utc) - timedelta(
            seconds=60
        )  # Expired 1 minute ago
        cache._cache[oauth_client.id] = CacheEntry(
            client=oauth_client, expires_at=expired_time
        )

        # Entry should be expired
        cached = cache.get(oauth_client.id)
        assert cached is None

        # Entry should have been removed from cache
        assert oauth_client.id not in cache._cache

    @pytest.mark.usefixtures("cache_enabled")
    def test_cache_not_expired(self, oauth_client):
        """Test that cache entries within TTL are returned."""
        cache = ClientCache()

        # Create a cache entry that expires in the future
        future_time = datetime.now(timezone.utc) + timedelta(
            seconds=300
        )  # Expires in 5 minutes
        cache._cache[oauth_client.id] = CacheEntry(
            client=oauth_client, expires_at=future_time
        )

        # Entry should still be valid
        cached = cache.get(oauth_client.id)
        assert cached is not None
        assert cached.id == oauth_client.id

    @pytest.mark.usefixtures("cache_disabled")
    def test_cache_disabled_when_ttl_zero(self, oauth_client):
        """Test that cache operations are no-ops when TTL is 0."""
        cache = ClientCache()

        # Set should do nothing
        cache.set(oauth_client.id, oauth_client)
        assert cache.size() == 0

        # Get should return None
        cached = cache.get(oauth_client.id)
        assert cached is None

    @pytest.mark.usefixtures("cache_enabled")
    def test_cache_delete(self, oauth_client):
        """Test deleting entries from cache."""
        cache = ClientCache()

        # Add entry to cache
        cache.set(oauth_client.id, oauth_client)
        assert cache.get(oauth_client.id) is not None

        # Delete the entry
        result = cache.delete(oauth_client.id)
        assert result is True

        # Entry should be gone
        assert cache.get(oauth_client.id) is None

        # Deleting non-existent entry returns False
        assert cache.delete("non-existent-id") is False

    @pytest.mark.usefixtures("cache_enabled")
    def test_cache_clear(self, oauth_client):
        """Test clearing all cache entries."""
        cache = ClientCache()

        # Add multiple entries
        cache.set(oauth_client.id, oauth_client)
        cache.set("another-id", oauth_client)
        assert cache.size() == 2

        # Clear the cache
        count = cache.clear()
        assert count == 2
        assert cache.size() == 0

    @pytest.mark.usefixtures("cache_enabled")
    def test_cache_eviction_at_max_size(self, oauth_client):
        """Test that an entry is evicted when cache is full."""
        cache = ClientCache(max_size=2)

        # Add two entries to fill the cache
        cache.set("client1", oauth_client)
        cache.set("client2", oauth_client)
        assert cache.size() == 2

        # Add third entry - should evict one of the existing entries
        cache.set("client3", oauth_client)

        # Cache should still be at max size
        assert cache.size() == 2
        # New entry should be present
        assert "client3" in cache._cache


class TestGetCachedClient:
    """Tests for the get_cached_client function."""

    @pytest.fixture(scope="function")
    def cache_enabled(self, config):
        """Fixture to enable client cache with 300 second TTL."""
        assert config.test_mode
        original_value = config.security.oauth_client_cache_ttl_seconds
        config.security.oauth_client_cache_ttl_seconds = 300
        yield config
        config.security.oauth_client_cache_ttl_seconds = original_value

    @pytest.fixture(scope="function")
    def cache_disabled(self, config):
        """Fixture to disable client cache (TTL=0)."""
        assert config.test_mode
        original_value = config.security.oauth_client_cache_ttl_seconds
        config.security.oauth_client_cache_ttl_seconds = 0
        yield config
        config.security.oauth_client_cache_ttl_seconds = original_value

    def test_cache_miss_queries_database(self, db, oauth_client, cache_enabled):
        """Test that a cache miss results in a database query."""
        # Clear the cache first
        clear_client_cache()

        client = get_cached_client(
            db=db,
            client_id=oauth_client.id,
            config=cache_enabled,
            scopes=SCOPE_REGISTRY,
            roles=[],
        )

        assert client is not None
        assert client.id == oauth_client.id

        # Client should now be in cache
        cached = _client_cache.get(oauth_client.id)
        assert cached is not None

    def test_cache_hit_returns_cached_client(self, db, oauth_client, cache_enabled):
        """Test that a cache hit returns the cached client."""
        clear_client_cache()

        # First call should query DB and cache
        client1 = get_cached_client(
            db=db,
            client_id=oauth_client.id,
            config=cache_enabled,
            scopes=SCOPE_REGISTRY,
            roles=[],
        )

        # Second call should return cached client
        client2 = get_cached_client(
            db=db,
            client_id=oauth_client.id,
            config=cache_enabled,
            scopes=SCOPE_REGISTRY,
            roles=[],
        )

        # Both should be the same object (cached)
        assert client1 is client2

    def test_root_client_not_cached(self, db, cache_enabled):
        """Test that root client is not cached (it's already in-memory)."""
        clear_client_cache()

        client = get_cached_client(
            db=db,
            client_id=cache_enabled.security.oauth_root_client_id,
            config=cache_enabled,
            scopes=SCOPE_REGISTRY,
            roles=[],
        )

        assert client is not None

        # Root client should NOT be in cache
        cached = _client_cache.get(cache_enabled.security.oauth_root_client_id)
        assert cached is None

    def test_nonexistent_client_returns_none(self, db, cache_enabled):
        """Test that looking up a non-existent client returns None."""
        clear_client_cache()

        client = get_cached_client(
            db=db,
            client_id="non-existent-client-id",
            config=cache_enabled,
            scopes=SCOPE_REGISTRY,
            roles=[],
        )

        assert client is None

    def test_cache_disabled_always_queries_db(self, db, oauth_client, cache_disabled):
        """Test that with cache disabled, every call queries the database."""
        clear_client_cache()

        client = get_cached_client(
            db=db,
            client_id=oauth_client.id,
            config=cache_disabled,
            scopes=SCOPE_REGISTRY,
            roles=[],
        )

        assert client is not None

        # Nothing should be cached
        assert _client_cache.size() == 0


class TestGlobalCacheFunctions:
    """Tests for the global cache helper functions."""

    @pytest.fixture(scope="function")
    def cache_enabled(self, config):
        """Fixture to enable client cache with 300 second TTL."""
        assert config.test_mode
        original_value = config.security.oauth_client_cache_ttl_seconds
        config.security.oauth_client_cache_ttl_seconds = 300
        yield config
        config.security.oauth_client_cache_ttl_seconds = original_value

    def test_clear_client_cache(self, db, oauth_client, cache_enabled):
        """Test the clear_client_cache helper function."""
        _client_cache.set(oauth_client.id, oauth_client)

        assert _client_cache.size() > 0

        count = clear_client_cache()
        assert count > 0
        assert _client_cache.size() == 0
