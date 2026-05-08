"""Unit tests for DSR cache sweeper status helpers."""

from fides.api.schemas.privacy_request import (
    ACTIVE_REQUEST_STATUSES,
    PrivacyRequestStatus,
)
from fides.service.privacy_request.dsr_cache_sweeper import (
    _candidate_privacy_request_ids_in_key,
    build_dsr_cache_sweeper_statuses,
    redis_key_is_dsr_cache_key_for_id,
)


def test_build_terminal_statuses_complete_and_canceled_only() -> None:
    statuses = build_dsr_cache_sweeper_statuses(
        include_denied_and_duplicate=False,
        include_error=False,
    )
    assert statuses == {
        PrivacyRequestStatus.complete,
        PrivacyRequestStatus.canceled,
    }


def test_build_terminal_statuses_includes_denied_duplicate_when_enabled() -> None:
    statuses = build_dsr_cache_sweeper_statuses(
        include_denied_and_duplicate=True,
        include_error=False,
    )
    assert PrivacyRequestStatus.denied in statuses
    assert PrivacyRequestStatus.duplicate in statuses


def test_build_terminal_statuses_includes_error_when_enabled() -> None:
    statuses = build_dsr_cache_sweeper_statuses(
        include_denied_and_duplicate=False,
        include_error=True,
    )
    assert PrivacyRequestStatus.error in statuses


def test_terminal_allowlist_never_overlaps_active() -> None:
    statuses = build_dsr_cache_sweeper_statuses(
        include_denied_and_duplicate=True,
        include_error=True,
    )
    assert not (statuses & ACTIVE_REQUEST_STATUSES)


def test_redis_key_shape_matches_dsr_prefixes() -> None:
    uid = "aaaaaaaa-bbbb-4ccc-dddd-eeeeeeeeeeee"
    pri = f"pri_{uid}"
    assert redis_key_is_dsr_cache_key_for_id(f"dsr:{uid}:async_execution", uid)
    assert redis_key_is_dsr_cache_key_for_id(f"dsr:{pri}:async_execution", pri)
    assert redis_key_is_dsr_cache_key_for_id(f"__idx:dsr:{uid}", uid)
    assert redis_key_is_dsr_cache_key_for_id(f"__idx:dsr:{pri}", pri)
    assert redis_key_is_dsr_cache_key_for_id(f"__migrated:{uid}", uid)
    assert redis_key_is_dsr_cache_key_for_id(f"id-{uid}-async-execution", uid)
    assert redis_key_is_dsr_cache_key_for_id(f"id-{pri}-async-execution", pri)
    assert redis_key_is_dsr_cache_key_for_id(f"EN_DATA_USE_MAP__{uid}", uid)
    assert redis_key_is_dsr_cache_key_for_id(f"EN_DATA_USE_MAP__{pri}", pri)


def test_redis_key_shape_rejects_decoy_with_uuid() -> None:
    uid = "aaaaaaaa-bbbb-4ccc-dddd-eeeeeeeeeeee"
    pri = f"pri_{uid}"
    assert not redis_key_is_dsr_cache_key_for_id(f"DECOY-{uid}-noise", uid)
    assert not redis_key_is_dsr_cache_key_for_id(f"DECOY-{pri}-noise", pri)


def test_candidate_privacy_request_ids_expand_pri_prefix() -> None:
    uid = "AAAAAAAA-BBBB-4CCC-DDDD-EEEEEEEEEEEE"
    u = uid.lower()
    found = _candidate_privacy_request_ids_in_key(f"prefix-{uid}-suffix")
    assert found == {u, f"pri_{u}"}
