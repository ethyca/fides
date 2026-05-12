"""
Tests for ``redis.dsr_cache_strict_index`` (DSRCacheStore listing without keyspace SCAN).

When strict index mode is enabled, ``get_all_keys`` and helpers that depend on it
must not call ``scan_iter``. Legacy key *reads* still migrate via ``get_*`` paths.
When strict mode is off, ``get_all_keys`` may SCAN to discover unindexed legacy keys.
"""

from __future__ import annotations

from typing import Any, List, Tuple

import pytest

from fides.common.cache import dsr_store as dsr_store_module
from fides.common.cache.dsr_store import DSRCacheStore
from fides.common.cache.manager import RedisCacheManager
from fides.common.cache.redis_json_codec import encode_cache_obj

_TTL = 3600


def _make_legacy_key(dsr_id: str, field_type: str, field_name: str = "") -> str:
    if field_name:
        return f"id-{dsr_id}-{field_type}-{field_name}"
    return f"id-{dsr_id}-{field_type}"


def _make_new_key(dsr_id: str, part: str) -> str:
    return f"dsr:{dsr_id}:{part}"


def _wrap_scan_iter(mock_redis: Any) -> List[Tuple[tuple, dict]]:
    """Record each ``scan_iter`` call; chain to the mock's existing ``side_effect``."""
    inner = mock_redis.scan_iter.side_effect
    calls: List[Tuple[tuple, dict]] = []

    def wrapped(*args: Any, **kwargs: Any) -> Any:
        calls.append((args, kwargs))
        if callable(inner):
            return inner(*args, **kwargs)
        raise RuntimeError(
            "mock_redis.scan_iter.side_effect must be callable for scan tracking tests"
        )

    mock_redis.scan_iter.side_effect = wrapped
    return calls


@pytest.mark.unit
class TestStrictIndexNoScan:
    """``dsr_cache_strict_index=True`` avoids Redis keyspace scans for listings."""

    def test_get_all_keys_empty_index_no_scan(
        self,
        monkeypatch: pytest.MonkeyPatch,
        mock_redis: Any,
        manager: RedisCacheManager,
    ) -> None:
        monkeypatch.setattr(
            dsr_store_module.CONFIG.redis, "dsr_cache_strict_index", True, raising=False
        )
        scan_calls = _wrap_scan_iter(mock_redis)
        dsr_id = "test-pr-strict-empty"
        store = DSRCacheStore(dsr_id, manager)

        assert store.get_all_keys() == []
        assert scan_calls == []

    def test_get_all_keys_omits_unindexed_legacy_without_scan(
        self,
        monkeypatch: pytest.MonkeyPatch,
        mock_redis: Any,
        manager: RedisCacheManager,
    ) -> None:
        monkeypatch.setattr(
            dsr_store_module.CONFIG.redis, "dsr_cache_strict_index", True, raising=False
        )
        scan_calls = _wrap_scan_iter(mock_redis)
        dsr_id = "test-pr-strict-legacy-list"
        legacy = _make_legacy_key(dsr_id, "identity", "email")
        mock_redis.set(legacy, "only-legacy@example.com")

        store = DSRCacheStore(dsr_id, manager)
        assert store.get_all_keys() == []
        assert scan_calls == []

    def test_legacy_read_still_migrates_without_scan(
        self,
        monkeypatch: pytest.MonkeyPatch,
        mock_redis: Any,
        manager: RedisCacheManager,
    ) -> None:
        monkeypatch.setattr(
            dsr_store_module.CONFIG.redis, "dsr_cache_strict_index", True, raising=False
        )
        scan_calls = _wrap_scan_iter(mock_redis)
        dsr_id = "test-pr-strict-migrate-read"
        mock_redis.set(
            _make_legacy_key(dsr_id, "identity", "email"), "migrated@example.com"
        )

        store = DSRCacheStore(dsr_id, manager)
        assert store.get_identity("email") == "migrated@example.com"
        assert (
            mock_redis.get(_make_new_key(dsr_id, "identity:email"))
            == "migrated@example.com"
        )
        assert mock_redis.get(_make_legacy_key(dsr_id, "identity", "email")) is None
        assert scan_calls == []

    def test_indexed_operations_and_helpers_no_scan(
        self,
        monkeypatch: pytest.MonkeyPatch,
        mock_redis: Any,
        manager: RedisCacheManager,
    ) -> None:
        monkeypatch.setattr(
            dsr_store_module.CONFIG.redis, "dsr_cache_strict_index", True, raising=False
        )
        scan_calls = _wrap_scan_iter(mock_redis)
        dsr_id = "test-pr-strict-helpers"
        store = DSRCacheStore(dsr_id, manager)
        store.write_identity("email", "indexed@example.com", _TTL)
        store.write_custom_field("dept", "Eng", _TTL)

        assert store.get_all_keys()
        assert store.get_cached_identity_data() == {"email": "indexed@example.com"}
        assert store.has_cached_identity_data() is True
        assert store.get_cached_custom_fields() == {"dept": "Eng"}
        assert store.has_cached_custom_fields() is True
        store.clear()
        assert store.get_all_keys() == []
        assert scan_calls == []


