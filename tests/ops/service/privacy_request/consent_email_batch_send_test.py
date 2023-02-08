from unittest import mock

import pytest
from sqlalchemy.orm import Session

from fides.api.ops.common_exceptions import MessageDispatchException
from fides.api.ops.models.messaging import MessagingConfig
from fides.api.ops.models.policy import CurrentStep, Policy
from fides.api.ops.models.privacy_request import (
    CheckpointActionRequired,
    PrivacyRequest,
    PrivacyRequestStatus,
)
from fides.api.ops.schemas.connection_configuration import ConsentEmailSchema
from fides.api.ops.schemas.connection_configuration.connection_secrets_email_consent import (
    AdvancedSettings,
)
from fides.api.ops.schemas.messaging.messaging import ConsentPreferencesByUser
from fides.api.ops.schemas.privacy_request import Consent
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.privacy_request.consent_email_batch_service import (
    BatchedUserConsentData,
    ConsentEmailExitState,
    add_batched_user_preferences_to_emails,
    restart_privacy_requests_from_post_webhook_send,
    send_consent_email_batch,
    stage_resource_per_connector,
)
from fides.core.config import get_config
from fides.lib.models.audit_log import AuditLog, AuditLogAction
from tests.ops.fixtures.application_fixtures import _create_privacy_request_for_policy

CONFIG = get_config()


def cache_identity_and_consent_preferences(privacy_request, db):
    identity = Identity(email="customer_1#@example.com", ljt_readerID="12345")
    privacy_request.cache_identity(identity)
    privacy_request.consent_preferences = [
        Consent(data_use="advertising", opt_in=False).dict()
    ]
    privacy_request.save(db)


@pytest.fixture(scope="function")
def second_privacy_request_awaiting_consent_email_send(
    db: Session, consent_policy: Policy
) -> PrivacyRequest:
    """Add a second privacy in this state for these tests"""
    privacy_request = _create_privacy_request_for_policy(
        db,
        consent_policy,
    )
    privacy_request.status = PrivacyRequestStatus.awaiting_consent_email_send
    privacy_request.save(db)
    yield privacy_request
    privacy_request.delete(db)


