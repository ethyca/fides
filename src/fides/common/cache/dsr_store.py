"""DSR cache store: single place for all DSR (privacy request) cache access.

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

import re
from typing import Any, Callable, Dict, List, Optional, Set, Union

from loguru import logger
from redis import Redis

from fides.common.cache.key_mapping import DSR_KEY_PREFIX, KeyMapper
from fides.common.cache.manager import RedisCacheManager, RedisValue
from fides.common.cache.redis_json_codec import decode_cache_obj, encode_cache_obj
from fides.config import CONFIG

__all__ = [
    "DSR_KEY_PREFIX",
    "DSRCacheStore",
    "candidate_privacy_request_ids_for_sweep",
    "decode_dsr_redis_key",
    "redis_key_is_dsr_cache_key_for_id",
]


def _dsr_key(dsr_id: str, part: str) -> str:
    """Build the Redis key for a DSR cache part."""
    return f"{DSR_KEY_PREFIX}{dsr_id}:{part}"


def _dsr_index_prefix(dsr_id: str) -> str:
    """Index prefix for this DSR; index set is __idx:dsr:{dsr_id}."""
    return f"{DSR_KEY_PREFIX}{dsr_id}"


# Canonical 8-4-4-4-12 UUID tokens (case-insensitive). Privacy request ids are typically
# ``pri_<uuid>``; sweepers extract uuid substrings then expand to both bare and ``pri_``
# forms for membership checks against DB ids.
_DSR_REDIS_KEY_SWEEP_UUID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.IGNORECASE,
)


def decode_dsr_redis_key(raw: Any) -> str:
    """Decode a Redis key from SCAN/MGET for consistent string handling."""
    if isinstance(raw, bytes):
        return raw.decode("utf-8", errors="replace")
    return str(raw)


def _normalize_uuid_token(token: str) -> str:
    return token.lower()


def _dsr_logical_body_matches_cache_id(body: str, dsr_id_lower: str) -> bool:
    """True if ``body`` matches a known DSR logical/encoded-object key shape for this id."""
    if body.startswith(f"{dsr_id_lower}__"):
        return True
    if body.startswith(f"WEBHOOK_MANUAL_ACCESS_INPUT__{dsr_id_lower}__"):
        return True
    if body.startswith(f"WEBHOOK_MANUAL_ERASURE_INPUT__{dsr_id_lower}__"):
        return True
    if body == f"DATA_USE_MAP__{dsr_id_lower}":
        return True
    if body.startswith(f"EMAIL_INFORMATION__{dsr_id_lower}__"):
        return True
    if body == f"PAUSED_LOCATION__{dsr_id_lower}":
        return True
    if body == f"FAILED_LOCATION__{dsr_id_lower}":
        return True
    if body.startswith(f"PLACEHOLDER_RESULTS__{dsr_id_lower}__"):
        return True
    return False


def redis_key_is_dsr_cache_key_for_id(key: str, dsr_id_lower: str) -> bool:
    """
    Return True if ``key`` is a known Fides DSR cache Redis key for ``dsr_id_lower``.

    Conservative: avoids deleting unrelated keys that merely embed a UUID substring
    unless they match ``dsr:`` / index / migration / legacy ``id-`` / ``EN_`` logical
    patterns documented in ``KeyMapper`` and ``DSRCacheStore``.
    """
    if key.startswith(f"dsr:{dsr_id_lower}:"):
        return True
    if key == f"__idx:dsr:{dsr_id_lower}":
        return True
    if key == f"__migrated:{dsr_id_lower}":
        return True
    if key.startswith(f"id-{dsr_id_lower}-"):
        return True
    if key.startswith("EN_"):
        return _dsr_logical_body_matches_cache_id(key[3:], dsr_id_lower)
    return _dsr_logical_body_matches_cache_id(key, dsr_id_lower)


def candidate_privacy_request_ids_for_sweep(key: str) -> Set[str]:
    """Candidate ids to check with SMISMEMBER (normalized lowercase)."""
    out: set[str] = set()
    for m in _DSR_REDIS_KEY_SWEEP_UUID_RE.findall(key):
        u = _normalize_uuid_token(m)
        out.add(u)
        # Product privacy request ids are ``pri_<uuid>`` (see DSR package link validation).
        out.add(f"pri_{u}")
    return out


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

    # --- Encoded JSON blobs (legacy EN_{logical} + indexed dsr:{id}:…) ---

    @staticmethod
    def _redis_str(val: Optional[Union[str, bytes]]) -> Optional[str]:
        if val is None:
            return None
        if isinstance(val, bytes):
            return val.decode("utf-8", errors="replace")
        return str(val)

    def _legacy_en_key(self, legacy_logical: str) -> str:
        return f"EN_{legacy_logical}"

    def _get_decoded_encoded_with_legacy(
        self, part: str, legacy_logical: str
    ) -> Optional[Any]:
        """Read JSON-encoded object from new key, else legacy EN_{logical}; optionally migrate."""
        new_key = _dsr_key(self._dsr_id, part)
        raw = self._redis.get(new_key)
        s = self._redis_str(raw)
        if s is not None:
            return decode_cache_obj(s)

        legacy_key = self._legacy_en_key(legacy_logical)
        raw = self._redis.get(legacy_key)
        if raw is None:
            return None

        payload = self._redis_str(raw)
        decoded = decode_cache_obj(payload)
        if self._migrate_on_read and payload is not None:
            ttl = self._redis.ttl(legacy_key)
            expire = ttl if ttl > 0 else self._default_ttl
            self.set(part, payload, expire)
            self._redis.delete(legacy_key)
        return decoded

    def _set_encoded_json(
        self,
        part: str,
        legacy_logical: str,
        obj: Any,
        expire_seconds: int,
    ) -> None:
        """Write JSON-encoded object to indexed new key and remove legacy EN_* if present."""
        payload = encode_cache_obj(obj)
        self.set(part, payload, expire_seconds)
        legacy_key = self._legacy_en_key(legacy_logical)
        if self._redis.get(legacy_key) is not None:
            self._redis.delete(legacy_key)

    def write_encoded_email_info(
        self,
        step: str,
        dataset: str,
        collection: str,
        obj: Any,
        expire_seconds: int,
    ) -> None:
        _, legacy_logical = KeyMapper.email_info(
            self._dsr_id, step, dataset, collection
        )
        part = f"email_info:{step}:{dataset}:{collection}"
        self._set_encoded_json(part, legacy_logical, obj, expire_seconds)

    def list_decoded_email_info_for_dataset(self, step: str, dataset: str) -> List[Any]:
        """Return decoded email checkpoint payloads for a dataset.

        Always reads ``dsr:{id}:email_info:…`` keys registered in the per-DSR index.

        When ``CONFIG.redis.dsr_cache_strict_index`` is False, also runs a **narrow**
        ``SCAN … MATCH EN_EMAIL_INFORMATION__{id}__{step}__{dataset}__*`` to discover
        legacy encoded keys not yet represented under ``dsr:`` parts. When strict
        mode is True, legacy ``EN_*`` keys are ignored here (index-only listing).
        """
        index_prefix = _dsr_index_prefix(self._dsr_id)
        dsr_full_prefix = f"{DSR_KEY_PREFIX}{self._dsr_id}:"
        part_prefix = f"email_info:{step}:{dataset}:"
        items: List[tuple[str, Any]] = []
        for full_key in self._manager.get_keys_by_index(index_prefix):
            if not full_key.startswith(dsr_full_prefix):
                continue
            part = full_key[len(dsr_full_prefix) :]
            if not part.startswith(part_prefix):
                continue
            collection = part[len(part_prefix) :]
            _, legacy_logical = KeyMapper.email_info(
                self._dsr_id, step, dataset, collection
            )
            decoded = self._get_decoded_encoded_with_legacy(part, legacy_logical)
            if decoded is not None:
                items.append((part, decoded))

        seen_collections = {part[len(part_prefix) :] for part, _ in items}

        if not CONFIG.redis.dsr_cache_strict_index:
            en_match_prefix = (
                f"EN_EMAIL_INFORMATION__{self._dsr_id}__{step}__{dataset}__"
            )
            for raw_key in self._redis.scan_iter(
                match=f"{en_match_prefix}*", count=500
            ):
                redis_key = decode_dsr_redis_key(raw_key)
                if not redis_key.startswith("EN_"):
                    continue
                logical = redis_key[len("EN_") :]
                em_pfx = "EMAIL_INFORMATION__"
                if not logical.startswith(em_pfx):
                    continue
                rest = logical[len(em_pfx) :]
                try:
                    pr_id, step_v, ds, coll = rest.rsplit("__", 3)
                except ValueError:
                    continue
                if pr_id != self._dsr_id or step_v != step or ds != dataset:
                    continue
                if coll in seen_collections:
                    continue
                raw_val = self._redis.get(redis_key)
                payload = self._redis_str(raw_val)
                if not payload:
                    continue
                decoded = decode_cache_obj(payload)
                if decoded is None:
                    continue
                part = f"email_info:{step}:{dataset}:{coll}"
                items.append((part, decoded))
                seen_collections.add(coll)

        items.sort(key=lambda t: t[0])
        return [d for _, d in items]

    def write_encoded_data_use_map(self, obj: Any, expire_seconds: int) -> None:
        _, legacy_logical = KeyMapper.data_use_map(self._dsr_id)
        self._set_encoded_json("data_use_map", legacy_logical, obj, expire_seconds)

    def read_encoded_data_use_map(self) -> Optional[Any]:
        _, legacy_logical = KeyMapper.data_use_map(self._dsr_id)
        return self._get_decoded_encoded_with_legacy("data_use_map", legacy_logical)

    def write_encoded_webhook_manual_access(
        self, webhook_id: str, obj: Any, expire_seconds: int
    ) -> None:
        _, legacy_logical = KeyMapper.webhook_manual_access(self._dsr_id, webhook_id)
        part = f"webhook_manual_access:{webhook_id}"
        self._set_encoded_json(part, legacy_logical, obj, expire_seconds)

    def read_encoded_webhook_manual_access(self, webhook_id: str) -> Optional[Any]:
        _, legacy_logical = KeyMapper.webhook_manual_access(self._dsr_id, webhook_id)
        part = f"webhook_manual_access:{webhook_id}"
        return self._get_decoded_encoded_with_legacy(part, legacy_logical)

    def write_encoded_webhook_manual_erasure(
        self, webhook_id: str, obj: Any, expire_seconds: int
    ) -> None:
        _, legacy_logical = KeyMapper.webhook_manual_erasure(self._dsr_id, webhook_id)
        part = f"webhook_manual_erasure:{webhook_id}"
        self._set_encoded_json(part, legacy_logical, obj, expire_seconds)

    def read_encoded_webhook_manual_erasure(self, webhook_id: str) -> Optional[Any]:
        _, legacy_logical = KeyMapper.webhook_manual_erasure(self._dsr_id, webhook_id)
        part = f"webhook_manual_erasure:{webhook_id}"
        return self._get_decoded_encoded_with_legacy(part, legacy_logical)

    def write_encoded_paused_location(self, obj: Any, expire_seconds: int) -> None:
        _, legacy_logical = KeyMapper.paused_location(self._dsr_id)
        self._set_encoded_json("paused_location", legacy_logical, obj, expire_seconds)

    def read_encoded_paused_location(self) -> Optional[Any]:
        _, legacy_logical = KeyMapper.paused_location(self._dsr_id)
        return self._get_decoded_encoded_with_legacy("paused_location", legacy_logical)

    def write_encoded_failed_location(self, obj: Any, expire_seconds: int) -> None:
        _, legacy_logical = KeyMapper.failed_location(self._dsr_id)
        self._set_encoded_json("failed_location", legacy_logical, obj, expire_seconds)

    def read_encoded_failed_location(self) -> Optional[Any]:
        _, legacy_logical = KeyMapper.failed_location(self._dsr_id)
        return self._get_decoded_encoded_with_legacy("failed_location", legacy_logical)

    # --- List / clear ---

    def get_all_keys(self) -> list[str]:
        """
        Return all cache keys for this DSR.

        Prefers the DSR index (``SMEMBERS`` on ``__idx:dsr:{id}``). When
        ``CONFIG.redis.dsr_cache_strict_index`` is True, never scans. Otherwise,
        performs at most one keyspace ``SCAN`` per DSR until the migration marker
        shows the index is complete, backfilling discovered keys into the index.
        """
        index_prefix = _dsr_index_prefix(self._dsr_id)
        keys = self._manager.get_keys_by_index(index_prefix)
        migration_key = f"__migrated:{self._dsr_id}"

        if CONFIG.redis.dsr_cache_strict_index:
            return keys

        if keys and self._redis.exists(migration_key):
            return keys

        logger.warning(
            "DSR cache: get_all_keys SCAN for dsr_id={} (set redis.dsr_cache_strict_index to skip)",
            self._dsr_id,
        )
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

        if keys and not (scanned_set - indexed):
            self._redis.setex(migration_key, 86400, "1")  # 24h TTL

        return all_keys

    def clear(self) -> None:
        """
        Delete all indexed cache keys for this DSR and remove the index.

        Intentionally **does not** scan Redis: only keys registered in
        ``__idx:dsr:{id}`` are removed (via ``delete_keys_by_index``). Legacy
        ``EN_*`` or ``id-{id}-*`` values that never entered that index can remain
        until TTL expiry or until the **DSR cache sweeper** (and related hygiene)
        deletes them. Prefer running index backfill / migration before relying on
        ``clear()`` alone for compliance-sensitive teardown.
        """
        index_prefix = _dsr_index_prefix(self._dsr_id)
        self._manager.delete_keys_by_index(index_prefix)
        self._redis.delete(f"__migrated:{self._dsr_id}")
