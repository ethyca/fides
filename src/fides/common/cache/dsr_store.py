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

from typing import Any, Dict, List, Optional, Union

from redis import Redis

from fides.common.cache.key_mapping import KeyMapper
from fides.common.cache.manager import RedisCacheManager, RedisValue

# Key format: dsr:{dsr_id}:{part} (re-export for callers; KeyMapper builds these)
DSR_KEY_PREFIX = "dsr:"


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
        cache_manager: RedisCacheManager,
        *,
        backfill_index_on_legacy_read: bool = True,
        migrate_legacy_on_read: bool = True,
    ) -> None:
        """
        Args:
            cache_manager: RedisCacheManager (e.g. from get_redis_cache_manager()).
            backfill_index_on_legacy_read: When listing keys and we fall back to
                KEYS for legacy keys, add those keys to the index. Default True.
            migrate_legacy_on_read: When a get finds value in legacy key only,
                write to new key, delete legacy key, add new key to index.
                Default True.
        """
        self._manager = cache_manager
        self._redis: Redis = cache_manager.redis
        self._backfill = backfill_index_on_legacy_read
        self._migrate_on_read = migrate_legacy_on_read

    def write(
        self,
        dsr_id: str,
        field_type: str,
        field_key: str,
        value: RedisValue,
        expire_seconds: Optional[int] = None,
    ) -> Optional[bool]:
        """
        Low-level write: set dsr:{dsr_id}:{field_type}:{field_key} and add to index.
        Prefer convenience methods (write_custom_field, etc.) so legacy mapping
        stays in one place.
        """
        part = f"{field_type}:{field_key}" if field_key else field_type
        return self.set(dsr_id, part, value, expire_seconds)

    def get_with_legacy(
        self,
        dsr_id: str,
        part: str,
        legacy_key: str,
    ) -> Optional[Union[str, bytes]]:
        """
        Get value for part; if missing, try legacy_key. If found in legacy only
        and migrate_legacy_on_read, copy to new key, delete legacy, add to index.
        """
        val = self._redis.get(_dsr_key(dsr_id, part))
        if val is not None:
            return val
        val = self._redis.get(legacy_key)
        if val is None:
            return None
        if self._migrate_on_read:
            self.set(dsr_id, part, val)
            self._redis.delete(legacy_key)
        return val

    def get(self, dsr_id: str, part: str) -> Optional[Union[str, bytes]]:
        """Get a value for the given DSR and part. Returns None if missing."""
        return self._redis.get(_dsr_key(dsr_id, part))

    def set(
        self,
        dsr_id: str,
        part: str,
        value: RedisValue,
        expire_seconds: Optional[int] = None,
    ) -> Optional[bool]:
        """
        Set a value for the given DSR and part. Registers the key in the DSR index.
        """
        key = _dsr_key(dsr_id, part)
        return self._manager.set_with_index(
            key, value, _dsr_index_prefix(dsr_id), expire_seconds
        )

    def delete(self, dsr_id: str, part: str) -> None:
        """Delete a single part and remove it from the DSR index."""
        key = _dsr_key(dsr_id, part)
        self._manager.delete_key_and_remove_from_index(key, _dsr_index_prefix(dsr_id))

    # --- Convenience: custom privacy request fields ---

    def write_custom_field(
        self,
        dsr_id: str,
        field_key: str,
        value: RedisValue,
        expire_seconds: Optional[int] = None,
    ) -> Optional[bool]:
        """Write a custom privacy request field. New key: dsr:{id}:custom_field:{field_key}."""
        return self.write(dsr_id, "custom_field", field_key, value, expire_seconds)

    def get_custom_field(
        self, dsr_id: str, field_key: str
    ) -> Optional[Union[str, bytes]]:
        """Get custom field; reads from legacy id-{id}-custom-privacy-request-field-{key} if needed."""
        part = f"custom_field:{field_key}"
        return self.get_with_legacy(
            dsr_id, part, KeyMapper.custom_field(dsr_id, field_key)[1]
        )

    def cache_custom_fields(
        self, dsr_id: str, custom_fields: Dict[str, Any], expire_seconds: Optional[int] = None
    ) -> None:
        """
        Cache all custom privacy request fields for a DSR.
        
        Writes each non-None field to dsr:{id}:custom_field:{field_key} format.
        """
        for key, value in custom_fields.items():
            if value is not None:
                self.write_custom_field(dsr_id, key, value, expire_seconds)

    def get_cached_custom_fields(self, dsr_id: str) -> Dict[str, Any]:
        """
        Retrieve all cached custom fields for a DSR.
        
        Returns dict with custom field values. Automatically migrates legacy keys on read.
        Returns empty dict if no custom fields cached.
        """
        result: Dict[str, Any] = {}
        all_keys = self.get_all_keys(dsr_id)
        
        # Filter for custom field keys (both new and legacy formats)
        # New: dsr:{id}:custom_field:{key}
        # Legacy: id-{id}-custom-privacy-request-field-{key}
        custom_keys = [
            k for k in all_keys 
            if ":custom_field:" in k or "-custom-privacy-request-field-" in k
        ]
        
        for key in custom_keys:
            # Extract field name from key
            if ":custom_field:" in key:
                field_key = key.split(":")[-1]
            else:
                # Legacy format
                field_key = key.split("-")[-1]
            
            value = self.get_custom_field(dsr_id, field_key)
            if value:
                result[field_key] = value
        
        return result

    def has_cached_custom_fields(self, dsr_id: str) -> bool:
        """
        Check if any custom fields are cached for this DSR.
        
        Returns True if any custom field keys exist (legacy or new format).
        """
        all_keys = self.get_all_keys(dsr_id)
        return any(
            ":custom_field:" in k or "-custom-privacy-request-field-" in k
            for k in all_keys
        )

    # --- Convenience: identity ---

    def write_identity(
        self,
        dsr_id: str,
        attr: str,
        value: RedisValue,
        expire_seconds: Optional[int] = None,
    ) -> Optional[bool]:
        """Write an identity attribute. New key: dsr:{id}:identity:{attr}."""
        return self.write(dsr_id, "identity", attr, value, expire_seconds)

    def get_identity(self, dsr_id: str, attr: str) -> Optional[Union[str, bytes]]:
        """Get identity attribute; reads from legacy id-{id}-identity-{attr} if needed."""
        part = f"identity:{attr}"
        return self.get_with_legacy(dsr_id, part, KeyMapper.identity(dsr_id, attr)[1])

    def cache_identity_data(
        self, dsr_id: str, identity_dict: Dict[str, Any], expire_seconds: Optional[int] = None
    ) -> None:
        """
        Cache all identity attributes for a DSR.
        
        Writes each non-None attribute to dsr:{id}:identity:{attr} format.
        """
        for key, value in identity_dict.items():
            if value is not None:
                self.write_identity(dsr_id, key, value, expire_seconds)

    def get_cached_identity_data(self, dsr_id: str) -> Dict[str, Any]:
        """
        Retrieve all cached identity data for a DSR.
        
        Returns dict with identity attributes. Automatically migrates legacy keys on read.
        Returns empty dict if no identity data cached.
        """
        result: Dict[str, Any] = {}
        all_keys = self.get_all_keys(dsr_id)
        
        # Filter for identity keys (both new and legacy formats)
        identity_keys = [k for k in all_keys if ":identity:" in k or "-identity-" in k]
        
        for key in identity_keys:
            # Extract attribute name from key
            # New format: dsr:{id}:identity:{attr}
            # Legacy format: id-{id}-identity-{attr}
            if ":identity:" in key:
                attr = key.split(":")[-1]
            else:
                # Legacy format
                attr = key.split("-")[-1]
            
            value = self.get_identity(dsr_id, attr)
            if value:
                result[attr] = value
        
        return result

    def has_cached_identity_data(self, dsr_id: str) -> bool:
        """
        Check if any identity data is cached for this DSR.
        
        Returns True if any identity keys exist (legacy or new format).
        """
        all_keys = self.get_all_keys(dsr_id)
        return any(":identity:" in k or "-identity-" in k for k in all_keys)

    # --- Convenience: encryption ---

    def write_encryption(
        self,
        dsr_id: str,
        attr: str,
        value: RedisValue,
        expire_seconds: Optional[int] = None,
    ) -> Optional[bool]:
        """Write an encryption attribute. New key: dsr:{id}:encryption:{attr}."""
        return self.write(dsr_id, "encryption", attr, value, expire_seconds)

    def get_encryption(self, dsr_id: str, attr: str) -> Optional[Union[str, bytes]]:
        """Get encryption attribute; reads from legacy id-{id}-encryption-{attr} if needed."""
        part = f"encryption:{attr}"
        return self.get_with_legacy(dsr_id, part, KeyMapper.encryption(dsr_id, attr)[1])

    # --- Convenience: DRP request body ---

    def write_drp(
        self,
        dsr_id: str,
        attr: str,
        value: RedisValue,
        expire_seconds: Optional[int] = None,
    ) -> Optional[bool]:
        """Write DRP request body attribute. New key: dsr:{id}:drp:{attr}."""
        return self.write(dsr_id, "drp", attr, value, expire_seconds)

    def get_drp(self, dsr_id: str, attr: str) -> Optional[Union[str, bytes]]:
        """Get DRP attribute; reads from legacy id-{id}-drp-{attr} if needed."""
        part = f"drp:{attr}"
        return self.get_with_legacy(dsr_id, part, KeyMapper.drp(dsr_id, attr)[1])

    def cache_drp_request_body(
        self, dsr_id: str, drp_body: Dict[str, Any], expire_seconds: Optional[int] = None
    ) -> None:
        """
        Cache all DRP request body fields for a DSR.
        Writes each non-None field to dsr:{id}:drp:{field_key} format.
        """
        for key, value in drp_body.items():
            if value is not None:
                self.write_drp(dsr_id, key, value, expire_seconds)

    def get_cached_drp_request_body(self, dsr_id: str) -> Dict[str, Any]:
        """
        Retrieve all cached DRP request body data for a DSR.
        Returns dict with DRP fields. Automatically migrates legacy keys on read.
        Returns empty dict if no DRP data cached.
        """
        result: Dict[str, Any] = {}
        all_keys = self.get_all_keys(dsr_id)

        # Filter for DRP keys (both new and legacy formats)
        drp_keys = [k for k in all_keys if ":drp:" in k or "-drp-" in k]

        for key in drp_keys:
            # Extract field name from key
            # New format: dsr:{id}:drp:{field}
            # Legacy format: id-{id}-drp-{field}
            if ":drp:" in key:
                field = key.split(":")[-1]
            else:
                # Legacy format
                field = key.split("-")[-1]

            value = self.get_drp(dsr_id, field)
            if value:
                result[field] = value

        return result

    def has_cached_drp_request_body(self, dsr_id: str) -> bool:
        """
        Check if any DRP request body data is cached for this DSR.
        Checks both new and legacy key formats.
        """
        all_keys = self.get_all_keys(dsr_id)
        return any(":drp:" in k or "-drp-" in k for k in all_keys)

    # --- Convenience: masking secret ---

    def write_masking_secret(
        self,
        dsr_id: str,
        strategy: str,
        secret_type: str,
        value: RedisValue,
        expire_seconds: Optional[int] = None,
    ) -> Optional[bool]:
        """Write masking secret. New key: dsr:{id}:masking_secret:{strategy}:{secret_type}."""
        part = f"masking_secret:{strategy}:{secret_type}"
        return self.set(dsr_id, part, value, expire_seconds)

    def get_masking_secret(
        self,
        dsr_id: str,
        strategy: str,
        secret_type: str,
    ) -> Optional[Union[str, bytes]]:
        """Get masking secret; reads from legacy id-{id}-masking-secret-{strategy}-{type} if needed."""
        part = f"masking_secret:{strategy}:{secret_type}"
        return self.get_with_legacy(
            dsr_id,
            part,
            KeyMapper.masking_secret(dsr_id, strategy, secret_type)[1],
        )

    # --- Convenience: async execution (single value per DSR) ---

    def write_async_execution(
        self,
        dsr_id: str,
        value: RedisValue,
        expire_seconds: Optional[int] = None,
    ) -> Optional[bool]:
        """Write async task id. New key: dsr:{id}:async_execution."""
        return self.write(dsr_id, "async_execution", "", value, expire_seconds)

    def get_async_execution(self, dsr_id: str) -> Optional[Union[str, bytes]]:
        """Get async task id; reads from legacy id-{id}-async-execution if needed."""
        part = "async_execution"
        return self.get_with_legacy(dsr_id, part, KeyMapper.async_execution(dsr_id)[1])

    # --- Convenience: retry count ---

    def write_retry_count(
        self,
        dsr_id: str,
        value: RedisValue,
        expire_seconds: Optional[int] = None,
    ) -> Optional[bool]:
        """Write privacy request retry count. New key: dsr:{id}:retry_count."""
        return self.write(dsr_id, "retry_count", "", value, expire_seconds)

    def get_retry_count(self, dsr_id: str) -> Optional[Union[str, bytes]]:
        """Get retry count; reads from legacy id-{id}-privacy-request-retry-count if needed."""
        part = "retry_count"
        return self.get_with_legacy(dsr_id, part, KeyMapper.retry_count(dsr_id)[1])

    # --- List / clear (unchanged) ---

    def get_all_keys(self, dsr_id: str) -> List[str]:
        """
        Return all cache keys for this DSR.
        Uses the index first; if empty, falls back to SCAN for legacy keys
        and optionally backfills the index.
        """
        index_prefix = _dsr_index_prefix(dsr_id)
        keys = self._manager.get_keys_by_index(index_prefix)
        if keys:
            return keys
        legacy_keys = list(self._redis.scan_iter(match=f"*{dsr_id}*", count=500))
        if not legacy_keys:
            return []
        if self._backfill:
            for k in legacy_keys:
                self._manager.add_key_to_index(index_prefix, k)
        return list(legacy_keys)

    def clear(self, dsr_id: str) -> None:
        """
        Delete all cache keys for this DSR and remove the index.
        
        Always uses SCAN to find all keys (both indexed and legacy) to ensure
        complete cleanup in mixed-key scenarios.
        """
        # Use SCAN to find ALL keys (indexed + legacy)
        all_keys_via_scan = list(self._redis.scan_iter(match=f"*{dsr_id}*", count=500))
        
        index_prefix = _dsr_index_prefix(dsr_id)
        
        # Delete all found keys in batch
        if all_keys_via_scan:
            self._redis.delete(*all_keys_via_scan)
        
        # Delete the index itself
        self._manager.delete_index(index_prefix)
