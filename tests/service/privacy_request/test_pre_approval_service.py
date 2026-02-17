"""Tests for pre-approval service-layer logic.

Covers:
- handle_approval sets status to awaiting_pre_approval when webhooks exist
- _trigger_pre_approval_webhooks creates audit log
- approve_privacy_requests accepts awaiting_pre_approval and pre_approval_not_eligible
- deny_privacy_requests accepts awaiting_pre_approval and pre_approval_not_eligible
- approve_privacy_requests audit log message varies by webhook_id presence
"""

from unittest.mock import create_autospec, patch

import pytest
from sqlalchemy.orm import Session

from fides.api.models.audit_log import AuditLog, AuditLogAction
from fides.api.models.pre_approval_webhook import PreApprovalWebhook
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.config.config_proxy import ConfigProxy
from fides.service.messaging.messaging_service import MessagingService
from fides.service.privacy_request.privacy_request_service import (
    PrivacyRequestService,
    _trigger_pre_approval_webhooks,
    handle_approval,
)


class TestHandleApprovalSetsAwaitingPreApproval:
    """Tests that handle_approval transitions to awaiting_pre_approval
    when manual approval is required and pre-approval webhooks exist."""

    @pytest.fixture
    def mock_messaging_service(self) -> MessagingService:
        return create_autospec(MessagingService)

    @pytest.fixture
    def config_proxy(self, db: Session) -> ConfigProxy:
        return ConfigProxy(db)

    @patch(
        "fides.api.models.privacy_request.PrivacyRequest.trigger_pre_approval_webhook"
    )
    def test_handle_approval_sets_awaiting_pre_approval(
        self,
        mock_trigger,
        db: Session,
        config_proxy: ConfigProxy,
        privacy_request_status_pending: PrivacyRequest,
        pre_approval_webhooks: list,
        require_manual_request_approval,
    ):
        """When manual approval is required and pre-approval webhooks exist,
        handle_approval should set the status to awaiting_pre_approval."""
        handle_approval(db, config_proxy, privacy_request_status_pending)

        db.refresh(privacy_request_status_pending)
        assert (
            privacy_request_status_pending.status
            == PrivacyRequestStatus.awaiting_pre_approval
        )
        assert mock_trigger.called

    @patch(
        "fides.api.models.privacy_request.PrivacyRequest.trigger_pre_approval_webhook"
    )
    def test_handle_approval_stays_pending_without_webhooks(
        self,
        mock_trigger,
        db: Session,
        config_proxy: ConfigProxy,
        privacy_request_status_pending: PrivacyRequest,
        require_manual_request_approval,
    ):
        """Without pre-approval webhooks, request stays in pending status."""
        assert db.query(PreApprovalWebhook).count() == 0

        handle_approval(db, config_proxy, privacy_request_status_pending)

        db.refresh(privacy_request_status_pending)
        assert privacy_request_status_pending.status == PrivacyRequestStatus.pending
        assert not mock_trigger.called


class TestTriggerPreApprovalWebhooksAuditLog:
    """Tests that _trigger_pre_approval_webhooks creates an audit log entry."""

    @patch(
        "fides.api.models.privacy_request.PrivacyRequest.trigger_pre_approval_webhook"
    )
    def test_trigger_creates_audit_log(
        self,
        mock_trigger,
        db: Session,
        privacy_request_status_pending: PrivacyRequest,
        pre_approval_webhooks: list,
    ):
        _trigger_pre_approval_webhooks(db, privacy_request_status_pending)

        audit_log = AuditLog.filter(
            db=db,
            conditions=(
                (AuditLog.privacy_request_id == privacy_request_status_pending.id)
                & (AuditLog.action == AuditLogAction.pre_approval_webhook_triggered)
            ),
        ).first()

        assert audit_log is not None
        webhook_names = ", ".join(w.name or w.key for w in pre_approval_webhooks)
        assert audit_log.message == f"Triggered pre-approval webhooks: {webhook_names}"
        audit_log.delete(db)

    @patch(
        "fides.api.models.privacy_request.PrivacyRequest.trigger_pre_approval_webhook"
    )
    def test_trigger_no_audit_log_without_webhooks(
        self,
        mock_trigger,
        db: Session,
        privacy_request_status_pending: PrivacyRequest,
    ):
        """No audit log should be created if there are no pre-approval webhooks."""
        assert db.query(PreApprovalWebhook).count() == 0
        _trigger_pre_approval_webhooks(db, privacy_request_status_pending)

        audit_log = AuditLog.filter(
            db=db,
            conditions=(
                (AuditLog.privacy_request_id == privacy_request_status_pending.id)
                & (AuditLog.action == AuditLogAction.pre_approval_webhook_triggered)
            ),
        ).first()

        assert audit_log is None
        assert not mock_trigger.called


