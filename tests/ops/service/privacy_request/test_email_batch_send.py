from unittest import mock

import pytest
from sqlalchemy.orm import Session

from fides.api.ops.common_exceptions import MessageDispatchException
from fides.api.ops.models.messaging import MessagingConfig
from fides.api.ops.models.policy import Policy
from fides.api.ops.models.privacy_request import (
    ExecutionLog,
    ExecutionLogStatus,
    PrivacyRequest,
    PrivacyRequestStatus,
)
from fides.api.ops.schemas.messaging.messaging import ConsentPreferencesByUser
from fides.api.ops.schemas.privacy_request import Consent
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.privacy_request.email_batch_service import (
    EmailExitState,
    send_email_batch,
)
from fides.core.config import get_config
from tests.fixtures.application_fixtures import _create_privacy_request_for_policy

CONFIG = get_config()


def cache_identity_and_consent_preferences(privacy_request, db, reader_id):
    identity = Identity(email="customer_1#@example.com", ljt_readerID=reader_id)
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
    privacy_request.status = PrivacyRequestStatus.awaiting_email_send
    privacy_request.save(db)
    yield privacy_request
    privacy_request.delete(db)


@pytest.fixture(scope="function")
def second_privacy_request_awaiting_erasure_email_send(
    db: Session, erasure_policy: Policy
) -> PrivacyRequest:
    """Add a second privacy in this state for these tests"""
    privacy_request = _create_privacy_request_for_policy(
        db, erasure_policy, email_identity="test2@example.com"
    )
    privacy_request.status = PrivacyRequestStatus.awaiting_email_send
    privacy_request.save(db)
    yield privacy_request
    privacy_request.delete(db)


