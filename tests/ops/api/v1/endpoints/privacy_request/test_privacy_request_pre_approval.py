"""Tests for pre-approval webhook status transitions, audit log creation, and validation.

Covers:
- Eligible/not-eligible callbacks create audit log entries
- Not-eligible callback transitions status to pre_approval_not_eligible
- Validation accepts awaiting_pre_approval status
- Validation rejects invalid statuses
- Auto-approve when all webhooks respond eligible
- Approve/deny endpoints accept new pre-approval statuses
- Audit log display names in verbose event log
- PATCH connection secrets preserves authorization when only URL is updated
"""

from unittest import mock

import pytest
from starlette.testclient import TestClient

from fides.api.models.audit_log import AuditLog, AuditLogAction
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.pre_approval_webhook import PreApprovalWebhookReply
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.common.api.scope_registry import (
    CONNECTION_CREATE_OR_UPDATE,
    PRIVACY_REQUEST_READ,
    PRIVACY_REQUEST_REVIEW,
)
from fides.common.api.v1.urn_registry import (
    CONNECTION_SECRETS,
    PRIVACY_REQUEST_APPROVE,
    PRIVACY_REQUEST_DENY,
    PRIVACY_REQUEST_PRE_APPROVE_ELIGIBLE,
    PRIVACY_REQUEST_PRE_APPROVE_NOT_ELIGIBLE,
    PRIVACY_REQUESTS,
    V1_URL_PREFIX,
)


class TestMarkEligibleAuditLogAndStatus:
    """Tests that the eligible callback creates audit log entries and handles
    the awaiting_pre_approval status correctly."""

    @pytest.fixture(scope="function")
    def url(self, db, privacy_request_status_pending):
        return V1_URL_PREFIX + PRIVACY_REQUEST_PRE_APPROVE_ELIGIBLE.format(
            privacy_request_id=privacy_request_status_pending.id
        )

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.apply_async"
    )
    @mock.patch(
        "fides.service.messaging.messaging_service.dispatch_message_task.apply_async"
    )
    def test_mark_eligible_creates_audit_log(
        self,
        mock_dispatch_message,
        submit_mock,
        db,
        url,
        api_client,
        privacy_request_status_pending,
        pre_approval_webhooks,
        generate_pre_approval_webhook_auth_header,
    ):
        auth_header = generate_pre_approval_webhook_auth_header(
            webhook=pre_approval_webhooks[1]
        )
        response = api_client.post(url, headers=auth_header)
        assert response.status_code == 200

        eligible_audit_log = AuditLog.filter(
            db=db,
            conditions=(
                (AuditLog.privacy_request_id == privacy_request_status_pending.id)
                & (AuditLog.action == AuditLogAction.pre_approval_eligible)
            ),
        ).first()

        assert eligible_audit_log is not None
        assert (
            f"Pre-approval webhook '{pre_approval_webhooks[1].name}' responded: eligible"
            == eligible_audit_log.message
        )
        eligible_audit_log.delete(db)

    def test_mark_eligible_accepts_awaiting_pre_approval_status(
        self,
        db,
        api_client,
        privacy_request_status_pending,
        pre_approval_webhooks,
        generate_pre_approval_webhook_auth_header,
    ):
        """Validation should accept awaiting_pre_approval status."""
        privacy_request_status_pending.status = (
            PrivacyRequestStatus.awaiting_pre_approval
        )
        privacy_request_status_pending.save(db=db)

        eligible_url = V1_URL_PREFIX + PRIVACY_REQUEST_PRE_APPROVE_ELIGIBLE.format(
            privacy_request_id=privacy_request_status_pending.id
        )
        auth_header = generate_pre_approval_webhook_auth_header(
            webhook=pre_approval_webhooks[1]
        )
        response = api_client.post(eligible_url, headers=auth_header)
        assert response.status_code == 200

    def test_mark_eligible_rejects_approved_status(
        self,
        db,
        api_client,
        privacy_request_status_pending,
        pre_approval_webhooks,
        generate_pre_approval_webhook_auth_header,
    ):
        """Validation should reject approved status."""
        privacy_request_status_pending.status = PrivacyRequestStatus.approved
        privacy_request_status_pending.save(db=db)

        eligible_url = V1_URL_PREFIX + PRIVACY_REQUEST_PRE_APPROVE_ELIGIBLE.format(
            privacy_request_id=privacy_request_status_pending.id
        )
        auth_header = generate_pre_approval_webhook_auth_header(
            webhook=pre_approval_webhooks[1]
        )
        response = api_client.post(eligible_url, headers=auth_header)
        assert response.status_code == 400