class TestConsentEmailBatchSend:
    @mock.patch(
        "fides.api.ops.service.privacy_request.consent_email_batch_service.send_single_consent_email",
    )
    @mock.patch(
        "fides.api.ops.service.privacy_request.consent_email_batch_service.restart_privacy_requests_from_post_webhook_send",
    )
    def test_send_consent_email_batch_no_applicable_privacy_requests(
        self,
        requeue_privacy_requests,
        send_single_consent_email,
    ) -> None:
        exit_state = send_consent_email_batch.delay().get()
        assert exit_state == ConsentEmailExitState.no_applicable_privacy_requests

        assert not send_single_consent_email.called
        assert not requeue_privacy_requests.called

    @mock.patch(
        "fides.api.ops.service.privacy_request.consent_email_batch_service.send_single_consent_email",
    )
    @mock.patch(
        "fides.api.ops.service.privacy_request.consent_email_batch_service.restart_privacy_requests_from_post_webhook_send",
    )
    @pytest.mark.usefixtures("privacy_request_awaiting_consent_email_send")
    def test_send_consent_email_batch_no_applicable_connectors(
        self,
        requeue_privacy_requests,
        send_single_consent_email,
    ) -> None:
        exit_state = send_consent_email_batch.delay().get()
        assert exit_state == ConsentEmailExitState.no_applicable_connectors

        assert not send_single_consent_email.called
        assert requeue_privacy_requests.called

    @mock.patch(
        "fides.api.ops.service.privacy_request.consent_email_batch_service.send_single_consent_email",
    )
    @mock.patch(
        "fides.api.ops.service.privacy_request.consent_email_batch_service.restart_privacy_requests_from_post_webhook_send",
    )
    @pytest.mark.usefixtures("privacy_request_awaiting_consent_email_send")
    @pytest.mark.usefixtures("sovrn_email_connection_config")
    def test_send_consent_email_batch_missing_identities(
        self,
        requeue_privacy_requests,
        send_single_consent_email,
    ) -> None:
        exit_state = send_consent_email_batch.delay().get()
        assert exit_state == ConsentEmailExitState.missing_required_data

        assert not send_single_consent_email.called
        assert requeue_privacy_requests.called

    @mock.patch(
        "fides.api.ops.service.privacy_request.consent_email_batch_service.send_single_consent_email",
    )
    @mock.patch(
        "fides.api.ops.service.privacy_request.consent_email_batch_service.restart_privacy_requests_from_post_webhook_send",
    )
    @pytest.mark.usefixtures("sovrn_email_connection_config")
    def test_send_consent_email_no_consent_preferences_saved(
        self,
        requeue_privacy_requests,
        send_single_consent_email,
        privacy_request_awaiting_consent_email_send,
    ) -> None:
        identity = Identity(email="customer_1#@example.com", ljt_readerID="12345")
        privacy_request_awaiting_consent_email_send.cache_identity(identity)

        exit_state = send_consent_email_batch.delay().get()
        assert exit_state == ConsentEmailExitState.missing_required_data

        assert not send_single_consent_email.called
        assert requeue_privacy_requests.called

    @mock.patch(
        "fides.api.ops.service.privacy_request.consent_email_batch_service.restart_privacy_requests_from_post_webhook_send",
    )
    @pytest.mark.usefixtures("sovrn_email_connection_config", "test_fides_org")
    def test_send_consent_email_failure(
        self,
        requeue_privacy_requests,
        db,
        privacy_request_awaiting_consent_email_send,
    ) -> None:
        with pytest.raises(MessageDispatchException):
            # Assert there's no messaging config hooked up so this consent email send should fail
            MessagingConfig.get_configuration(
                db=db, service_type=CONFIG.notifications.notification_service_type
            )
        identity = Identity(email="customer_1#@example.com", ljt_readerID="12345")
        privacy_request_awaiting_consent_email_send.cache_identity(identity)
        privacy_request_awaiting_consent_email_send.consent_preferences = [
            Consent(data_use="advertising", opt_in=False).dict()
        ]
        privacy_request_awaiting_consent_email_send.save(db)

        exit_state = send_consent_email_batch.delay().get()
        assert exit_state == ConsentEmailExitState.email_send_failed

        assert not requeue_privacy_requests.called
        email_audit_log: AuditLog = AuditLog.filter(
            db=db,
            conditions=(
                (
                    AuditLog.privacy_request_id
                    == privacy_request_awaiting_consent_email_send.id
                )
                & (AuditLog.action == AuditLogAction.email_sent)
            ),
        ).first()
        assert not email_audit_log

    @mock.patch(
        "fides.api.ops.service.privacy_request.consent_email_batch_service.send_single_consent_email",
    )
    @mock.patch(
        "fides.api.ops.service.privacy_request.consent_email_batch_service.restart_privacy_requests_from_post_webhook_send",
    )
    def test_send_consent_email(
        self,
        requeue_privacy_requests,
        send_single_consent_email,
        db,
        privacy_request_awaiting_consent_email_send,
        second_privacy_request_awaiting_consent_email_send,
        sovrn_email_connection_config,
    ) -> None:
        cache_identity_and_consent_preferences(
            privacy_request_awaiting_consent_email_send, db
        )
        exit_state = send_consent_email_batch.delay().get()
        assert exit_state == ConsentEmailExitState.complete

        assert send_single_consent_email.called
        assert requeue_privacy_requests.called

        call_kwargs = send_single_consent_email.call_args.kwargs

        assert not call_kwargs["db"] == db
        assert call_kwargs["subject_email"] == "sovrn@example.com"
        assert call_kwargs["subject_name"] == "Sovrn"
        assert call_kwargs["required_identities"] == ["ljt_readerID"]
        assert call_kwargs["user_consent_preferences"] == [
            ConsentPreferencesByUser(
                identities={"ljt_readerID": "12345"},
                consent_preferences=[
                    Consent(
                        data_use="advertising", data_use_description=None, opt_in=False
                    )
                ],
            )
        ]
        assert not call_kwargs["test_mode"]

        email_audit_log: AuditLog = AuditLog.filter(
            db=db,
            conditions=(
                (
                    AuditLog.privacy_request_id
                    == privacy_request_awaiting_consent_email_send.id
                )
                & (AuditLog.action == AuditLogAction.email_sent)
            ),
        ).first()
        assert (
            email_audit_log.message
            == f"Consent email instructions dispatched for '{sovrn_email_connection_config.name}'"
        )

        logs_for_privacy_request_without_identity = AuditLog.filter(
            db=db,
            conditions=(
                (
                    AuditLog.privacy_request_id
                    == second_privacy_request_awaiting_consent_email_send.id
                )
                & (AuditLog.action == AuditLogAction.email_sent)
            ),
        ).first()
        assert logs_for_privacy_request_without_identity is None


