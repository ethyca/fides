from unittest import mock

import pytest
from sqlalchemy.orm import Session

from fides.api.common_exceptions import MessageDispatchException
from fides.api.models.messaging import MessagingConfig
from fides.api.models.policy import ActionType, Policy
from fides.api.models.privacy_preference import UserConsentPreference
from fides.api.models.privacy_request import ExecutionLog, PrivacyRequest
from fides.api.schemas.messaging.messaging import ConsentPreferencesByUser
from fides.api.schemas.privacy_notice import PrivacyNoticeHistorySchema
from fides.api.schemas.privacy_preference import MinimalPrivacyPreferenceHistorySchema
from fides.api.schemas.privacy_request import Consent, ExecutionLogStatus
from fides.api.schemas.redis_cache import Identity
from fides.api.service.privacy_request.email_batch_service import (
    EmailExitState,
    send_email_batch,
)
from fides.api.util.cache import get_all_cache_keys_for_privacy_request, get_cache
from fides.config import get_config
from tests.fixtures.application_fixtures import _create_privacy_request_for_policy

CONFIG = get_config()


def cache_identity_and_consent_preferences(privacy_request, db, reader_id):
    identity = Identity(email="customer_1#@example.com", ljt_readerID=reader_id)
    privacy_request.cache_identity(identity)
    privacy_request.consent_preferences = [
        Consent(data_use="marketing.advertising", opt_in=False).model_dump(mode="json")
    ]
    privacy_request.save(db)


def cache_identity_and_privacy_preferences(
    privacy_request, db, reader_id, privacy_preference_history
):
    identity = Identity(email="customer_1#@example.com", ljt_readerID=reader_id)
    privacy_request.cache_identity(identity)
    privacy_preference_history.privacy_request_id = privacy_request.id
    privacy_preference_history.save(db)


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


@pytest.fixture(scope="function")
def third_privacy_request_awaiting_erasure_email_send(
    db: Session, erasure_policy: Policy
) -> PrivacyRequest:
    """Add a third erasure privacy request w/ no identity in this state for these tests"""
    privacy_request = _create_privacy_request_for_policy(
        db,
        erasure_policy,
    )
    privacy_request.status = PrivacyRequestStatus.awaiting_email_send
    privacy_request.save(db)
    yield privacy_request
    privacy_request.delete(db)


