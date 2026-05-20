"""Tests for access_review_hooks — gate logic with DB-backed fixtures."""

from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from fides.api.graph.graph import DatasetGraph
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.policy import CurrentStep
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.service.privacy_request.access_review_hooks import (
    should_wait_for_access_review,
)
from fides.api.service.privacy_request.dsr_package.dsr_report_builder import (
    DSRReportBuilder,
)
from fides.api.service.privacy_request.dsr_package.dsr_report_builder_registry import (
    set_access_review_required,
    set_dsr_report_builder,
    set_pre_restart_cleanup,
    set_review_approved_callback,
)
from fides.service.privacy_request.privacy_request_service import (
    _process_privacy_request_restart,
)


@pytest.fixture(autouse=True)
def _reset_registry():
    """Reset all registry state after each test."""
    yield
    set_dsr_report_builder(DSRReportBuilder)
    set_access_review_required(False)
    set_review_approved_callback(None)
    set_pre_restart_cleanup(None)


def _run_gate(db: Session, policy: Policy, privacy_request: PrivacyRequest) -> bool:
    """Run the access review gate with minimal arguments."""
    return should_wait_for_access_review(
        session=db,
        policy=policy,
        access_result={},
        dataset_graph=DatasetGraph(),
        privacy_request=privacy_request,
        manual_data_for_storage={},
        fides_connector_datasets=set(),
    )


class TestCheckAccessReviewGate:
    def test_returns_false_when_review_not_required(
        self, db: Session, policy: Policy, privacy_request: PrivacyRequest
    ):
        """Gate is off by default — request proceeds to upload."""
        assert _run_gate(db, policy, privacy_request) is False

    def test_skips_pure_erasure_requests(
        self, db: Session, erasure_policy: Policy, privacy_request: PrivacyRequest
    ):
        """Gate should not fire for erasure-only requests."""
        set_access_review_required(True)
        assert _run_gate(db, erasure_policy, privacy_request) is False

    def test_skips_when_already_approved(
        self, db: Session, policy: Policy, privacy_request: PrivacyRequest
    ):
        """Gate should not fire when the approved callback returns True."""
        set_access_review_required(True)
        set_review_approved_callback(lambda pr_id, session: True)
        assert _run_gate(db, policy, privacy_request) is False

    def test_continues_when_approved_callback_returns_false(
        self, db: Session, policy: Policy, privacy_request: PrivacyRequest
    ):
        """Gate fires even when an approved callback is registered but returns False."""
        set_access_review_required(True)
        set_review_approved_callback(lambda pr_id, session: False)

        assert _run_gate(db, policy, privacy_request) is True

        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.awaiting_access_review

    def test_pauses_request(
        self,
        db: Session,
        policy: Policy,
        privacy_request: PrivacyRequest,
    ):
        """Gate pauses the request: saves results, sets status, returns True."""
        set_access_review_required(True)

        assert _run_gate(db, policy, privacy_request) is True

        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.awaiting_access_review


_QUEUE_PR = (
    "fides.service.privacy_request.privacy_request_service.queue_privacy_request"
)


class TestRestartCleanup:
    """Verify _process_privacy_request_restart cleans up review state."""

    @patch(_QUEUE_PR)
    def test_cleanup_called_on_restart_from_awaiting_review(
        self, mock_queue, db: Session, privacy_request: PrivacyRequest
    ):
        """Cleanup callback fires before status transitions to in_processing."""
        privacy_request.status = PrivacyRequestStatus.awaiting_access_review
        privacy_request.save(db=db)

        cleanup_calls: list[str] = []
        set_pre_restart_cleanup(lambda pr_id, session: cleanup_calls.append(pr_id))

        _process_privacy_request_restart(privacy_request, CurrentStep.upload_access, db)

        assert cleanup_calls == [privacy_request.id]
        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.in_processing
        mock_queue.assert_called_once()

    @patch(_QUEUE_PR)
    def test_restart_without_cleanup_callback(
        self, mock_queue, db: Session, privacy_request: PrivacyRequest
    ):
        """Restart works when no cleanup callback is registered."""
        privacy_request.status = PrivacyRequestStatus.awaiting_access_review
        privacy_request.save(db=db)

        _process_privacy_request_restart(privacy_request, CurrentStep.upload_access, db)

        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.in_processing
        mock_queue.assert_called_once()

    @patch(_QUEUE_PR)
    def test_cleanup_not_called_for_other_statuses(
        self, mock_queue, db: Session, privacy_request: PrivacyRequest
    ):
        """Cleanup only fires for awaiting_access_review, not other error states."""
        privacy_request.status = PrivacyRequestStatus.error
        privacy_request.save(db=db)

        cleanup_calls: list[str] = []
        set_pre_restart_cleanup(lambda pr_id, session: cleanup_calls.append(pr_id))

        _process_privacy_request_restart(privacy_request, None, db)

        assert cleanup_calls == []
        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.in_processing
