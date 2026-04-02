"""
DSR cache store: single place for all DSR (privacy request) cache access.

Enforces:
- Key naming: dsr:{dsr_id}:{part} for every key (part = field_type:field_key)
- Index: one set per DSR (__idx:dsr:{dsr_id}) listing all keys for that DSR
- Legacy: each field type has a legacy key format; reads try new key then legacy,
  and can lazily migrate (copy legacy -> new, delete legacy) on first read.

Hash alternative (future): Using a single Redis HASH per DSR (key=dsr:{id},
fields=part names) would give one key per DSR, no index, and atomic HSET/HGET
per field so concurrent writers don't touch an index. Tradeoff: one TTL for the
whole DSR and a different storage shape; can introduce a hash-backed backend
later if we want to avoid index consistency concerns.
"""

from typing import Any, Callable, Dict, Optional, Union

from redis import Redis

from fides.common.cache.key_mapping import DSR_KEY_PREFIX, KeyMapper
from fides.common.cache.manager import RedisCacheManager, RedisValue

__all__ = ["DSR_KEY_PREFIX", "DSRCacheStore"]


def _dsr_key(dsr_id: str, part: str) -> str:
    """Build the Redis key for a DSR cache part."""
    return f"{DSR_KEY_PREFIX}{dsr_id}:{part}"


def _dsr_index_prefix(dsr_id: str) -> str:
    """Index prefix for this DSR; index set is __idx:dsr:{dsr_id}."""
    return f"{DSR_KEY_PREFIX}{dsr_id}"