class TestConsentEmailBatchSend:
    @mock.patch(
        "fides.api.service.connectors.consent_email_connector.send_single_consent_email",
    )
    @mock.patch(
        "fides.api.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
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
        "fides.api.service.connectors.consent_email_connector.send_single_consent_email",
    )
    @mock.patch(
        "fides.api.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
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
        "fides.api.service.connectors.consent_email_connector.send_single_consent_email",
    )
    @mock.patch(
        "fides.api.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
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
        "fides.api.service.connectors.consent_email_connector.send_single_consent_email",
    )
    @mock.patch(
        "fides.api.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
    )
    @pytest.mark.usefixtures("sovrn_email_connection_config")
    def test_send_consent_email_no_consent_or_privacy_preferences_saved(
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
        "fides.api.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
    )
    @pytest.mark.usefixtures("sovrn_email_connection_config", "test_fides_org")
    def test_send_consent_email_failure_old_workflow(
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
            Consent(data_use="marketing.advertising", opt_in=False).model_dump(
                mode="json"
            )
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
        "fides.api.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
    )
    @pytest.mark.usefixtures("test_fides_org")
    def test_send_consent_email_failure_new_workflow(
        self,
        requeue_privacy_requests,
        db,
        privacy_request_awaiting_consent_email_send,
        privacy_preference_history,
        privacy_preference_history_us_ca_provide,
        sovrn_email_connection_config,
        system,
    ) -> None:
        sovrn_email_connection_config.system_id = system.id
        sovrn_email_connection_config.save(db)

        with pytest.raises(MessageDispatchException):
            # Assert there's no messaging config hooked up so this consent email send should fail
            MessagingConfig.get_configuration(
                db=db, service_type=CONFIG.notifications.notification_service_type
            )
        identity = Identity(email="customer_1#@example.com", ljt_readerID="12345")
        privacy_request_awaiting_consent_email_send.cache_identity(identity)
        # This preference matches on data use
        privacy_preference_history.privacy_request_id = (
            privacy_request_awaiting_consent_email_send.id
        )
        privacy_preference_history.save(db)

        # This preference does not match on data use
        privacy_preference_history_us_ca_provide.privacy_request_id = (
            privacy_request_awaiting_consent_email_send.id
        )
        privacy_preference_history_us_ca_provide.save(db)

        exit_state = send_email_batch.delay().get()
        assert exit_state == EmailExitState.email_send_failed

        assert not requeue_privacy_requests.called
        execution_logs: ExecutionLog = ExecutionLog.filter(
            db=db,
            conditions=(
                (
                    ExecutionLog.privacy_request_id
                    == privacy_request_awaiting_consent_email_send.id
                )
            ),
        )
        assert execution_logs.count() == 1
        assert execution_logs[0].status == ExecutionLogStatus.error

        db.refresh(privacy_preference_history)
        # Sovrn error status and identities added to affected systems and secondary user ids because this preference is relevant
        assert (
            privacy_preference_history.affected_system_status[
                sovrn_email_connection_config.system_key
            ]
            == "error"
        )
        assert privacy_preference_history.secondary_user_ids == {
            "ljt_readerID": "12345"
        }

        db.refresh(privacy_preference_history_us_ca_provide)
        # Sovrn error status and identities not added to affected systems and secondary user ids for irrelevant preference
        assert (
            privacy_preference_history_us_ca_provide.affected_system_status[
                sovrn_email_connection_config.system_key
            ]
            == "skipped"
        )
        assert not privacy_preference_history_us_ca_provide.secondary_user_ids

    @mock.patch(
        "fides.api.service.connectors.consent_email_connector.send_single_consent_email",
    )
    @mock.patch(
        "fides.api.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
    )
    def test_send_consent_email_old_workflow(
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
                        data_use="marketing.advertising",
                        data_use_description=None,
                        opt_in=False,
                    )
                ],
                privacy_preferences=[],
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
        "fides.api.service.connectors.consent_email_connector.send_single_consent_email",
    )
    @mock.patch(
        "fides.api.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
    )
    def test_send_generic_consent_email_old_workflow(
        self,
        requeue_privacy_requests,
        send_single_consent_email,
        db,
        privacy_request_awaiting_consent_email_send,
        second_privacy_request_awaiting_consent_email_send,
        generic_consent_email_connection_config,
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
                        data_use="marketing.advertising",
                        data_use_description=None,
                        opt_in=False,
                    )
                ],
                privacy_preferences=[],
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
            == f"Consent email instructions dispatched for '{generic_consent_email_connection_config.name}'"
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
        "fides.api.service.connectors.consent_email_connector.send_single_consent_email",
    )
    @mock.patch(
        "fides.api.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
    )
    def test_send_consent_email_skipped_logs_due_to_data_use_mismatch(
        self,
        requeue_privacy_requests,
        send_single_consent_email,
        db,
        privacy_request_awaiting_consent_email_send,
        sovrn_email_connection_config,
        privacy_preference_history_us_ca_provide,
        system,
    ) -> None:
        sovrn_email_connection_config.system_id = system.id
        sovrn_email_connection_config.save(db)

        cache_identity_and_privacy_preferences(
            privacy_request_awaiting_consent_email_send,
            db,
            "12345",
            privacy_preference_history_us_ca_provide,
        )
        exit_state = send_email_batch.delay().get()
        assert exit_state == EmailExitState.complete

        assert not send_single_consent_email.called
        assert requeue_privacy_requests.called

        email_execution_logs: ExecutionLog = ExecutionLog.filter(
            db=db,
            conditions=(
                (
                    ExecutionLog.privacy_request_id
                    == privacy_request_awaiting_consent_email_send.id
                )
            ),
        )
        assert email_execution_logs.count() == 1
        assert email_execution_logs[0].status == ExecutionLogStatus.skipped

        db.refresh(privacy_preference_history_us_ca_provide)
        # Entire privacy request is skipped, so "skipped" system logs are added in a different location then if
        # some preferences are propagated and others are not.
        assert (
            privacy_preference_history_us_ca_provide.affected_system_status[
                sovrn_email_connection_config.system_key
            ]
            == "skipped"
        )
        assert not privacy_preference_history_us_ca_provide.secondary_user_ids

    @mock.patch(
        "fides.api.service.connectors.consent_email_connector.send_single_consent_email",
    )
    @mock.patch(
        "fides.api.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
    )
    def test_send_consent_email_new_workflow(
        self,
        requeue_privacy_requests,
        send_single_consent_email,
        db,
        privacy_notice,
        privacy_request_awaiting_consent_email_send,
        second_privacy_request_awaiting_consent_email_send,
        sovrn_email_connection_config,
        privacy_preference_history,
        privacy_preference_history_us_ca_provide,
        system,
    ) -> None:
        sovrn_email_connection_config.system_id = system.id
        sovrn_email_connection_config.save(db)

        # This preference matches on data use
        cache_identity_and_privacy_preferences(
            privacy_request_awaiting_consent_email_send,
            db,
            "12345",
            privacy_preference_history,
        )

        # This preference does not match on data use
        cache_identity_and_privacy_preferences(
            privacy_request_awaiting_consent_email_send,
            db,
            "12345",
            privacy_preference_history_us_ca_provide,
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
                consent_preferences=[],
                privacy_preferences=[
                    MinimalPrivacyPreferenceHistorySchema(
                        preference=UserConsentPreference.opt_out,
                        privacy_notice_history=PrivacyNoticeHistorySchema(
                            name="example privacy notice",
                            notice_key="example_privacy_notice_1",
                            consent_mechanism="opt_in",
                            data_uses=["marketing.advertising", "third_party_sharing"],
                            enforcement_level="system_wide",
                            disabled=False,
                            has_gpc_flag=False,
                            id=privacy_preference_history.privacy_notice_history.id,
                            translation_id=privacy_preference_history.privacy_notice_history.translation_id,
                            origin=privacy_notice.translations[
                                0
                            ].privacy_notice_history.origin,
                            version=1.0,
                        ),
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
            ),
        )
        assert logs_for_privacy_request_without_identity.count() == 1
        assert (
            logs_for_privacy_request_without_identity[0].status
            == ExecutionLogStatus.skipped
        )

        # Sovrn complete status and identities added to affected systems and secondary user ids because this preference is relevant
        assert (
            privacy_preference_history.affected_system_status[
                sovrn_email_connection_config.system_key
            ]
            == "complete"
        )
        assert privacy_preference_history.secondary_user_ids == {
            "ljt_readerID": "12345"
        }

        # Sovrn skipped status added and identities not added to affected systems and secondary user ids for irrelevant preference
        db.refresh(privacy_preference_history_us_ca_provide)
        assert (
            privacy_preference_history_us_ca_provide.affected_system_status[
                sovrn_email_connection_config.system_key
            ]
            == "skipped"
        )
        assert not privacy_preference_history_us_ca_provide.secondary_user_ids

    @mock.patch(
        "fides.api.service.connectors.consent_email_connector.send_single_consent_email",
    )
    @mock.patch(
        "fides.api.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
    )
    def test_send_generic_consent_email_new_workflow(
        self,
        requeue_privacy_requests,
        send_single_consent_email,
        db,
        privacy_notice,
        privacy_request_awaiting_consent_email_send,
        second_privacy_request_awaiting_consent_email_send,
        generic_consent_email_connection_config,
        privacy_preference_history,
        privacy_preference_history_us_ca_provide,
        system,
    ) -> None:
        generic_consent_email_connection_config.system_id = system.id
        generic_consent_email_connection_config.save(db)

        # This preference matches on data use
        cache_identity_and_privacy_preferences(
            privacy_request_awaiting_consent_email_send,
            db,
            "12345",
            privacy_preference_history,
        )

        # This preference does not match on data use
        cache_identity_and_privacy_preferences(
            privacy_request_awaiting_consent_email_send,
            db,
            "12345",
            privacy_preference_history_us_ca_provide,
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
                consent_preferences=[],
                privacy_preferences=[
                    MinimalPrivacyPreferenceHistorySchema(
                        preference=UserConsentPreference.opt_out,
                        privacy_notice_history=PrivacyNoticeHistorySchema(
                            name="example privacy notice",
                            notice_key="example_privacy_notice_1",
                            consent_mechanism="opt_in",
                            data_uses=["marketing.advertising", "third_party_sharing"],
                            enforcement_level="system_wide",
                            disabled=False,
                            has_gpc_flag=False,
                            id=privacy_preference_history.privacy_notice_history.id,
                            version=1.0,
                            origin=privacy_notice.translations[
                                0
                            ].privacy_notice_history.origin,
                            translation_id=privacy_preference_history.privacy_notice_history.translation_id,
                        ),
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
            == f"Consent email instructions dispatched for '{generic_consent_email_connection_config.name}'"
        )

        logs_for_privacy_request_without_identity = ExecutionLog.filter(
            db=db,
            conditions=(
                (
                    ExecutionLog.privacy_request_id
                    == second_privacy_request_awaiting_consent_email_send.id
                )
            ),
        )
        assert logs_for_privacy_request_without_identity.count() == 1
        assert (
            logs_for_privacy_request_without_identity[0].status
            == ExecutionLogStatus.skipped
        )

        # Sovrn complete status and identities added to affected systems and secondary user ids because this preference is relevant
        assert (
            privacy_preference_history.affected_system_status[
                generic_consent_email_connection_config.system_key
            ]
            == "complete"
        )
        assert privacy_preference_history.secondary_user_ids == {
            "ljt_readerID": "12345"
        }

        # Sovrn skipped status added and identities not added to affected systems and secondary user ids for irrelevant preference
        db.refresh(privacy_preference_history_us_ca_provide)
        assert (
            privacy_preference_history_us_ca_provide.affected_system_status[
                generic_consent_email_connection_config.system_key
            ]
            == "skipped"
        )
        assert not privacy_preference_history_us_ca_provide.secondary_user_ids

    @mock.patch(
        "fides.api.service.connectors.consent_email_connector.send_single_consent_email",
    )
    @mock.patch(
        "fides.api.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
    )
    def test_send_consent_email_multiple_users_old_workflow(
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

    @mock.patch(
        "fides.api.service.connectors.consent_email_connector.send_single_consent_email",
    )
    @mock.patch(
        "fides.api.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
    )
    def test_send_consent_email_multiple_users_new_workflow(
        self,
        requeue_privacy_requests,
        send_single_consent_email,
        db,
        privacy_request_awaiting_consent_email_send,
        second_privacy_request_awaiting_consent_email_send,
        sovrn_email_connection_config,
        privacy_preference_history,
        privacy_preference_history_us_ca_provide,
    ) -> None:
        cache_identity_and_privacy_preferences(
            privacy_request_awaiting_consent_email_send,
            db,
            "12345",
            privacy_preference_history,
        )
        cache_identity_and_privacy_preferences(
            second_privacy_request_awaiting_consent_email_send,
            db,
            "abcde",
            privacy_preference_history_us_ca_provide,
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
        "fides.api.service.connectors.erasure_email_connector.send_single_erasure_email",
    )
    @mock.patch(
        "fides.api.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
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
        "fides.api.service.connectors.erasure_email_connector.send_single_erasure_email",
    )
    @mock.patch(
        "fides.api.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
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
        "fides.api.service.connectors.erasure_email_connector.send_single_erasure_email",
    )
    @mock.patch(
        "fides.api.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
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
        "fides.api.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
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
        "fides.api.service.connectors.erasure_email_connector.send_single_erasure_email",
    )
    @mock.patch(
        "fides.api.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
    )
    def test_send_erasure_email(
        self,
        requeue_privacy_requests,
        send_single_erasure_email,
        db,
        privacy_request_awaiting_erasure_email_send,
        second_privacy_request_awaiting_consent_email_send,
        third_privacy_request_awaiting_erasure_email_send,
        attentive_email_connection_config,
    ) -> None:
        """
        Test for batch erasure email, also verifies that a privacy request
        queued for a consent email doesn't trigger an erasure email.
        """
        # third_privacy_request_awaiting_erasure_email_send has no identities
        cache = get_cache()
        all_keys = get_all_cache_keys_for_privacy_request(
            privacy_request_id=third_privacy_request_awaiting_erasure_email_send.id
        )
        for key in all_keys:
            cache.delete(key)

        exit_state = send_email_batch.delay().get()
        assert exit_state == EmailExitState.complete

        assert send_single_erasure_email.called
        assert requeue_privacy_requests.called

        call_kwargs = send_single_erasure_email.call_args.kwargs

        assert not call_kwargs["db"] == db
        assert call_kwargs["subject_email"] == "attentive@example.com"
        assert call_kwargs["subject_name"] == "Attentive Email"
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
            == f"Erasure email instructions dispatched for '{attentive_email_connection_config.name}'"
        )

        # Consent privacy request awaiting email send not relevant here
        consent_logs = ExecutionLog.filter(
            db=db,
            conditions=(
                (
                    ExecutionLog.privacy_request_id
                    == second_privacy_request_awaiting_consent_email_send.id
                )
            ),
        ).first()
        assert consent_logs is None

        # Erasure privacy request without identity data
        logs_for_privacy_request_without_identity = ExecutionLog.filter(
            db=db,
            conditions=(
                (
                    ExecutionLog.privacy_request_id
                    == third_privacy_request_awaiting_erasure_email_send.id
                )
            ),
        )
        assert logs_for_privacy_request_without_identity.count() == 1
        assert (
            logs_for_privacy_request_without_identity[0].status
            == ExecutionLogStatus.skipped
        )
        assert (
            logs_for_privacy_request_without_identity[0].action_type
            == ActionType.erasure
        )

    @mock.patch(
        "fides.api.service.connectors.erasure_email_connector.send_single_erasure_email",
    )
    @mock.patch(
        "fides.api.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
    )
    def test_send_generic_erasure_email(
        self,
        requeue_privacy_requests,
        send_single_erasure_email,
        db,
        privacy_request_awaiting_erasure_email_send,
        second_privacy_request_awaiting_consent_email_send,
        third_privacy_request_awaiting_erasure_email_send,
        generic_erasure_email_connection_config,
    ) -> None:
        """
        Test for batch erasure email, also verifies that a privacy request
        queued for a consent email doesn't trigger an erasure email.
        """
        # third_privacy_request_awaiting_erasure_email_send has no identities
        cache = get_cache()
        all_keys = get_all_cache_keys_for_privacy_request(
            privacy_request_id=third_privacy_request_awaiting_erasure_email_send.id
        )
        for key in all_keys:
            cache.delete(key)

        exit_state = send_email_batch.delay().get()
        assert exit_state == EmailExitState.complete

        assert send_single_erasure_email.called
        assert requeue_privacy_requests.called

        call_kwargs = send_single_erasure_email.call_args.kwargs

        assert not call_kwargs["db"] == db
        assert call_kwargs["subject_email"] == "attentive@example.com"
        assert call_kwargs["subject_name"] == "Attentive Email"
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
            == f"Erasure email instructions dispatched for '{generic_erasure_email_connection_config.name}'"
        )

        # Consent privacy request awaiting email send not relevant here
        consent_logs = ExecutionLog.filter(
            db=db,
            conditions=(
                (
                    ExecutionLog.privacy_request_id
                    == second_privacy_request_awaiting_consent_email_send.id
                )
            ),
        ).first()
        assert consent_logs is None

        # Erasure privacy request without identity data
        logs_for_privacy_request_without_identity = ExecutionLog.filter(
            db=db,
            conditions=(
                (
                    ExecutionLog.privacy_request_id
                    == third_privacy_request_awaiting_erasure_email_send.id
                )
            ),
        )
        assert logs_for_privacy_request_without_identity.count() == 1
        assert (
            logs_for_privacy_request_without_identity[0].status
            == ExecutionLogStatus.skipped
        )
        assert (
            logs_for_privacy_request_without_identity[0].action_type
            == ActionType.erasure
        )

    @mock.patch(
        "fides.api.service.connectors.erasure_email_connector.send_single_erasure_email",
    )
    @mock.patch(
        "fides.api.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
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
            == f"Erasure email instructions dispatched for '{attentive_email_connection_config.name}'"
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
            == f"Erasure email instructions dispatched for '{attentive_email_connection_config.name}'"
        )