class TestMarkNotEligibleAuditLogAndStatus:
    """Tests that the not-eligible callback creates audit log entries and
    transitions the privacy request to pre_approval_not_eligible."""

    @pytest.fixture(scope="function")
    def url(self, db, privacy_request_status_pending):
        return V1_URL_PREFIX + PRIVACY_REQUEST_PRE_APPROVE_NOT_ELIGIBLE.format(
            privacy_request_id=privacy_request_status_pending.id
        )

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.apply_async"
    )
    @mock.patch(
        "fides.service.messaging.messaging_service.dispatch_message_task.apply_async"
    )
    def test_mark_not_eligible_creates_audit_log(
        self,
        mock_dispatch_message,
        submit_mock,
        db,
        url,
        api_client,
        privacy_request_status_pending,
        pre_approval_webhooks,
        generate_pre_approval_webhook_auth_header,
    ):
        auth_header = generate_pre_approval_webhook_auth_header(
            webhook=pre_approval_webhooks[1]
        )
        response = api_client.post(url, headers=auth_header)
        assert response.status_code == 200

        not_eligible_audit_log = AuditLog.filter(
            db=db,
            conditions=(
                (AuditLog.privacy_request_id == privacy_request_status_pending.id)
                & (AuditLog.action == AuditLogAction.pre_approval_not_eligible)
            ),
        ).first()

        assert not_eligible_audit_log is not None
        assert (
            not_eligible_audit_log.message
            == f"Request flagged for manual review by pre-approval webhooks. Webhook '{pre_approval_webhooks[1].name}' responded: not eligible"
        )
        not_eligible_audit_log.delete(db)

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.apply_async"
    )
    @mock.patch(
        "fides.service.messaging.messaging_service.dispatch_message_task.apply_async"
    )
    def test_mark_not_eligible_transitions_to_pre_approval_not_eligible(
        self,
        mock_dispatch_message,
        submit_mock,
        db,
        url,
        api_client,
        privacy_request_status_pending,
        pre_approval_webhooks,
        generate_pre_approval_webhook_auth_header,
    ):
        auth_header = generate_pre_approval_webhook_auth_header(
            webhook=pre_approval_webhooks[1]
        )
        response = api_client.post(url, headers=auth_header)
        assert response.status_code == 200

        db.refresh(privacy_request_status_pending)
        assert (
            privacy_request_status_pending.status
            == PrivacyRequestStatus.pre_approval_not_eligible
        )

    def test_mark_not_eligible_accepts_awaiting_pre_approval_status(
        self,
        db,
        api_client,
        privacy_request_status_pending,
        pre_approval_webhooks,
        generate_pre_approval_webhook_auth_header,
    ):
        """Validation should accept awaiting_pre_approval status."""
        privacy_request_status_pending.status = (
            PrivacyRequestStatus.awaiting_pre_approval
        )
        privacy_request_status_pending.save(db=db)

        not_eligible_url = (
            V1_URL_PREFIX
            + PRIVACY_REQUEST_PRE_APPROVE_NOT_ELIGIBLE.format(
                privacy_request_id=privacy_request_status_pending.id
            )
        )
        auth_header = generate_pre_approval_webhook_auth_header(
            webhook=pre_approval_webhooks[1]
        )
        response = api_client.post(not_eligible_url, headers=auth_header)
        assert response.status_code == 200

        db.refresh(privacy_request_status_pending)
        assert (
            privacy_request_status_pending.status
            == PrivacyRequestStatus.pre_approval_not_eligible
        )

    def test_mark_not_eligible_rejects_approved_status(
        self,
        db,
        api_client,
        privacy_request_status_pending,
        pre_approval_webhooks,
        generate_pre_approval_webhook_auth_header,
    ):
        """Validation should reject approved status."""
        privacy_request_status_pending.status = PrivacyRequestStatus.approved
        privacy_request_status_pending.save(db=db)

        not_eligible_url = (
            V1_URL_PREFIX
            + PRIVACY_REQUEST_PRE_APPROVE_NOT_ELIGIBLE.format(
                privacy_request_id=privacy_request_status_pending.id
            )
        )
        auth_header = generate_pre_approval_webhook_auth_header(
            webhook=pre_approval_webhooks[1]
        )
        response = api_client.post(not_eligible_url, headers=auth_header)
        assert response.status_code == 400


