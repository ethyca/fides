"""
In-memory TTL cache for OAuth client details.

This module provides a simple cache for ClientDetail objects to reduce
database queries during authentication. Entries automatically expire
after a configurable TTL (time-to-live).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.models.client import ClientDetail
from fides.config import CONFIG, FidesConfig

# Maximum number of clients to cache to prevent unbounded memory growth
MAX_CACHE_SIZE = 1000


@dataclass
class CacheEntry:
    """A cached client with its expiration timestamp."""

    client: ClientDetail
    expires_at: datetime


class ClientCache:
    """
    TTL cache for ClientDetail objects.

    This cache stores ClientDetail objects keyed by client_id and automatically
    considers entries expired after the configured TTL. The cache has a maximum
    size limit to prevent unbounded memory growth.
    """

    def __init__(self, max_size: int = MAX_CACHE_SIZE):
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size

    def get(self, client_id: str) -> Optional[ClientDetail]:
        """
        Retrieve a client from the cache if it exists and hasn't expired.

        Args:
            client_id: The client ID to look up.

        Returns:
            The cached ClientDetail if found and not expired, None otherwise.
        """
        # Cache disabled
        if not self.is_enabled():
            return None

        entry = self._cache.get(client_id)
        if entry is None:
            return None

        # Check if entry has expired
        now = datetime.now()
        if now >= entry.expires_at:
            # Entry expired, remove it
            self._cache.pop(client_id, None)
            return None

        return entry.client

    def set(self, client_id: str, client: ClientDetail) -> None:
        """
        Store a client in the cache.

        If the cache is at maximum capacity, the oldest entries are evicted
        to make room for the new entry.

        Args:
            client_id: The client ID to use as the cache key.
            client: The ClientDetail object to cache.
        """
        ttl_seconds = CONFIG.security.oauth_client_cache_ttl_seconds

        # Cache disabled
        if ttl_seconds <= 0:
            return

        # Evict an entry if at capacity
        if len(self._cache) >= self._max_size and client_id not in self._cache:
            self._evict_one()

        expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
        self._cache[client_id] = CacheEntry(client=client, expires_at=expires_at)

    def delete(self, client_id: str) -> bool:
        """
        Remove a specific client from the cache.

        Args:
            client_id: The client ID to remove.

        Returns:
            True if the entry was removed, False if it wasn't in the cache.
        """
        removed = self._cache.pop(client_id, None)
        if removed is not None:
            logger.debug("Removed client_id={} from cache", client_id)
            return True
        return False

    def clear(self) -> int:
        """
        Clear all entries from the cache.

        Returns:
            The number of entries that were cleared.
        """
        count = len(self._cache)
        self._cache.clear()
        logger.debug("Cleared {} entries from client cache", count)
        return count

    def _evict_one(self) -> None:
        """Evict an arbitrary entry from the cache"""
        try:
            # Pop an arbitrary key
            self._cache.pop(next(iter(self._cache)))
        except (StopIteration, KeyError):
            # Cache is empty or was modified concurrently
            pass

    def size(self) -> int:
        """Return the current number of entries in the cache."""
        return len(self._cache)

    def is_enabled(self) -> bool:
        """Return True if caching is enabled (TTL > 0)."""
        return CONFIG.security.oauth_client_cache_ttl_seconds > 0


# Global cache instance
_client_cache = ClientCache()


def get_cached_client(
    db: Session,
    client_id: str,
    config: FidesConfig,
    scopes: list[str],
    roles: list[str],
) -> Optional[ClientDetail]:
    """
    Get a client from cache or database.

    This function first checks the cache for the client. If not found (or expired),
    it queries the database and caches the result.

    Note: Root client is not cached as it's already an in-memory object that
    doesn't require a database query.

    Args:
        db: Database session for querying if cache miss.
        client_id: The client ID to look up.
        config: Fides configuration object.
        scopes: Scopes to pass to ClientDetail.get (only used for root client).
        roles: Roles to pass to ClientDetail.get (only used for root client).

    Returns:
        The ClientDetail if found, None otherwise.
    """
    # Root client is always created in-memory, no caching needed
    if client_id == config.security.oauth_root_client_id:
        return ClientDetail.get(
            db,
            object_id=client_id,
            config=config,
            scopes=scopes,
            roles=roles,
        )

    # Try cache first
    cached_client = _client_cache.get(client_id)
    if cached_client is not None:
        return cached_client

    # Cache miss - query database
    client = ClientDetail.get(
        db,
        object_id=client_id,
        config=config,
        scopes=scopes,
        roles=roles,
    )

    # Cache the result if found
    if client is not None:
        _client_cache.set(client_id, client)

    return client


def clear_client_cache() -> int:
    """
    Clear all entries from the client cache.

    Returns:
        The number of entries that were cleared.
    """
    return _client_cache.clear()
