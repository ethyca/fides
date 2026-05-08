"""Unit tests for DSR cache sweeper status helpers."""

from fides.api.schemas.privacy_request import (
    ACTIVE_REQUEST_STATUSES,
    PrivacyRequestStatus,
)
from fides.service.privacy_request.dsr_cache_sweeper import (
    build_dsr_cache_sweeper_statuses,
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