class TestAutoApproveWhenAllWebhooksEligible:
    """Tests the full auto-approve flow: when all pre-approval webhooks respond
    eligible, the privacy request is automatically approved."""

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.apply_async"
    )
    @mock.patch(
        "fides.service.messaging.messaging_service.dispatch_message_task.apply_async"
    )
    def test_auto_approve_when_all_webhooks_respond_eligible(
        self,
        mock_dispatch_message,
        submit_mock,
        db,
        api_client,
        privacy_request_status_pending,
        pre_approval_webhooks,
        generate_pre_approval_webhook_auth_header,
    ):
        """When replies from all configured webhooks are eligible, the request
        should be automatically approved and an approved audit log created."""
        # Pre-create an eligible reply for the first webhook
        first_reply = PreApprovalWebhookReply.create(
            db=db,
            data={
                "webhook_id": pre_approval_webhooks[0].id,
                "privacy_request_id": privacy_request_status_pending.id,
                "is_eligible": True,
            },
        )

        # Call the eligible endpoint for the second webhook
        eligible_url = V1_URL_PREFIX + PRIVACY_REQUEST_PRE_APPROVE_ELIGIBLE.format(
            privacy_request_id=privacy_request_status_pending.id
        )
        auth_header = generate_pre_approval_webhook_auth_header(
            webhook=pre_approval_webhooks[1]
        )
        response = api_client.post(eligible_url, headers=auth_header)
        assert response.status_code == 200

        # Privacy request should now be approved
        db.refresh(privacy_request_status_pending)
        assert privacy_request_status_pending.status == PrivacyRequestStatus.approved

        # An approved audit log with the auto-approve message should exist
        approved_audit_log = AuditLog.filter(
            db=db,
            conditions=(
                (AuditLog.privacy_request_id == privacy_request_status_pending.id)
                & (AuditLog.action == AuditLogAction.approved)
            ),
        ).first()
        assert approved_audit_log is not None
        assert (
            approved_audit_log.message
            == "Request auto-approved by pre-approval webhooks"
        )

        # Cleanup
        first_reply.delete(db)
        approved_audit_log.delete(db)

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.apply_async"
    )
    @mock.patch(
        "fides.service.messaging.messaging_service.dispatch_message_task.apply_async"
    )
    def test_no_auto_approve_when_not_all_webhooks_responded(
        self,
        mock_dispatch_message,
        submit_mock,
        db,
        api_client,
        privacy_request_status_pending,
        pre_approval_webhooks,
        generate_pre_approval_webhook_auth_header,
    ):
        """When only some webhooks have responded, the request should NOT be
        auto-approved."""
        # Call the eligible endpoint for only the second webhook (no reply from first)
        eligible_url = V1_URL_PREFIX + PRIVACY_REQUEST_PRE_APPROVE_ELIGIBLE.format(
            privacy_request_id=privacy_request_status_pending.id
        )
        auth_header = generate_pre_approval_webhook_auth_header(
            webhook=pre_approval_webhooks[1]
        )
        response = api_client.post(eligible_url, headers=auth_header)
        assert response.status_code == 200

        # Privacy request should still be pending (not auto-approved)
        db.refresh(privacy_request_status_pending)
        assert privacy_request_status_pending.status == PrivacyRequestStatus.pending