class TestApproveAndDenyFromPreApprovalStatuses:
    """Tests that approve/deny service methods accept new pre-approval statuses."""

    @pytest.fixture
    def mock_messaging_service(self) -> MessagingService:
        return create_autospec(MessagingService)

    @pytest.fixture
    def privacy_request_service(
        self, db: Session, mock_messaging_service: MessagingService
    ) -> PrivacyRequestService:
        return PrivacyRequestService(db, ConfigProxy(db), mock_messaging_service)

    @patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.apply_async"
    )
    def test_approve_from_awaiting_pre_approval(
        self,
        mock_run,
        db: Session,
        privacy_request_service: PrivacyRequestService,
        privacy_request_status_awaiting_pre_approval: PrivacyRequest,
    ):
        result = privacy_request_service.approve_privacy_requests(
            [privacy_request_status_awaiting_pre_approval.id]
        )
        assert len(result.succeeded) == 1
        assert len(result.failed) == 0
        db.refresh(privacy_request_status_awaiting_pre_approval)
        assert (
            privacy_request_status_awaiting_pre_approval.status
            == PrivacyRequestStatus.approved
        )

    @patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.apply_async"
    )
    def test_approve_from_pre_approval_not_eligible(
        self,
        mock_run,
        db: Session,
        privacy_request_service: PrivacyRequestService,
        privacy_request_status_pre_approval_not_eligible: PrivacyRequest,
    ):
        result = privacy_request_service.approve_privacy_requests(
            [privacy_request_status_pre_approval_not_eligible.id]
        )
        assert len(result.succeeded) == 1
        assert len(result.failed) == 0
        db.refresh(privacy_request_status_pre_approval_not_eligible)
        assert (
            privacy_request_status_pre_approval_not_eligible.status
            == PrivacyRequestStatus.approved
        )

    def test_deny_from_awaiting_pre_approval(
        self,
        db: Session,
        privacy_request_service: PrivacyRequestService,
        privacy_request_status_awaiting_pre_approval: PrivacyRequest,
    ):
        result = privacy_request_service.deny_privacy_requests(
            [privacy_request_status_awaiting_pre_approval.id],
            deny_reason="Denied during external review",
        )
        assert len(result.succeeded) == 1
        assert len(result.failed) == 0
        db.refresh(privacy_request_status_awaiting_pre_approval)
        assert (
            privacy_request_status_awaiting_pre_approval.status
            == PrivacyRequestStatus.denied
        )

    def test_deny_from_pre_approval_not_eligible(
        self,
        db: Session,
        privacy_request_service: PrivacyRequestService,
        privacy_request_status_pre_approval_not_eligible: PrivacyRequest,
    ):
        result = privacy_request_service.deny_privacy_requests(
            [privacy_request_status_pre_approval_not_eligible.id],
            deny_reason="Manual review denied",
        )
        assert len(result.succeeded) == 1
        assert len(result.failed) == 0
        db.refresh(privacy_request_status_pre_approval_not_eligible)
        assert (
            privacy_request_status_pre_approval_not_eligible.status
            == PrivacyRequestStatus.denied
        )

    def test_approve_rejects_in_processing_status(
        self,
        db: Session,
        privacy_request_service: PrivacyRequestService,
        privacy_request_status_pending: PrivacyRequest,
    ):
        """Sanity check: in_processing should still be rejected."""
        privacy_request_status_pending.status = PrivacyRequestStatus.in_processing
        privacy_request_status_pending.save(db=db)

        result = privacy_request_service.approve_privacy_requests(
            [privacy_request_status_pending.id]
        )
        assert len(result.succeeded) == 0
        assert len(result.failed) == 1
        assert result.failed[0].message == "Cannot transition status"

    @patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.apply_async"
    )
    def test_approve_with_webhook_id_sets_auto_approve_audit_message(
        self,
        mock_run,
        db: Session,
        privacy_request_service: PrivacyRequestService,
        privacy_request_status_pending: PrivacyRequest,
    ):
        """When webhook_id is provided, the approved audit log should contain
        the auto-approve message."""
        result = privacy_request_service.approve_privacy_requests(
            [privacy_request_status_pending.id],
            webhook_id="some-webhook-id",
        )
        assert len(result.succeeded) == 1

        audit_log = AuditLog.filter(
            db=db,
            conditions=(
                (AuditLog.privacy_request_id == privacy_request_status_pending.id)
                & (AuditLog.action == AuditLogAction.approved)
            ),
        ).first()
        assert audit_log is not None
        assert audit_log.message == "Request auto-approved by pre-approval webhooks"
        audit_log.delete(db)

    @patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.apply_async"
    )
    def test_approve_without_webhook_id_has_empty_audit_message(
        self,
        mock_run,
        db: Session,
        privacy_request_service: PrivacyRequestService,
        privacy_request_status_pending: PrivacyRequest,
    ):
        """When webhook_id is not provided (manual approval), the approved
        audit log message should be empty."""
        result = privacy_request_service.approve_privacy_requests(
            [privacy_request_status_pending.id]
        )
        assert len(result.succeeded) == 1

        audit_log = AuditLog.filter(
            db=db,
            conditions=(
                (AuditLog.privacy_request_id == privacy_request_status_pending.id)
                & (AuditLog.action == AuditLogAction.approved)
            ),
        ).first()
        assert audit_log is not None
        assert audit_log.message == ""
        audit_log.delete(db)