class TestConsentEmailBatchSend:
    @mock.patch(
        "fides.api.ops.service.connectors.consent_email_connector.send_single_consent_email",
    )
    @mock.patch(
        "fides.api.ops.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
    )
    def test_send_email_batch_no_applicable_privacy_requests(
        self,
        requeue_privacy_requests,
        send_single_consent_email,
    ) -> None:
        exit_state = send_email_batch.delay().get()
        assert exit_state == EmailExitState.no_applicable_privacy_requests

        assert not send_single_consent_email.called
        assert not requeue_privacy_requests.called

    @mock.patch(
        "fides.api.ops.service.connectors.consent_email_connector.send_single_consent_email",
    )
    @mock.patch(
        "fides.api.ops.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
    )
    @pytest.mark.usefixtures("privacy_request_awaiting_consent_email_send")
    def test_send_email_batch_no_applicable_connectors(
        self,
        requeue_privacy_requests,
        send_single_consent_email,
    ) -> None:
        exit_state = send_email_batch.delay().get()
        assert exit_state == EmailExitState.no_applicable_connectors

        assert not send_single_consent_email.called
        assert requeue_privacy_requests.called

    @mock.patch(
        "fides.api.ops.service.connectors.consent_email_connector.send_single_consent_email",
    )
    @mock.patch(
        "fides.api.ops.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
    )
    @pytest.mark.usefixtures("privacy_request_awaiting_consent_email_send")
    @pytest.mark.usefixtures("sovrn_email_connection_config")
    def test_send_email_batch_missing_identities(
        self,
        requeue_privacy_requests,
        send_single_consent_email,
    ) -> None:
        exit_state = send_email_batch.delay().get()
        assert exit_state == EmailExitState.complete

        assert not send_single_consent_email.called
        assert requeue_privacy_requests.called

    @mock.patch(
        "fides.api.ops.service.connectors.consent_email_connector.send_single_consent_email",
    )
    @mock.patch(
        "fides.api.ops.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
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

        exit_state = send_email_batch.delay().get()
        assert exit_state == EmailExitState.complete

        assert not send_single_consent_email.called
        assert requeue_privacy_requests.called

    @mock.patch(
        "fides.api.ops.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
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

        exit_state = send_email_batch.delay().get()
        assert exit_state == EmailExitState.email_send_failed

        assert not requeue_privacy_requests.called
        email_execution_log: ExecutionLog = ExecutionLog.filter(
            db=db,
            conditions=(
                (
                    ExecutionLog.privacy_request_id
                    == privacy_request_awaiting_consent_email_send.id
                )
                & (ExecutionLog.status == ExecutionLogStatus.complete)
            ),
        ).first()
        assert not email_execution_log

    @mock.patch(
        "fides.api.ops.service.connectors.consent_email_connector.send_single_consent_email",
    )
    @mock.patch(
        "fides.api.ops.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
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
            privacy_request_awaiting_consent_email_send, db, "12345"
        )
        exit_state = send_email_batch.delay().get()
        assert exit_state == EmailExitState.complete

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

        email_execution_log: ExecutionLog = ExecutionLog.filter(
            db=db,
            conditions=(
                (
                    ExecutionLog.privacy_request_id
                    == privacy_request_awaiting_consent_email_send.id
                )
                & (ExecutionLog.status == ExecutionLogStatus.complete)
            ),
        ).first()
        assert (
            email_execution_log.message
            == f"Consent email instructions dispatched for '{sovrn_email_connection_config.name}'"
        )

        logs_for_privacy_request_without_identity = ExecutionLog.filter(
            db=db,
            conditions=(
                (
                    ExecutionLog.privacy_request_id
                    == second_privacy_request_awaiting_consent_email_send.id
                )
                & (ExecutionLog.status == ExecutionLogStatus.complete)
            ),
        ).first()
        assert logs_for_privacy_request_without_identity is None

    @mock.patch(
        "fides.api.ops.service.connectors.consent_email_connector.send_single_consent_email",
    )
    @mock.patch(
        "fides.api.ops.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
    )
    def test_send_consent_email_multiple_users(
        self,
        requeue_privacy_requests,
        send_single_consent_email,
        db,
        privacy_request_awaiting_consent_email_send,
        second_privacy_request_awaiting_consent_email_send,
        sovrn_email_connection_config,
    ) -> None:
        cache_identity_and_consent_preferences(
            privacy_request_awaiting_consent_email_send, db, "12345"
        )
        cache_identity_and_consent_preferences(
            second_privacy_request_awaiting_consent_email_send, db, "abcde"
        )
        exit_state = send_email_batch.delay().get()
        assert exit_state == EmailExitState.complete

        assert send_single_consent_email.called
        assert requeue_privacy_requests.called

        call_kwargs = send_single_consent_email.call_args.kwargs

        user_consent_preferences = call_kwargs["user_consent_preferences"]
        assert {"12345", "abcde"} == {
            consent_pref.identities["ljt_readerID"]
            for consent_pref in user_consent_preferences
        }
        assert not call_kwargs["test_mode"]

        email_execution_log: ExecutionLog = ExecutionLog.filter(
            db=db,
            conditions=(
                (
                    ExecutionLog.privacy_request_id
                    == privacy_request_awaiting_consent_email_send.id
                )
                & (ExecutionLog.status == ExecutionLogStatus.complete)
            ),
        ).first()
        assert (
            email_execution_log.message
            == f"Consent email instructions dispatched for '{sovrn_email_connection_config.name}'"
        )

        second_privacy_request_log = ExecutionLog.filter(
            db=db,
            conditions=(
                (
                    ExecutionLog.privacy_request_id
                    == second_privacy_request_awaiting_consent_email_send.id
                )
                & (ExecutionLog.status == ExecutionLogStatus.complete)
            ),
        ).first()
        assert (
            second_privacy_request_log.message
            == f"Consent email instructions dispatched for '{sovrn_email_connection_config.name}'"
        )


class TestErasureEmailBatchSend:
    @mock.patch(
        "fides.api.ops.service.connectors.erasure_email_connector.send_single_erasure_email",
    )
    @mock.patch(
        "fides.api.ops.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
    )
    def test_send_email_batch_no_applicable_privacy_requests(
        self,
        requeue_privacy_requests,
        send_single_erasure_email,
    ) -> None:
        exit_state = send_email_batch.delay().get()
        assert exit_state == EmailExitState.no_applicable_privacy_requests

        assert not send_single_erasure_email.called
        assert not requeue_privacy_requests.called

    @mock.patch(
        "fides.api.ops.service.connectors.erasure_email_connector.send_single_erasure_email",
    )
    @mock.patch(
        "fides.api.ops.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
    )
    @pytest.mark.usefixtures("privacy_request_awaiting_consent_email_send")
    def test_send_email_batch_no_applicable_connectors(
        self,
        requeue_privacy_requests,
        send_single_erasure_email,
    ) -> None:
        exit_state = send_email_batch.delay().get()
        assert exit_state == EmailExitState.no_applicable_connectors

        assert not send_single_erasure_email.called
        assert requeue_privacy_requests.called

    @mock.patch(
        "fides.api.ops.service.connectors.erasure_email_connector.send_single_erasure_email",
    )
    @mock.patch(
        "fides.api.ops.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
    )
    @pytest.mark.usefixtures("privacy_request_awaiting_consent_email_send")
    @pytest.mark.usefixtures("attentive_email_connection_config")
    def test_send_email_batch_missing_identities(
        self,
        requeue_privacy_requests,
        send_single_erasure_email,
    ) -> None:
        exit_state = send_email_batch.delay().get()
        assert exit_state == EmailExitState.complete

        assert not send_single_erasure_email.called
        assert requeue_privacy_requests.called

    @mock.patch(
        "fides.api.ops.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
    )
    @pytest.mark.usefixtures("attentive_email_connection_config", "test_fides_org")
    def test_send_erasure_email_failure(
        self,
        requeue_privacy_requests,
        db,
        privacy_request_awaiting_erasure_email_send,
    ) -> None:
        with pytest.raises(MessageDispatchException):
            # Assert there's no messaging config hooked up so this consent email send should fail
            MessagingConfig.get_configuration(
                db=db, service_type=CONFIG.notifications.notification_service_type
            )
        identity = Identity(email="customer_1#@example.com")
        privacy_request_awaiting_erasure_email_send.cache_identity(identity)
        privacy_request_awaiting_erasure_email_send.save(db)

        exit_state = send_email_batch.delay().get()
        assert exit_state == EmailExitState.email_send_failed

        assert not requeue_privacy_requests.called
        email_execution_log: ExecutionLog = ExecutionLog.filter(
            db=db,
            conditions=(
                (
                    ExecutionLog.privacy_request_id
                    == privacy_request_awaiting_erasure_email_send.id
                )
                & (ExecutionLog.status == ExecutionLogStatus.complete)
            ),
        ).first()
        assert not email_execution_log

    @mock.patch(
        "fides.api.ops.service.connectors.erasure_email_connector.send_single_erasure_email",
    )
    @mock.patch(
        "fides.api.ops.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
    )
    def test_send_erasure_email(
        self,
        requeue_privacy_requests,
        send_single_erasure_email,
        db,
        privacy_request_awaiting_erasure_email_send,
        second_privacy_request_awaiting_consent_email_send,
        attentive_email_connection_config,
    ) -> None:
        """
        Test for batch erasure email, also verifies that a privacy request
        queued for a consent email doesn't trigger an erasure email.
        """

        exit_state = send_email_batch.delay().get()
        assert exit_state == EmailExitState.complete

        assert send_single_erasure_email.called
        assert requeue_privacy_requests.called

        call_kwargs = send_single_erasure_email.call_args.kwargs

        assert not call_kwargs["db"] == db
        assert call_kwargs["subject_email"] == "attentive@example.com"
        assert call_kwargs["subject_name"] == "Attentive"
        assert call_kwargs["batch_identities"] == [
            "test@example.com",
        ]
        assert not call_kwargs["test_mode"]

        email_execution_log: ExecutionLog = ExecutionLog.filter(
            db=db,
            conditions=(
                (
                    ExecutionLog.privacy_request_id
                    == privacy_request_awaiting_erasure_email_send.id
                )
                & (ExecutionLog.status == ExecutionLogStatus.complete)
            ),
        ).first()
        assert (
            email_execution_log.message
            == f"Erasure email instructions dispatched for {attentive_email_connection_config.name}"
        )

        logs_for_privacy_request_without_identity = ExecutionLog.filter(
            db=db,
            conditions=(
                (
                    ExecutionLog.privacy_request_id
                    == second_privacy_request_awaiting_consent_email_send.id
                )
                & (ExecutionLog.status == ExecutionLogStatus.complete)
            ),
        ).first()
        assert logs_for_privacy_request_without_identity is None

    @mock.patch(
        "fides.api.ops.service.connectors.erasure_email_connector.send_single_erasure_email",
    )
    @mock.patch(
        "fides.api.ops.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
    )
    def test_send_erasure_email_multiple_users(
        self,
        requeue_privacy_requests,
        send_single_erasure_email,
        db,
        privacy_request_awaiting_erasure_email_send,
        second_privacy_request_awaiting_erasure_email_send,
        attentive_email_connection_config,
    ) -> None:
        exit_state = send_email_batch.delay().get()
        assert exit_state == EmailExitState.complete

        assert send_single_erasure_email.called
        assert requeue_privacy_requests.called

        call_kwargs = send_single_erasure_email.call_args.kwargs

        assert not call_kwargs["test_mode"]
        assert call_kwargs["batch_identities"] == [
            "test@example.com",
            "test2@example.com",
        ]

        email_execution_log: ExecutionLog = ExecutionLog.filter(
            db=db,
            conditions=(
                (
                    ExecutionLog.privacy_request_id
                    == privacy_request_awaiting_erasure_email_send.id
                )
                & (ExecutionLog.status == ExecutionLogStatus.complete)
            ),
        ).first()
        assert (
            email_execution_log.message
            == f"Erasure email instructions dispatched for {attentive_email_connection_config.name}"
        )

        second_privacy_request_log = ExecutionLog.filter(
            db=db,
            conditions=(
                (
                    ExecutionLog.privacy_request_id
                    == second_privacy_request_awaiting_erasure_email_send.id
                )
                & (ExecutionLog.status == ExecutionLogStatus.complete)
            ),
        ).first()
        assert (
            second_privacy_request_log.message
            == f"Erasure email instructions dispatched for {attentive_email_connection_config.name}"
        )