class TestAuditLogDisplayNamesInEventLog:
    """Tests that audit log entries for pre-approval actions are displayed
    with user-friendly names in the verbose event log response."""

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.apply_async"
    )
    @mock.patch(
        "fides.service.messaging.messaging_service.dispatch_message_task.apply_async"
    )
    def test_pre_approval_audit_logs_use_display_names(
        self,
        mock_dispatch_message,
        submit_mock,
        db,
        api_client,
        generate_auth_header,
        privacy_request_status_pending,
    ):
        """Verbose event log should map pre-approval audit log actions to
        user-friendly display names rather than raw status strings."""
        # Create audit logs for each pre-approval action type
        audit_logs = []
        for action, expected_display_name in [
            (
                AuditLogAction.pre_approval_webhook_triggered,
                "Triggered pre-approval webhooks",
            ),
            (
                AuditLogAction.pre_approval_eligible,
                "Request auto-approved by pre-approval webhooks",
            ),
            (
                AuditLogAction.pre_approval_not_eligible,
                "Request flagged for manual review by pre-approval webhooks",
            ),
        ]:
            audit_log = AuditLog.create(
                db=db,
                data={
                    "privacy_request_id": privacy_request_status_pending.id,
                    "action": action,
                    "message": f"Test message for {action.value}",
                },
            )
            audit_logs.append((audit_log, expected_display_name))

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(
            V1_URL_PREFIX + PRIVACY_REQUESTS,
            headers=auth_header,
            params={
                "request_id": privacy_request_status_pending.id,
                "verbose": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        items = data["items"]
        assert len(items) == 1

        results = items[0].get("results", {})
        dataset_names = list(results.keys())

        for _audit_log, expected_display_name in audit_logs:
            assert expected_display_name in dataset_names, (
                f"Expected display name '{expected_display_name}' "
                f"not found in dataset names: {dataset_names}"
            )

        # Cleanup
        for audit_log, _ in audit_logs:
            audit_log.delete(db)


class TestApproveFromPreApprovalStatuses:
    """Tests that approve endpoint accepts pre-approval statuses."""

    @pytest.fixture(scope="function")
    def url(self):
        return V1_URL_PREFIX + PRIVACY_REQUEST_APPROVE

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.apply_async"
    )
    @mock.patch(
        "fides.service.messaging.messaging_service.dispatch_message_task.apply_async"
    )
    def test_approve_from_awaiting_pre_approval(
        self,
        mock_dispatch_message,
        submit_mock,
        db,
        url,
        api_client: TestClient,
        generate_auth_header,
        privacy_request_status_awaiting_pre_approval,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_REVIEW])
        response = api_client.patch(
            url,
            headers=auth_header,
            json={"request_ids": [privacy_request_status_awaiting_pre_approval.id]},
        )
        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data["succeeded"]) == 1
        assert len(response_data["failed"]) == 0
        assert (
            response_data["succeeded"][0]["status"]
            == PrivacyRequestStatus.approved.value
        )

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.apply_async"
    )
    @mock.patch(
        "fides.service.messaging.messaging_service.dispatch_message_task.apply_async"
    )
    def test_approve_from_pre_approval_not_eligible(
        self,
        mock_dispatch_message,
        submit_mock,
        db,
        url,
        api_client: TestClient,
        generate_auth_header,
        privacy_request_status_pre_approval_not_eligible,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_REVIEW])
        response = api_client.patch(
            url,
            headers=auth_header,
            json={"request_ids": [privacy_request_status_pre_approval_not_eligible.id]},
        )
        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data["succeeded"]) == 1
        assert len(response_data["failed"]) == 0
        assert (
            response_data["succeeded"][0]["status"]
            == PrivacyRequestStatus.approved.value
        )