class TestConsentEmailBatchSendHelperFunctions:
    def test_stage_resource_per_connector(self, sovrn_email_connection_config):
        starting_resources = stage_resource_per_connector(
            [sovrn_email_connection_config]
        )

        assert starting_resources == [
            BatchedUserConsentData(
                connection_secrets=ConsentEmailSchema(
                    third_party_vendor_name="Sovrn",
                    recipient_email_address=sovrn_email_connection_config.secrets[
                        "recipient_email_address"
                    ],
                    test_email_address=sovrn_email_connection_config.secrets[
                        "test_email_address"
                    ],
                    advanced_settings=AdvancedSettings(
                        browser_identity_types=["ljt_readerID"], identity_types=[]
                    ),
                ),
                connection_name=sovrn_email_connection_config.name,
                required_identities=["ljt_readerID"],
            )
        ]

    def test_add_user_preferences_to_email_data(
        self,
        db,
        sovrn_email_connection_config,
        privacy_request_awaiting_consent_email_send,
        second_privacy_request_awaiting_consent_email_send,
    ):
        """Only privacy requests with at least one identity matching
        an identity needed by the connector, and those with consent preferences saved get
        queued up.
        """
        cache_identity_and_consent_preferences(
            privacy_request_awaiting_consent_email_send, db
        )

        starting_resources = stage_resource_per_connector(
            [sovrn_email_connection_config]
        )

        add_batched_user_preferences_to_emails(
            [
                privacy_request_awaiting_consent_email_send,
                second_privacy_request_awaiting_consent_email_send,
            ],
            starting_resources,
        )

        assert starting_resources[0].skipped_privacy_requests == [
            second_privacy_request_awaiting_consent_email_send.id
        ]
        assert starting_resources[0].batched_user_consent_preferences[0].dict() == {
            "identities": {"ljt_readerID": "12345"},
            "consent_preferences": [
                {
                    "data_use": "advertising",
                    "data_use_description": None,
                    "opt_in": False,
                },
            ],
        }

    @mock.patch(
        "fides.api.ops.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_restart_privacy_requests_from_post_webhook_send_temporary_paused_status(
        self,
        run_privacy_request,
        db,
        privacy_request_awaiting_consent_email_send,
    ):
        """Assert privacy request is temporarily put into a paused status and checkpoint is cached."""
        assert (
            privacy_request_awaiting_consent_email_send.status
            == PrivacyRequestStatus.awaiting_consent_email_send
        )

        restart_privacy_requests_from_post_webhook_send(
            [privacy_request_awaiting_consent_email_send], db
        )

        db.refresh(privacy_request_awaiting_consent_email_send)
        assert (
            privacy_request_awaiting_consent_email_send.status
            == PrivacyRequestStatus.paused
        )
        assert (
            privacy_request_awaiting_consent_email_send.get_paused_collection_details()
            == CheckpointActionRequired(
                step=CurrentStep.post_webhooks, collection=None, action_needed=None
            )
        )
        assert run_privacy_request.called

    @mock.patch(
        "fides.api.ops.service.privacy_request.request_runner_service.needs_consent_email_send",
    )
    def test_restart_privacy_requests_from_post_webhook_send(
        self,
        needs_consent_email_send_check,
        db,
        privacy_request_awaiting_consent_email_send,
    ):
        assert (
            privacy_request_awaiting_consent_email_send.status
            == PrivacyRequestStatus.awaiting_consent_email_send
        )

        restart_privacy_requests_from_post_webhook_send(
            [privacy_request_awaiting_consent_email_send], db
        )

        db.refresh(privacy_request_awaiting_consent_email_send)
        assert (
            privacy_request_awaiting_consent_email_send.status
            == PrivacyRequestStatus.complete
        )

        assert (
            not needs_consent_email_send_check.called
        ), "Privacy request is resumed after this point"