@pytest.mark.unit
class TestNonStrictLegacyAndScan:
    """With strict index off, legacy migration on read still runs; listings may SCAN."""

    def test_legacy_migrated_on_read_when_not_strict(
        self,
        monkeypatch: pytest.MonkeyPatch,
        mock_redis: Any,
        manager: RedisCacheManager,
    ) -> None:
        monkeypatch.setattr(
            dsr_store_module.CONFIG.redis,
            "dsr_cache_strict_index",
            False,
            raising=False,
        )
        dsr_id = "test-pr-nonstrict-migrate"
        mock_redis.set(
            _make_legacy_key(dsr_id, "identity", "email"), "legacy@example.com"
        )

        store = DSRCacheStore(dsr_id, manager)
        assert store.get_identity("email") == "legacy@example.com"
        assert (
            mock_redis.get(_make_new_key(dsr_id, "identity:email"))
            == "legacy@example.com"
        )
        assert mock_redis.get(_make_legacy_key(dsr_id, "identity", "email")) is None

    def test_get_all_keys_invokes_scan_for_unindexed_legacy_when_not_strict(
        self,
        monkeypatch: pytest.MonkeyPatch,
        mock_redis: Any,
        manager: RedisCacheManager,
    ) -> None:
        monkeypatch.setattr(
            dsr_store_module.CONFIG.redis,
            "dsr_cache_strict_index",
            False,
            raising=False,
        )
        scan_calls = _wrap_scan_iter(mock_redis)
        dsr_id = "test-pr-nonstrict-scan"
        mock_redis.set(
            _make_legacy_key(dsr_id, "identity", "email"), "scan@example.com"
        )
        mock_redis.set(
            _make_legacy_key(dsr_id, "identity", "phone_number"), "+15555550100"
        )

        store = DSRCacheStore(dsr_id, manager)
        keys = store.get_all_keys()

        assert len(keys) == 2
        assert scan_calls, (
            "expected keyspace scan_iter when index is empty and strict is off"
        )
        idx_members = mock_redis.smembers(f"__idx:dsr:{dsr_id}")
        assert _make_legacy_key(dsr_id, "identity", "email") in idx_members
        assert _make_legacy_key(dsr_id, "identity", "phone_number") in idx_members


def _en_email_key(dsr_id: str, step: str, dataset: str, collection: str) -> str:
    return (
        f"EN_EMAIL_INFORMATION__{dsr_id}__{step}__{dataset}__{collection}"
    )


@pytest.mark.unit
class TestListEmailInfoLegacyEnScan:
    """Legacy ``EN_EMAIL_INFORMATION__*`` listing is gated on strict index mode."""

    def test_list_email_strict_index_skips_legacy_en_without_scan(
        self,
        monkeypatch: pytest.MonkeyPatch,
        mock_redis: Any,
        manager: RedisCacheManager,
    ) -> None:
        monkeypatch.setattr(
            dsr_store_module.CONFIG.redis, "dsr_cache_strict_index", True, raising=False
        )
        scan_calls = _wrap_scan_iter(mock_redis)
        dsr_id = "pri_test_email_strict"
        step, dataset, coll = "access", "postgres", "addresses"
        mock_redis.set(
            _en_email_key(dsr_id, step, dataset, coll),
            encode_cache_obj({"step": step, "collection": None, "action_needed": None}),
        )
        store = DSRCacheStore(dsr_id, manager)
        out = store.list_decoded_email_info_for_dataset(step, dataset)
        assert out == []
        assert scan_calls == []

    def test_list_email_non_strict_finds_legacy_en_with_scan(
        self,
        monkeypatch: pytest.MonkeyPatch,
        mock_redis: Any,
        manager: RedisCacheManager,
    ) -> None:
        monkeypatch.setattr(
            dsr_store_module.CONFIG.redis,
            "dsr_cache_strict_index",
            False,
            raising=False,
        )
        scan_calls = _wrap_scan_iter(mock_redis)
        dsr_id = "pri_test_email_nonstrict"
        step, dataset, coll = "access", "postgres", "addresses"
        payload = {"step": step, "collection": None, "action_needed": None}
        mock_redis.set(_en_email_key(dsr_id, step, dataset, coll), encode_cache_obj(payload))

        store = DSRCacheStore(dsr_id, manager)
        out = store.list_decoded_email_info_for_dataset(step, dataset)

        assert out == [payload]
        assert scan_calls, "expected narrow scan_iter for legacy EN email keys"

    def test_list_email_non_strict_prefers_index_over_duplicate_legacy_en(
        self,
        monkeypatch: pytest.MonkeyPatch,
        mock_redis: Any,
        manager: RedisCacheManager,
    ) -> None:
        monkeypatch.setattr(
            dsr_store_module.CONFIG.redis,
            "dsr_cache_strict_index",
            False,
            raising=False,
        )
        dsr_id = "pri_test_email_dedupe"
        step, dataset, coll = "access", "crm", "contacts"
        indexed_payload = {"step": step, "collection": None, "action_needed": None}
        legacy_payload = {"step": step, "collection": {"dataset": "x"}, "action_needed": None}

        store = DSRCacheStore(dsr_id, manager)
        store.write_encoded_email_info(step, dataset, coll, indexed_payload, _TTL)
        mock_redis.set(
            _en_email_key(dsr_id, step, dataset, coll), encode_cache_obj(legacy_payload)
        )

        out = store.list_decoded_email_info_for_dataset(step, dataset)
        assert len(out) == 1
        assert out[0] == indexed_payload