class TestDenyFromPreApprovalStatuses:
    """Tests that deny endpoint accepts pre-approval statuses."""

    @pytest.fixture(scope="function")
    def url(self):
        return V1_URL_PREFIX + PRIVACY_REQUEST_DENY

    def test_deny_from_awaiting_pre_approval(
        self,
        db,
        url,
        api_client: TestClient,
        generate_auth_header,
        privacy_request_status_awaiting_pre_approval,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_REVIEW])
        response = api_client.patch(
            url,
            headers=auth_header,
            json={
                "request_ids": [privacy_request_status_awaiting_pre_approval.id],
                "reason": "Denied during external review",
            },
        )
        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data["succeeded"]) == 1
        assert len(response_data["failed"]) == 0
        assert (
            response_data["succeeded"][0]["status"] == PrivacyRequestStatus.denied.value
        )

    def test_deny_from_pre_approval_not_eligible(
        self,
        db,
        url,
        api_client: TestClient,
        generate_auth_header,
        privacy_request_status_pre_approval_not_eligible,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_REVIEW])
        response = api_client.patch(
            url,
            headers=auth_header,
            json={
                "request_ids": [privacy_request_status_pre_approval_not_eligible.id],
                "reason": "Manual review denied",
            },
        )
        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data["succeeded"]) == 1
        assert len(response_data["failed"]) == 0
        assert (
            response_data["succeeded"][0]["status"] == PrivacyRequestStatus.denied.value
        )


class TestPatchConnectionSecretsPreservesAuthorization:
    """Tests that PATCHing connection secrets with only a URL update
    preserves the existing authorization value."""

    def test_patch_secrets_url_only_preserves_authorization(
        self,
        db,
        api_client,
        generate_auth_header,
        https_connection_config,
    ):
        """When editing a webhook's URL without changing the authorization,
        a PATCH with only the url field should preserve the existing auth."""
        original_auth = https_connection_config.secrets["authorization"]
        new_url = "http://new-endpoint.example.com/webhook"

        secrets_url = (
            V1_URL_PREFIX
            + CONNECTION_SECRETS.format(connection_key=https_connection_config.key)
            + "?verify=false"
        )
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        response = api_client.patch(
            secrets_url,
            headers=auth_header,
            json={"url": new_url},
        )
        assert response.status_code == 200

        db.refresh(https_connection_config)
        assert https_connection_config.secrets["url"] == new_url
        assert https_connection_config.secrets["authorization"] == original_auth

    def test_patch_secrets_url_and_authorization_updates_both(
        self,
        db,
        api_client,
        generate_auth_header,
        https_connection_config,
    ):
        """When both url and authorization are provided, both should be updated."""
        new_url = "http://updated.example.com/webhook"
        new_auth = "new_secret_token"

        secrets_url = (
            V1_URL_PREFIX
            + CONNECTION_SECRETS.format(connection_key=https_connection_config.key)
            + "?verify=false"
        )
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        response = api_client.patch(
            secrets_url,
            headers=auth_header,
            json={"url": new_url, "authorization": new_auth},
        )
        assert response.status_code == 200

        db.refresh(https_connection_config)
        assert https_connection_config.secrets["url"] == new_url
        assert https_connection_config.secrets["authorization"] == new_auth

    def test_put_secrets_without_authorization_fails(
        self,
        api_client,
        generate_auth_header,
        https_connection_config,
    ):
        """PUT requires all fields -- omitting authorization should fail."""
        secrets_url = (
            V1_URL_PREFIX
            + CONNECTION_SECRETS.format(connection_key=https_connection_config.key)
            + "?verify=false"
        )
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        response = api_client.put(
            secrets_url,
            headers=auth_header,
            json={"url": "http://example.com/webhook"},
        )
        assert response.status_code == 422
