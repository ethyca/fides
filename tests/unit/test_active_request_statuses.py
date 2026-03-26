"""Tests for ACTIVE_REQUEST_STATUSES and is_overdue filter."""

from fides.api.schemas.privacy_request import (
    ACTIVE_REQUEST_STATUSES,
    PrivacyRequestFilter,
    PrivacyRequestStatus,
)


class TestActiveRequestStatuses:
    def test_contains_expected_active_statuses(self):
        assert PrivacyRequestStatus.in_processing in ACTIVE_REQUEST_STATUSES
        assert PrivacyRequestStatus.pending in ACTIVE_REQUEST_STATUSES
        assert PrivacyRequestStatus.approved in ACTIVE_REQUEST_STATUSES
        assert PrivacyRequestStatus.paused in ACTIVE_REQUEST_STATUSES
        assert PrivacyRequestStatus.requires_input in ACTIVE_REQUEST_STATUSES
        assert (
            PrivacyRequestStatus.requires_manual_finalization in ACTIVE_REQUEST_STATUSES
        )
        assert PrivacyRequestStatus.pending_external in ACTIVE_REQUEST_STATUSES

    def test_excludes_terminal_statuses(self):
        assert PrivacyRequestStatus.complete not in ACTIVE_REQUEST_STATUSES
        assert PrivacyRequestStatus.canceled not in ACTIVE_REQUEST_STATUSES
        assert PrivacyRequestStatus.error not in ACTIVE_REQUEST_STATUSES
        assert PrivacyRequestStatus.denied not in ACTIVE_REQUEST_STATUSES
        assert PrivacyRequestStatus.duplicate not in ACTIVE_REQUEST_STATUSES
        assert PrivacyRequestStatus.identity_unverified not in ACTIVE_REQUEST_STATUSES


class TestPrivacyRequestFilterOverdue:
    def test_accepts_true(self):
        f = PrivacyRequestFilter(is_overdue=True)
        assert f.is_overdue is True

    def test_accepts_false(self):
        f = PrivacyRequestFilter(is_overdue=False)
        assert f.is_overdue is False

    def test_defaults_to_none(self):
        f = PrivacyRequestFilter()
        assert f.is_overdue is None
