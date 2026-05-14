"""Tests for access_review_hooks — gate logic with DB-backed fixtures."""

import pytest
from sqlalchemy.orm import Session

from fides.api.graph.graph import DatasetGraph
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.service.privacy_request.access_review_hooks import (
    check_access_review_gate,
)
from fides.api.service.privacy_request.dsr_package.dsr_report_builder import (
    DSRReportBuilder,
)
from fides.api.service.privacy_request.dsr_package.dsr_report_builder_registry import (
    set_access_review_required,
    set_dsr_report_builder,
    set_pre_restart_cleanup,
    set_review_approved_callback,
    set_review_gate_callback,
)
from fides.api.service.privacy_request.request_runner_service import (
    save_access_results,
)


@pytest.fixture(autouse=True)
def _reset_registry():
    """Reset all registry state after each test."""
    yield
    set_dsr_report_builder(DSRReportBuilder)
    set_access_review_required(False)
    set_review_approved_callback(None)  # type: ignore[arg-type]
    set_pre_restart_cleanup(None)  # type: ignore[arg-type]
    set_review_gate_callback(None)  # type: ignore[arg-type]


def _run_gate(db: Session, policy: Policy, privacy_request: PrivacyRequest) -> bool:
    """Run the access review gate with minimal arguments."""
    return check_access_review_gate(
        session=db,
        policy=policy,
        access_result={},
        dataset_graph=DatasetGraph(),
        privacy_request=privacy_request,
        manual_data_for_storage={},
        fides_connector_datasets=set(),
        save_access_results=save_access_results,
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

    def test_pauses_request_when_review_required(
        self,
        db: Session,
        policy: Policy,
        privacy_request: PrivacyRequest,
    ):
        """Gate fires: saves results, calls gate callback, sets status, returns True."""
        set_access_review_required(True)
        gate_calls = []
        set_review_gate_callback(lambda pr_id, session: gate_calls.append(pr_id))

        assert _run_gate(db, policy, privacy_request) is True
        assert gate_calls == [privacy_request.id]

        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.awaiting_access_review