class DSRCacheStore:
    """
    Cache store for DSR (privacy request) data with enforced naming and indexing.

    All keys are stored as dsr:{dsr_id}:{part}. Every write is registered in
    an index set so listing and clearing by DSR is O(index size) without KEYS/SCAN.
    Convenience methods (write_custom_field, get_custom_field, etc.) map to part
    names and support lazy migration from legacy key formats on read.
    """

    def __init__(
        self,
        dsr_id: str,
        cache_manager: RedisCacheManager,
        *,
        default_ttl_seconds: int = 3600,
        backfill_index_on_legacy_read: bool = True,
        migrate_legacy_on_read: bool = True,
    ) -> None:
        """
        Args:
            dsr_id: The privacy request ID this store is scoped to.
            cache_manager: RedisCacheManager (e.g. from get_redis_cache_manager()).
            default_ttl_seconds: Fallback TTL for migrated keys when the legacy
                key has no expiration. Default 3600s (1 hour).
            backfill_index_on_legacy_read: When listing keys and we fall back to
                KEYS for legacy keys, add those keys to the index. Default True.
            migrate_legacy_on_read: When a get finds value in legacy key only,
                write to new key, delete legacy key, add new key to index.
                Default True.
        """
        self._dsr_id = dsr_id
        self._manager = cache_manager
        self._redis: Redis = cache_manager.redis
        self._default_ttl = default_ttl_seconds
        self._backfill = backfill_index_on_legacy_read
        self._migrate_on_read = migrate_legacy_on_read

    def write(
        self,
        field_type: str,
        field_key: str,
        value: RedisValue,
        expire_seconds: int,
    ) -> Optional[bool]:
        """
        Low-level write: set dsr:{dsr_id}:{field_type}:{field_key} and add to index.
        Prefer convenience methods (write_custom_field, etc.) so legacy mapping
        stays in one place.
        """
        part = f"{field_type}:{field_key}" if field_key else field_type
        return self.set(part, value, expire_seconds)

    def get_with_legacy(
        self,
        part: str,
        legacy_key: str,
    ) -> Optional[Union[str, bytes]]:
        """
        Get value for part; if missing, try legacy_key. If found in legacy only
        and migrate_legacy_on_read, copy to new key, delete legacy, add to index.
        Propagates the legacy key's remaining TTL to the new key.
        """
        new_key = _dsr_key(self._dsr_id, part)
        val = self._redis.get(new_key)
        if val is not None:
            return val
        val = self._redis.get(legacy_key)
        if val is None:
            # Re-check: another reader may have migrated between our two GETs
            return self._redis.get(new_key)
        if self._migrate_on_read:
            ttl = self._redis.ttl(legacy_key)
            expire = ttl if ttl > 0 else self._default_ttl
            self.set(part, val, expire)
            self._redis.delete(legacy_key)
        return val

    def get(self, part: str) -> Optional[Union[str, bytes]]:
        """Get a value for the given DSR and part. Returns None if missing."""
        return self._redis.get(_dsr_key(self._dsr_id, part))

    def set(
        self,
        part: str,
        value: RedisValue,
        expire_seconds: int,
    ) -> Optional[bool]:
        """
        Set a value for the given DSR and part. Registers the key in the DSR index.
        """
        key = _dsr_key(self._dsr_id, part)
        return self._manager.set_with_index(
            key, value, _dsr_index_prefix(self._dsr_id), expire_seconds
        )

    def delete(self, part: str) -> None:
        """Delete a single part and remove it from the DSR index."""
        key = _dsr_key(self._dsr_id, part)
        self._manager.delete_key_and_remove_from_index(
            key, _dsr_index_prefix(self._dsr_id)
        )

    # --- Shared get/has helpers ---

    def _get_cached_by_type(
        self,
        new_infix: str,
        legacy_infix: str,
        getter: Callable[[str], Optional[Union[str, bytes]]],
    ) -> Dict[str, Any]:
        """Shared implementation for get_cached_custom_fields/identity_data/drp_request_body."""
        result: Dict[str, Any] = {}
        for key in self.get_all_keys():
            if new_infix in key:
                field = key.split(":")[-1]
            elif legacy_infix in key:
                field = key.split(legacy_infix, 1)[-1]
            else:
                continue
            value = getter(field)
            if value:  # Intentionally drops empty/falsy — matches legacy behavior
                result[field] = value
        return result

    def _has_cached_by_type(self, new_infix: str, legacy_infix: str) -> bool:
        """Shared implementation for has_cached_* methods."""
        return any(new_infix in k or legacy_infix in k for k in self.get_all_keys())

    # --- Convenience: custom privacy request fields ---

    def write_custom_field(
        self,
        field_key: str,
        value: RedisValue,
        expire_seconds: int,
    ) -> Optional[bool]:
        """Write a custom privacy request field. New key: dsr:{id}:custom_field:{field_key}."""
        return self.write("custom_field", field_key, value, expire_seconds)

    def get_custom_field(self, field_key: str) -> Optional[Union[str, bytes]]:
        """Get custom field; reads from legacy id-{id}-custom-privacy-request-field-{key} if needed."""
        part = f"custom_field:{field_key}"
        return self.get_with_legacy(
            part, KeyMapper.custom_field(self._dsr_id, field_key)[1]
        )

    def cache_custom_fields(
        self,
        custom_fields: Dict[str, Any],
        expire_seconds: int,
    ) -> None:
        """
        Cache all custom privacy request fields for a DSR.

        Writes each non-None field to dsr:{id}:custom_field:{field_key} format.
        """
        for key, value in custom_fields.items():
            if value is not None:
                self.write_custom_field(key, value, expire_seconds)

    def get_cached_custom_fields(self) -> Dict[str, Any]:
        """
        Retrieve all cached custom fields for a DSR.

        Returns dict with custom field values. Automatically migrates legacy keys on read.
        Returns empty dict if no custom fields cached.
        """
        return self._get_cached_by_type(
            ":custom_field:",
            "-custom-privacy-request-field-",
            self.get_custom_field,
        )

    def has_cached_custom_fields(self) -> bool:
        """
        Check if any custom fields are cached for this DSR.

        Returns True if any custom field keys exist (legacy or new format).
        """
        return self._has_cached_by_type(
            ":custom_field:", "-custom-privacy-request-field-"
        )

    # --- Convenience: identity ---

    def write_identity(
        self,
        attr: str,
        value: RedisValue,
        expire_seconds: int,
    ) -> Optional[bool]:
        """Write an identity attribute. New key: dsr:{id}:identity:{attr}."""
        return self.write("identity", attr, value, expire_seconds)

    def get_identity(self, attr: str) -> Optional[Union[str, bytes]]:
        """Get identity attribute; reads from legacy id-{id}-identity-{attr} if needed."""
        part = f"identity:{attr}"
        return self.get_with_legacy(part, KeyMapper.identity(self._dsr_id, attr)[1])

    def cache_identity_data(
        self,
        identity_dict: Dict[str, Any],
        expire_seconds: int,
    ) -> None:
        """
        Cache all identity attributes for a DSR.

        Writes each non-None attribute to dsr:{id}:identity:{attr} format.
        """
        for key, value in identity_dict.items():
            if value is not None:
                self.write_identity(key, value, expire_seconds)

    def get_cached_identity_data(self) -> Dict[str, Any]:
        """
        Retrieve all cached identity data for a DSR.

        Returns dict with identity attributes. Automatically migrates legacy keys on read.
        Returns empty dict if no identity data cached.
        """
        return self._get_cached_by_type(":identity:", "-identity-", self.get_identity)

    def has_cached_identity_data(self) -> bool:
        """
        Check if any identity data is cached for this DSR.

        Returns True if any identity keys exist (legacy or new format).
        """
        return self._has_cached_by_type(":identity:", "-identity-")

    # --- Convenience: encryption ---

    def write_encryption(
        self,
        attr: str,
        value: RedisValue,
        expire_seconds: int,
    ) -> Optional[bool]:
        """Write an encryption attribute. New key: dsr:{id}:encryption:{attr}."""
        return self.write("encryption", attr, value, expire_seconds)

    def get_encryption(self, attr: str) -> Optional[Union[str, bytes]]:
        """Get encryption attribute; reads from legacy id-{id}-encryption-{attr} if needed."""
        part = f"encryption:{attr}"
        return self.get_with_legacy(part, KeyMapper.encryption(self._dsr_id, attr)[1])

    # --- Convenience: DRP request body ---

    def write_drp(
        self,
        attr: str,
        value: RedisValue,
        expire_seconds: int,
    ) -> Optional[bool]:
        """Write DRP request body attribute. New key: dsr:{id}:drp:{attr}."""
        return self.write("drp", attr, value, expire_seconds)

    def get_drp(self, attr: str) -> Optional[Union[str, bytes]]:
        """Get DRP attribute; reads from legacy id-{id}-drp-{attr} if needed."""
        part = f"drp:{attr}"
        return self.get_with_legacy(part, KeyMapper.drp(self._dsr_id, attr)[1])

    def cache_drp_request_body(
        self,
        drp_body: Dict[str, Any],
        expire_seconds: int,
    ) -> None:
        """
        Cache all DRP request body fields for a DSR.
        Writes each non-None field to dsr:{id}:drp:{field_key} format.
        """
        for key, value in drp_body.items():
            if value is not None:
                self.write_drp(key, value, expire_seconds)

    def get_cached_drp_request_body(self) -> Dict[str, Any]:
        """
        Retrieve all cached DRP request body data for a DSR.
        Returns dict with DRP fields. Automatically migrates legacy keys on read.
        Returns empty dict if no DRP data cached.
        """
        return self._get_cached_by_type(":drp:", "-drp-", self.get_drp)

    def has_cached_drp_request_body(self) -> bool:
        """
        Check if any DRP request body data is cached for this DSR.
        Checks both new and legacy key formats.
        """
        return self._has_cached_by_type(":drp:", "-drp-")

    # --- Convenience: masking secret ---

    def write_masking_secret(
        self,
        strategy: str,
        secret_type: str,
        value: RedisValue,
        expire_seconds: int,
    ) -> Optional[bool]:
        """Write masking secret. New key: dsr:{id}:masking_secret:{strategy}:{secret_type}."""
        part = f"masking_secret:{strategy}:{secret_type}"
        return self.set(part, value, expire_seconds)

    def get_masking_secret(
        self,
        strategy: str,
        secret_type: str,
    ) -> Optional[Union[str, bytes]]:
        """Get masking secret; reads from legacy id-{id}-masking-secret-{strategy}-{type} if needed."""
        part = f"masking_secret:{strategy}:{secret_type}"
        return self.get_with_legacy(
            part,
            KeyMapper.masking_secret(self._dsr_id, strategy, secret_type)[1],
        )

    # --- Convenience: async execution (single value per DSR) ---

    def write_async_execution(
        self,
        value: RedisValue,
        expire_seconds: int,
    ) -> Optional[bool]:
        """Write async task id. New key: dsr:{id}:async_execution."""
        return self.write("async_execution", "", value, expire_seconds)

    def get_async_execution(self) -> Optional[Union[str, bytes]]:
        """Get async task id; reads from legacy id-{id}-async-execution if needed."""
        part = "async_execution"
        return self.get_with_legacy(part, KeyMapper.async_execution(self._dsr_id)[1])

    # --- Convenience: retry count ---

    def write_retry_count(
        self,
        value: RedisValue,
        expire_seconds: int,
    ) -> Optional[bool]:
        """Write privacy request retry count. New key: dsr:{id}:retry_count."""
        return self.write("retry_count", "", value, expire_seconds)

    def get_retry_count(self) -> Optional[Union[str, bytes]]:
        """Get retry count; reads from legacy id-{id}-privacy-request-retry-count if needed."""
        part = "retry_count"
        return self.get_with_legacy(part, KeyMapper.retry_count(self._dsr_id)[1])

    # --- List / clear ---

    def get_all_keys(self) -> list[str]:
        """
        Return all cache keys for this DSR.

        Uses the index first. If a migration flag confirms no legacy keys remain,
        returns index contents directly. Otherwise, does a one-time SCAN to find
        legacy stragglers, backfills them into the index, and sets the migration
        flag so future calls skip the SCAN.
        """
        index_prefix = _dsr_index_prefix(self._dsr_id)
        keys = self._manager.get_keys_by_index(index_prefix)

        # If we've already confirmed no legacy keys remain, index is authoritative
        migration_key = f"__migrated:{self._dsr_id}"
        if keys and self._redis.exists(migration_key):
            return keys

        # SCAN for all keys (one-time per DSR until migration confirmed)
        # Filter out internal keys (__migrated:, __idx:) that match the SCAN pattern
        scanned_keys = [
            k
            for k in self._redis.scan_iter(match=f"*{self._dsr_id}*", count=500)
            if not k.startswith("__migrated:") and not k.startswith("__idx:")
        ]
        indexed = set(keys)
        scanned_set = set(scanned_keys)
        all_keys = list(indexed | scanned_set) if keys else scanned_keys

        if not all_keys:
            return []

        if self._backfill:
            for k in scanned_keys:
                if k not in indexed:
                    self._manager.add_key_to_index(index_prefix, k)

        # If index existed and no scanned keys found outside it, mark as migrated
        if keys and not (scanned_set - indexed):
            self._redis.setex(migration_key, 86400, "1")  # 24h TTL

        return all_keys

    def clear(self) -> None:
        """
        Delete all cache keys for this DSR and remove the index.

        Always uses SCAN to find all keys (both indexed and legacy) to ensure
        complete cleanup in mixed-key scenarios. Does a second SCAN pass to
        catch keys written by concurrent migrations between the first SCAN
        and DELETE.
        """
        all_keys = list(self._redis.scan_iter(match=f"*{self._dsr_id}*", count=500))
        index_prefix = _dsr_index_prefix(self._dsr_id)
        if all_keys:
            self._redis.delete(*all_keys)
        self._manager.delete_index(index_prefix)
        # Invalidate migration flag so future reads re-scan
        self._redis.delete(f"__migrated:{self._dsr_id}")
        # Second pass: catch keys written by concurrent migrations
        stragglers = list(self._redis.scan_iter(match=f"*{self._dsr_id}*", count=500))
        if stragglers:
            self._redis.delete(*stragglers)
