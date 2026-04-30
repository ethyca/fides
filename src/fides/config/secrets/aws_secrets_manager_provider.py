"""AWS Secrets Manager provider with caching, stale-while-revalidate,
thundering-herd protection, and circuit breaker."""

import json
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, Optional

import boto3
from loguru import logger as log

from fides.config.secrets.base import SecretProvider, SecretProviderError, SecretValue


@dataclass
class _CacheEntry:
    """Per-secret cache state."""

    value: Optional[SecretValue]
    fetched_at: float
    last_failed_at: float = 0.0
    lock: threading.Lock = field(default_factory=threading.Lock)


class AWSSecretsManagerProvider(SecretProvider):
    """Fetches secrets from AWS Secrets Manager with local caching.

    Features:
    - TTL-based cache with stale-while-revalidate fallback
    - Per-secret locking for thundering-herd protection
    - Circuit breaker to prevent retry amplification on bad credentials
    """

    def __init__(
        self,
        region_name: str,
        cache_ttl_seconds: float = 300.0,
        cache_stale_ttl_seconds: float = 1800.0,
        circuit_breaker_cooldown_seconds: float = 30.0,
        endpoint_url: Optional[str] = None,
    ) -> None:
        self._cache_ttl = cache_ttl_seconds
        self._cache_stale_ttl = cache_stale_ttl_seconds
        self._circuit_breaker_cooldown = circuit_breaker_cooldown_seconds

        session = boto3.Session(region_name=region_name)
        self._client = session.client(
            "secretsmanager",
            endpoint_url=endpoint_url,
        )

        self._cache: Dict[str, _CacheEntry] = {}
        self._cache_lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def get_secret(self, secret_id: str) -> SecretValue:
        entry = self._get_or_create_entry(secret_id)

        now = time.monotonic()
        if entry.fetched_at > 0 and (now - entry.fetched_at) < self._cache_ttl:
            return entry.value

        # Snapshot fetched_at before acquiring the lock — if another thread
        # refreshes while we wait, we'll see the change and skip re-fetching.
        observed_fetched_at = entry.fetched_at

        # Cache miss or expired — acquire per-secret lock
        with entry.lock:
            # Another thread refreshed while we were waiting for the lock
            if entry.fetched_at != observed_fetched_at:
                return entry.value

            # Re-check TTL (covers the case where we didn't wait long)
            now = time.monotonic()
            if entry.fetched_at > 0 and (now - entry.fetched_at) < self._cache_ttl:
                return entry.value

            # Circuit breaker: if we recently failed, serve cached value
            # rather than hitting Secrets Manager again
            if (
                entry.last_failed_at > 0
                and (now - entry.last_failed_at) < self._circuit_breaker_cooldown
                and entry.value is not None
            ):
                return entry.value

            return self._fetch_and_update(secret_id, entry)

    def invalidate(self, secret_id: str) -> None:
        with self._cache_lock:
            entry = self._cache.get(secret_id)

        if entry is None:
            return

        with entry.lock:
            now = time.monotonic()
            if (
                entry.last_failed_at > 0
                and (now - entry.last_failed_at) < self._circuit_breaker_cooldown
            ):
                log.debug(
                    "Circuit breaker active for {!r}, skipping invalidation",
                    secret_id,
                )
                return

            entry.fetched_at = 0.0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_or_create_entry(self, secret_id: str) -> _CacheEntry:
        with self._cache_lock:
            entry = self._cache.get(secret_id)
            if entry is None:
                # Placeholder entry — fetched_at=0 forces a fetch on first access
                entry = _CacheEntry(
                    value=None,
                    fetched_at=0.0,
                )
                self._cache[secret_id] = entry
            return entry

    def _fetch_and_update(self, secret_id: str, entry: _CacheEntry) -> SecretValue:
        """Fetch from Secrets Manager, update cache, handle failures."""
        try:
            new_value = self._fetch(secret_id)
        except Exception as exc:
            return self._handle_fetch_failure(secret_id, entry, exc)

        entry.value = new_value
        entry.fetched_at = time.monotonic()
        entry.last_failed_at = 0.0
        return new_value

    def _fetch(self, secret_id: str) -> SecretValue:
        """Call AWS Secrets Manager and parse the response."""
        response = self._client.get_secret_value(
            SecretId=secret_id,
            VersionStage="AWSCURRENT",
        )
        secret_string = response["SecretString"]
        try:
            data = json.loads(secret_string)
        except json.JSONDecodeError as exc:
            # Don't chain the original exception — its .doc attribute
            # contains the raw secret string, which could leak credentials
            # if the exception is logged or inspected upstream.
            raise SecretProviderError(
                f"Secret {secret_id!r} is not valid JSON "
                f"(parse error at line {exc.lineno}, column {exc.colno})"
            ) from None
        return SecretValue(data)

    def _handle_fetch_failure(
        self, secret_id: str, entry: _CacheEntry, exc: Exception
    ) -> SecretValue:
        """Serve stale value if within grace period, otherwise raise."""
        entry.last_failed_at = time.monotonic()

        has_cached_value = entry.value is not None
        if not has_cached_value:
            raise SecretProviderError(
                f"Failed to fetch secret {secret_id!r} and no cached value available"
            ) from exc

        now = time.monotonic()
        # fetched_at may be 0 if invalidated — use the stale window from
        # the original fetch time. If fetched_at is 0 but we have a value,
        # we lost the original timestamp; serve stale and let TTL sort it out.
        age = now - entry.fetched_at if entry.fetched_at > 0 else self._cache_stale_ttl
        if age < self._cache_ttl + self._cache_stale_ttl:
            log.warning(
                "Failed to refresh secret {!r}, serving stale value: {}",
                secret_id,
                exc,
            )
            return entry.value

        raise SecretProviderError(
            f"Failed to fetch secret {secret_id!r} and stale cache has expired"
        ) from exc
