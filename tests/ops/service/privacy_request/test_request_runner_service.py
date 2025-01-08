# pylint: disable=missing-docstring, redefined-outer-name
import time
from typing import Any, Dict, List, Set
from unittest import mock
from unittest.mock import ANY, Mock, call

import pydash
import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

from fides.api.common_exceptions import (
    ClientUnsuccessfulException,
    PrivacyRequestPaused,
)
from fides.api.graph.graph import DatasetGraph
from fides.api.models.application_config import ApplicationConfig
from fides.api.models.policy import CurrentStep, PolicyPostWebhook
from fides.api.models.privacy_request import (
    ActionType,
    CheckpointActionRequired,
    ExecutionLog,
    ExecutionLogStatus,
    PolicyPreWebhook,
    PrivacyRequest,
    PrivacyRequestStatus,
)
from fides.api.schemas.masking.masking_configuration import MaskingConfiguration
from fides.api.schemas.masking.masking_secrets import MaskingSecretCache
from fides.api.schemas.messaging.messaging import (
    AccessRequestCompleteBodyParams,
    MessagingActionType,
    MessagingServiceType,
)
from fides.api.schemas.policy import Rule
from fides.api.schemas.privacy_request import Consent
from fides.api.schemas.redis_cache import Identity
from fides.api.service.masking.strategy.masking_strategy import MaskingStrategy
from fides.api.service.privacy_request.request_runner_service import (
    build_consent_dataset_graph,
    needs_batch_email_send,
    run_webhooks_and_report_status,
)
from fides.common.api.v1.urn_registry import REQUEST_TASK_CALLBACK, V1_URL_PREFIX
from fides.config import CONFIG

PRIVACY_REQUEST_TASK_TIMEOUT = 5
# External services take much longer to return
PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL = 100


@pytest.fixture(scope="function")
def privacy_request_complete_email_notification_enabled(db):
    """Enable request completion email"""
    original_value = CONFIG.notifications.send_request_completion_notification
    CONFIG.notifications.send_request_completion_notification = True
    ApplicationConfig.update_config_set(db, CONFIG)
    yield
    CONFIG.notifications.send_request_completion_notification = original_value
    ApplicationConfig.update_config_set(db, CONFIG)


@mock.patch("fides.api.service.privacy_request.request_runner_service.dispatch_message")
@mock.patch("fides.api.service.privacy_request.request_runner_service.upload")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_policy_upload_dispatch_message_called(
    upload_mock: Mock,
    mock_email_dispatch: Mock,
    privacy_request_status_pending: PrivacyRequest,
    run_privacy_request_task,
    dsr_version,
    request,
    privacy_request_complete_email_notification_enabled,
) -> None:
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    upload_mock.return_value = "http://www.data-download-url"
    run_privacy_request_task.delay(privacy_request_status_pending.id).get(
        timeout=PRIVACY_REQUEST_TASK_TIMEOUT
    )
    assert upload_mock.called
    assert mock_email_dispatch.call_count == 1


@mock.patch("fides.api.service.privacy_request.request_runner_service.dispatch_message")
@mock.patch("fides.api.service.privacy_request.request_runner_service.upload")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_complete_email_not_sent_if_consent_request(
    upload_mock: Mock,
    mock_email_dispatch: Mock,
    privacy_request_with_consent_policy: PrivacyRequest,
    run_privacy_request_task,
    dsr_version,
    request,
    privacy_request_complete_email_notification_enabled,
) -> None:
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    upload_mock.return_value = "http://www.data-download-url"
    run_privacy_request_task.delay(privacy_request_with_consent_policy.id).get(
        timeout=PRIVACY_REQUEST_TASK_TIMEOUT
    )
    assert not mock_email_dispatch.called


@mock.patch("fides.api.service.privacy_request.request_runner_service.dispatch_message")
@mock.patch("fides.api.service.privacy_request.request_runner_service.upload")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_start_processing_sets_started_processing_at(
    upload_mock: Mock,
    mock_email_dispatch: Mock,
    db: Session,
    privacy_request_status_pending: PrivacyRequest,
    run_privacy_request_task,
    request,
    dsr_version,
    privacy_request_complete_email_notification_enabled,
) -> None:
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    upload_mock.return_value = "http://www.data-download-url"
    updated_at = privacy_request_status_pending.updated_at
    assert privacy_request_status_pending.started_processing_at is None
    run_privacy_request_task.delay(privacy_request_status_pending.id).get(
        timeout=PRIVACY_REQUEST_TASK_TIMEOUT
    )

    db.refresh(privacy_request_status_pending)
    assert privacy_request_status_pending.started_processing_at is not None
    assert privacy_request_status_pending.updated_at > updated_at

    assert mock_email_dispatch.call_count == 1


@mock.patch("fides.api.service.privacy_request.request_runner_service.dispatch_message")
@mock.patch("fides.api.service.privacy_request.request_runner_service.upload")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_start_processing_doesnt_overwrite_started_processing_at(
    upload_mock: Mock,
    mock_email_dispatch: Mock,
    db: Session,
    privacy_request: PrivacyRequest,
    run_privacy_request_task,
    request,
    dsr_version,
    privacy_request_complete_email_notification_enabled,
) -> None:
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    upload_mock.return_value = "http://www.data-download-url"
    before = privacy_request.started_processing_at
    assert before is not None
    updated_at = privacy_request.updated_at

    run_privacy_request_task.delay(privacy_request.id).get(
        timeout=PRIVACY_REQUEST_TASK_TIMEOUT
    )

    db.refresh(privacy_request)
    assert privacy_request.started_processing_at == before
    assert privacy_request.updated_at > updated_at

    assert mock_email_dispatch.call_count == 1


@mock.patch(
    "fides.api.service.privacy_request.request_runner_service.upload_access_results"
)
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_halts_proceeding_if_cancelled(
    upload_access_results_mock,
    db: Session,
    privacy_request_status_canceled: PrivacyRequest,
    run_privacy_request_task,
    dsr_version,
    request,
    privacy_request_complete_email_notification_enabled,
) -> None:
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    assert privacy_request_status_canceled.status == PrivacyRequestStatus.canceled
    run_privacy_request_task.delay(privacy_request_status_canceled.id).get(
        timeout=PRIVACY_REQUEST_TASK_TIMEOUT
    )
    db.refresh(privacy_request_status_canceled)
    reloaded_pr = PrivacyRequest.get(
        db=db, object_id=privacy_request_status_canceled.id
    )
    assert reloaded_pr.started_processing_at is None
    assert reloaded_pr.status == PrivacyRequestStatus.canceled
    assert not upload_access_results_mock.called


@mock.patch("fides.api.service.privacy_request.request_runner_service.dispatch_message")
@mock.patch(
    "fides.api.service.privacy_request.request_runner_service.upload_access_results"
)
@mock.patch(
    "fides.api.service.privacy_request.request_runner_service.run_webhooks_and_report_status",
)
@mock.patch("fides.api.service.privacy_request.request_runner_service.access_runner")
@mock.patch("fides.api.service.privacy_request.request_runner_service.erasure_runner")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_from_graph_resume_does_not_run_pre_webhooks(
    run_erasure,
    run_access,
    run_webhooks,
    upload_mock: Mock,
    mock_email_dispatch,
    db: Session,
    privacy_request: PrivacyRequest,
    run_privacy_request_task,
    erasure_policy,
    dsr_version,
    request,
    privacy_request_complete_email_notification_enabled,
) -> None:
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    upload_mock.return_value = "http://www.data-download-url"
    privacy_request.started_processing_at = None
    privacy_request.policy = erasure_policy
    privacy_request.save(db)
    updated_at = privacy_request.updated_at

    run_privacy_request_task.delay(
        privacy_request_id=privacy_request.id,
        from_step=CurrentStep.access.value,
    ).get(timeout=PRIVACY_REQUEST_TASK_TIMEOUT)

    db.refresh(privacy_request)
    assert privacy_request.started_processing_at is not None
    assert privacy_request.updated_at > updated_at

    # Starting privacy request in the middle of the graph means we don't run pre-webhooks again
    assert run_webhooks.call_count == 1
    assert run_webhooks.call_args[1]["webhook_cls"] == PolicyPostWebhook

    assert run_access.call_count == 1  # Access request runs
    assert run_erasure.call_count == 1  # Erasure request runs

    assert mock_email_dispatch.call_count == 1


@mock.patch("fides.api.service.privacy_request.request_runner_service.dispatch_message")
@mock.patch(
    "fides.api.service.privacy_request.request_runner_service.run_webhooks_and_report_status",
)
@mock.patch("fides.api.service.privacy_request.request_runner_service.access_runner")
@mock.patch("fides.api.service.privacy_request.request_runner_service.erasure_runner")
def test_resume_privacy_request_from_erasure(
    run_erasure,
    run_access,
    run_webhooks,
    mock_email_dispatch,
    db: Session,
    privacy_request: PrivacyRequest,
    run_privacy_request_task,
    erasure_policy,
    privacy_request_complete_email_notification_enabled,
) -> None:
    privacy_request.started_processing_at = None
    privacy_request.policy = erasure_policy
    privacy_request.save(db)
    updated_at = privacy_request.updated_at

    run_privacy_request_task.delay(
        privacy_request_id=privacy_request.id,
        from_step=CurrentStep.erasure.value,
    ).get(timeout=PRIVACY_REQUEST_TASK_TIMEOUT)

    db.refresh(privacy_request)
    assert privacy_request.started_processing_at is not None
    assert privacy_request.updated_at > updated_at

    # Starting privacy request in the middle of the graph means we don't run pre-webhooks again
    assert run_webhooks.call_count == 1
    assert run_webhooks.call_args[1]["webhook_cls"] == PolicyPostWebhook

    assert run_access.call_count == 0  # Access request skipped
    assert run_erasure.call_count == 1  # Erasure request runs

    assert mock_email_dispatch.call_count == 1


def get_privacy_request_results(
    db,
    policy,
    run_privacy_request_task,
    privacy_request_data: Dict[str, Any],
    task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT,
) -> PrivacyRequest:
    """Utility method to run a privacy request and return results after waiting for
    the returned future."""
    kwargs = {
        "requested_at": pydash.get(privacy_request_data, "requested_at"),
        "policy_id": policy.id,
        "status": "pending",
    }
    optional_fields = ["started_processing_at", "finished_processing_at"]
    for field in optional_fields:
        try:
            attr = getattr(privacy_request_data, field)
            if attr is not None:
                kwargs[field] = attr
        except AttributeError:
            pass
    privacy_request = PrivacyRequest.create(db=db, data=kwargs)
    privacy_request.cache_identity(privacy_request_data["identity"])
    privacy_request.cache_custom_privacy_request_fields(
        privacy_request_data.get("custom_privacy_request_fields", None)
    )
    if "encryption_key" in privacy_request_data:
        privacy_request.cache_encryption(privacy_request_data["encryption_key"])

    erasure_rules: List[Rule] = policy.get_rules_for_action(
        action_type=ActionType.erasure
    )
    unique_masking_strategies_by_name: Set[str] = set()
    for rule in erasure_rules:
        strategy_name: str = rule.masking_strategy["strategy"]
        configuration: MaskingConfiguration = rule.masking_strategy["configuration"]
        if strategy_name in unique_masking_strategies_by_name:
            continue
        unique_masking_strategies_by_name.add(strategy_name)
        masking_strategy = MaskingStrategy.get_strategy(strategy_name, configuration)
        if masking_strategy.secrets_required():
            masking_secrets: List[MaskingSecretCache] = (
                masking_strategy.generate_secrets_for_cache()
            )
            for masking_secret in masking_secrets:
                privacy_request.cache_masking_secret(masking_secret)

    run_privacy_request_task.delay(privacy_request.id).get(
        timeout=task_timeout,
    )

    return PrivacyRequest.get(db=db, object_id=privacy_request.id)


class TestRunPrivacyRequestRunsWebhooks:
    @mock.patch(
        "fides.api.models.privacy_request.PrivacyRequest.trigger_policy_webhook"
    )
    def test_run_webhooks_halt_received(
        self,
        mock_trigger_policy_webhook,
        db,
        privacy_request,
        policy_pre_execution_webhooks,
    ):
        mock_trigger_policy_webhook.side_effect = PrivacyRequestPaused(
            "Request received to halt"
        )

        proceed = run_webhooks_and_report_status(db, privacy_request, PolicyPreWebhook)
        assert not proceed
        assert privacy_request.finished_processing_at is None
        assert privacy_request.status == PrivacyRequestStatus.paused
        assert privacy_request.paused_at is not None

    @mock.patch(
        "fides.api.models.privacy_request.PrivacyRequest.trigger_policy_webhook"
    )
    def test_run_webhooks_ap_scheduler_cleanup(
        self,
        mock_trigger_policy_webhook,
        db,
        privacy_request,
        policy_pre_execution_webhooks,
        short_redis_cache_expiration,  # Fixture forces cache to expire quickly
    ):
        mock_trigger_policy_webhook.side_effect = PrivacyRequestPaused(
            "Request received to halt"
        )

        proceed = run_webhooks_and_report_status(db, privacy_request, PolicyPreWebhook)
        assert not proceed
        time.sleep(3)

        db.refresh(privacy_request)
        # Privacy request has been set to errored by ap scheduler, because it took too long for webhook to report back
        assert privacy_request.status == PrivacyRequestStatus.error
        assert privacy_request.finished_processing_at is not None
        assert privacy_request.paused_at is not None

    @mock.patch(
        "fides.api.models.privacy_request.PrivacyRequest.trigger_policy_webhook"
    )
    def test_run_webhooks_client_error(
        self,
        mock_trigger_policy_webhook,
        db,
        privacy_request,
        policy_pre_execution_webhooks,
    ):
        mock_trigger_policy_webhook.side_effect = ClientUnsuccessfulException(
            status_code=500
        )

        proceed = run_webhooks_and_report_status(db, privacy_request, PolicyPreWebhook)
        assert not proceed
        assert privacy_request.status == PrivacyRequestStatus.error
        assert privacy_request.finished_processing_at is not None
        assert (
            privacy_request.get_failed_checkpoint_details()
            == CheckpointActionRequired(step=CurrentStep.pre_webhooks)
        )
        assert privacy_request.paused_at is None

    @mock.patch(
        "fides.api.models.privacy_request.PrivacyRequest.trigger_policy_webhook"
    )
    def test_run_webhooks_validation_error(
        self,
        mock_trigger_policy_webhook,
        db,
        privacy_request,
        policy_pre_execution_webhooks,
    ):
        mock_trigger_policy_webhook.side_effect = ValidationError.from_exception_data(
            title="Validation Error", line_errors=[]
        )

        proceed = run_webhooks_and_report_status(db, privacy_request, PolicyPreWebhook)
        assert not proceed
        assert privacy_request.finished_processing_at is not None
        assert privacy_request.status == PrivacyRequestStatus.error
        assert privacy_request.paused_at is None

    @mock.patch(
        "fides.api.models.privacy_request.PrivacyRequest.trigger_policy_webhook"
    )
    def test_run_webhooks(
        self,
        mock_trigger_policy_webhook,
        db,
        privacy_request,
        policy_pre_execution_webhooks,
    ):
        proceed = run_webhooks_and_report_status(db, privacy_request, PolicyPreWebhook)
        assert proceed
        assert privacy_request.status == PrivacyRequestStatus.in_processing
        assert privacy_request.finished_processing_at is None
        assert mock_trigger_policy_webhook.call_count == 2

    @mock.patch(
        "fides.api.models.privacy_request.PrivacyRequest.trigger_policy_webhook"
    )
    def test_run_webhooks_after_webhook(
        self,
        mock_trigger_policy_webhook,
        db,
        privacy_request,
        policy_pre_execution_webhooks,
    ):
        """Test running webhooks after specific webhook - for when we're resuming privacy request execution"""
        proceed = run_webhooks_and_report_status(
            db, privacy_request, PolicyPreWebhook, policy_pre_execution_webhooks[0].id
        )
        assert proceed
        assert privacy_request.status == PrivacyRequestStatus.in_processing
        assert privacy_request.finished_processing_at is None
        assert mock_trigger_policy_webhook.call_count == 1

        kwarg = "policy_action"
        assert kwarg in mock_trigger_policy_webhook._mock_call_args_list[0][1]
        assert (
            mock_trigger_policy_webhook._mock_call_args_list[0][1][kwarg]
            == ActionType.access
        )


class TestPrivacyRequestsEmailNotifications:
    @pytest.fixture(scope="function")
    def privacy_request_complete_email_notification_enabled(self, db):
        """Enable request completion email"""
        original_value = CONFIG.notifications.send_request_completion_notification
        CONFIG.notifications.send_request_completion_notification = True
        ApplicationConfig.update_config_set(db, CONFIG)
        yield
        CONFIG.notifications.send_request_completion_notification = original_value
        ApplicationConfig.update_config_set(db, CONFIG)

    @pytest.mark.integration_postgres
    @pytest.mark.integration
    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.dispatch_message"
    )
    def test_email_complete_send_erasure(
        self,
        mailgun_send,
        postgres_integration_db,
        postgres_example_test_dataset_config,
        cache,
        db,
        generate_auth_header,
        erasure_policy,
        read_connection_config,
        messaging_config,
        dsr_version,
        request,
        privacy_request_complete_email_notification_enabled,
        run_privacy_request_task,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        customer_email = "customer-1@example.com"
        data = {
            "requested_at": "2021-08-30T16:09:37.359Z",
            "policy_key": erasure_policy.key,
            "identity": {"email": customer_email},
        }

        pr = get_privacy_request_results(
            db,
            erasure_policy,
            run_privacy_request_task,
            data,
        )
        pr.delete(db=db)

        mailgun_send.assert_called_once()

    @pytest.mark.integration_postgres
    @pytest.mark.integration
    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.dispatch_message"
    )
    @mock.patch("fides.api.service.privacy_request.request_runner_service.upload")
    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    def test_email_complete_send_access(
        self,
        upload_mock,
        mailgun_send,
        postgres_integration_db,
        postgres_example_test_dataset_config,
        cache,
        db,
        generate_auth_header,
        policy,
        read_connection_config,
        messaging_config,
        privacy_request_complete_email_notification_enabled,
        run_privacy_request_task,
        dsr_version,
        request,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        upload_mock.return_value = "http://www.data-download-url"
        customer_email = "customer-1@example.com"
        data = {
            "requested_at": "2021-08-30T16:09:37.359Z",
            "policy_key": policy.key,
            "identity": {"email": customer_email},
        }

        pr = get_privacy_request_results(
            db,
            policy,
            run_privacy_request_task,
            data,
        )
        pr.delete(db=db)

        mailgun_send.assert_called_once()

    @pytest.mark.integration_postgres
    @pytest.mark.integration
    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.dispatch_message"
    )
    @mock.patch("fides.api.service.privacy_request.request_runner_service.upload")
    def test_email_complete_send_access_and_erasure(
        self,
        upload_mock,
        mailgun_send,
        postgres_integration_db,
        postgres_example_test_dataset_config,
        cache,
        db,
        generate_auth_header,
        access_and_erasure_policy,
        read_connection_config,
        messaging_config,
        dsr_version,
        request,
        privacy_request_complete_email_notification_enabled,
        run_privacy_request_task,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        upload_mock.return_value = "http://www.data-download-url"
        download_time_in_days = "5"
        customer_email = "customer-1@example.com"
        data = {
            "requested_at": "2021-08-30T16:09:37.359Z",
            "policy_key": access_and_erasure_policy.key,
            "identity": {"email": customer_email},
        }

        pr = get_privacy_request_results(
            db,
            access_and_erasure_policy,
            run_privacy_request_task,
            data,
        )
        pr.delete(db=db)
        identity = Identity(email=customer_email)

        mailgun_send.assert_has_calls(
            [
                call(
                    db=ANY,
                    action_type=MessagingActionType.PRIVACY_REQUEST_COMPLETE_ACCESS,
                    to_identity=identity,
                    service_type=MessagingServiceType.mailgun.value,
                    message_body_params=AccessRequestCompleteBodyParams(
                        subject_request_download_time_in_days=download_time_in_days,
                        download_links=[upload_mock.return_value],
                    ),
                    property_id=None,
                ),
                call(
                    db=ANY,
                    action_type=MessagingActionType.PRIVACY_REQUEST_COMPLETE_DELETION,
                    to_identity=identity,
                    service_type=MessagingServiceType.mailgun.value,
                    message_body_params=None,
                    property_id=None,
                ),
            ],
            any_order=True,
        )

    @pytest.mark.integration_postgres
    @pytest.mark.integration
    @mock.patch(
        "fides.api.service.messaging.message_dispatch_service._mailgun_dispatcher"
    )
    @mock.patch("fides.api.service.privacy_request.request_runner_service.upload")
    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    def test_email_complete_send_access_no_messaging_config(
        self,
        upload_mock,
        mailgun_send,
        postgres_integration_db,
        postgres_example_test_dataset_config,
        cache,
        db,
        generate_auth_header,
        policy,
        read_connection_config,
        dsr_version,
        request,
        privacy_request_complete_email_notification_enabled,
        run_privacy_request_task,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        upload_mock.return_value = "http://www.data-download-url"
        customer_email = "customer-1@example.com"
        data = {
            "requested_at": "2021-08-30T16:09:37.359Z",
            "policy_key": policy.key,
            "identity": {"email": customer_email},
        }

        pr = get_privacy_request_results(
            db,
            policy,
            run_privacy_request_task,
            data,
        )
        db.refresh(pr)
        assert pr.status == PrivacyRequestStatus.error
        pr.delete(db=db)

        assert mailgun_send.called is False

    @pytest.mark.integration_postgres
    @pytest.mark.integration
    @mock.patch(
        "fides.api.service.messaging.message_dispatch_service._mailgun_dispatcher"
    )
    @mock.patch("fides.api.service.privacy_request.request_runner_service.upload")
    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    def test_email_complete_send_access_no_email_identity(
        self,
        upload_mock,
        mailgun_send,
        postgres_integration_db,
        postgres_example_test_dataset_config,
        cache,
        db,
        generate_auth_header,
        policy,
        read_connection_config,
        privacy_request_complete_email_notification_enabled,
        run_privacy_request_task,
        dsr_version,
        request,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        upload_mock.return_value = "http://www.data-download-url"
        data = {
            "requested_at": "2021-08-30T16:09:37.359Z",
            "policy_key": policy.key,
            "identity": {"phone_number": "+1231231233"},
        }

        pr = get_privacy_request_results(
            db,
            policy,
            run_privacy_request_task,
            data,
        )
        db.refresh(pr)
        assert pr.status == PrivacyRequestStatus.error
        pr.delete(db=db)

        assert mailgun_send.called is False


class TestPrivacyRequestsManualWebhooks:
    @mock.patch("fides.api.service.privacy_request.request_runner_service.upload")
    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    def test_privacy_request_needs_manual_input_key_in_cache(
        self,
        mock_upload,
        integration_manual_webhook_config,
        access_manual_webhook,
        policy,
        run_privacy_request_task,
        db,
        dsr_version,
        request,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        customer_email = "customer-1@example.com"
        data = {
            "requested_at": "2021-08-30T16:09:37.359Z",
            "policy_key": policy.key,
            "identity": {"email": customer_email},
        }

        pr = get_privacy_request_results(
            db,
            policy,
            run_privacy_request_task,
            data,
        )
        db.refresh(pr)
        assert pr.status == PrivacyRequestStatus.requires_input
        assert not mock_upload.called

    @mock.patch("fides.api.service.privacy_request.request_runner_service.upload")
    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.erasure_runner"
    )
    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    def test_manual_input_required_for_erasure_only_policies(
        self,
        mock_erasure,
        mock_upload,
        integration_manual_webhook_config,
        access_manual_webhook,
        erasure_policy,
        dsr_version,
        request,
        run_privacy_request_task,
        db,
    ):
        """Manual inputs are not tied to policies, but should still hold up a request even for erasure requests."""
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        customer_email = "customer-1@example.com"
        data = {
            "requested_at": "2021-08-30T16:09:37.359Z",
            "policy_key": erasure_policy.key,
            "identity": {"email": customer_email},
        }

        pr = get_privacy_request_results(
            db,
            erasure_policy,
            run_privacy_request_task,
            data,
        )
        db.refresh(pr)
        assert pr.status == PrivacyRequestStatus.requires_input
        assert not mock_upload.called  # erasure only request, no data uploaded
        assert not mock_erasure.called

    @mock.patch("fides.api.service.privacy_request.request_runner_service.upload")
    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    def test_pass_on_manually_added_input(
        self,
        mock_upload,
        integration_manual_webhook_config,
        access_manual_webhook,
        policy,
        run_privacy_request_task,
        privacy_request_requires_input: PrivacyRequest,
        db,
        dsr_version,
        request,
        cached_access_input,
    ):
        mock_upload.return_value = "http://www.data-download-url"
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        run_privacy_request_task.delay(privacy_request_requires_input.id).get(
            timeout=PRIVACY_REQUEST_TASK_TIMEOUT
        )
        db.refresh(privacy_request_requires_input)
        assert privacy_request_requires_input.status == PrivacyRequestStatus.complete
        assert mock_upload.called
        assert mock_upload.call_args.kwargs["data"] == {
            "manual_webhook_example": [
                {"email": "customer-1@example.com", "last_name": "McCustomer"}
            ]
        }

    @mock.patch("fides.api.service.privacy_request.request_runner_service.upload")
    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    def test_pass_on_partial_manually_added_input(
        self,
        mock_upload,
        integration_manual_webhook_config,
        access_manual_webhook,
        policy,
        run_privacy_request_task,
        dsr_version,
        request,
        privacy_request_requires_input: PrivacyRequest,
        db,
    ):
        mock_upload.return_value = "http://www.data-download-url"
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        privacy_request_requires_input.cache_manual_webhook_access_input(
            access_manual_webhook,
            {"email": "customer-1@example.com"},
        )

        run_privacy_request_task.delay(privacy_request_requires_input.id).get(
            timeout=PRIVACY_REQUEST_TASK_TIMEOUT
        )

        db.refresh(privacy_request_requires_input)
        assert privacy_request_requires_input.status == PrivacyRequestStatus.complete
        assert mock_upload.called
        assert mock_upload.call_args.kwargs["data"] == {
            "manual_webhook_example": [
                {"email": "customer-1@example.com", "last_name": None}
            ]
        }

    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    @mock.patch("fides.api.service.privacy_request.request_runner_service.upload")
    def test_pass_on_empty_confirmed_input(
        self,
        mock_upload,
        integration_manual_webhook_config,
        access_manual_webhook,
        policy,
        run_privacy_request_task,
        privacy_request_requires_input: PrivacyRequest,
        db,
        dsr_version,
        request,
    ):
        mock_upload.return_value = "http://www.data-download-url"
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        privacy_request_requires_input.cache_manual_webhook_access_input(
            access_manual_webhook,
            {},
        )

        run_privacy_request_task.delay(privacy_request_requires_input.id).get(
            timeout=PRIVACY_REQUEST_TASK_TIMEOUT
        )

        db.refresh(privacy_request_requires_input)
        assert privacy_request_requires_input.status == PrivacyRequestStatus.complete
        assert mock_upload.called
        assert mock_upload.call_args.kwargs["data"] == {
            "manual_webhook_example": [{"email": None, "last_name": None}]
        }


def test_build_consent_dataset_graph(
    postgres_example_test_dataset_config_read_access,
    mysql_example_test_dataset_config,
    saas_example_dataset_config,
):
    """Currently returns a DatasetGraph made up of resources that have consent requests defined
    in the saas config"""
    dataset_graph: DatasetGraph = build_consent_dataset_graph(
        [
            postgres_example_test_dataset_config_read_access,
            mysql_example_test_dataset_config,
            saas_example_dataset_config,
        ]
    )
    assert len(dataset_graph.nodes.keys()) == 1
    assert [col_addr.value for col_addr in dataset_graph.nodes.keys()] == [
        "saas_connector_example:saas_connector_example"
    ]


class TestConsentEmailStep:
    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    def test_privacy_request_completes_if_no_consent_email_send_needed(
        self,
        db,
        privacy_request_with_consent_policy,
        run_privacy_request_task,
        dsr_version,
        request,
        sovrn_email_connection_config,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        run_privacy_request_task.delay(
            privacy_request_id=privacy_request_with_consent_policy.id,
            from_step=None,
        ).get(timeout=5)
        db.refresh(privacy_request_with_consent_policy)
        assert (
            privacy_request_with_consent_policy.status == PrivacyRequestStatus.complete
        )
        execution_logs = db.query(ExecutionLog).filter_by(
            privacy_request_id=privacy_request_with_consent_policy.id,
            dataset_name=sovrn_email_connection_config.name,
        )

        assert execution_logs.count() == 1

        assert [log.status for log in execution_logs] == [
            ExecutionLogStatus.skipped,
        ]

    @pytest.mark.usefixtures("sovrn_email_connection_config")
    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    def test_privacy_request_is_put_in_awaiting_email_send_status_old_workflow(
        self,
        db,
        privacy_request_with_consent_policy,
        run_privacy_request_task,
        dsr_version,
        request,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        identity = Identity(email="customer_1#@example.com", ljt_readerID="12345")
        privacy_request_with_consent_policy.cache_identity(identity)
        privacy_request_with_consent_policy.consent_preferences = [
            Consent(data_use="marketing.advertising", opt_in=False).model_dump(
                mode="json"
            )
        ]
        privacy_request_with_consent_policy.save(db)

        run_privacy_request_task.delay(
            privacy_request_id=privacy_request_with_consent_policy.id,
            from_step=None,
        ).get(timeout=PRIVACY_REQUEST_TASK_TIMEOUT)
        db.refresh(privacy_request_with_consent_policy)
        assert (
            privacy_request_with_consent_policy.status
            == PrivacyRequestStatus.awaiting_email_send
        )
        assert privacy_request_with_consent_policy.awaiting_email_send_at is not None

    @pytest.mark.usefixtures("sovrn_email_connection_config")
    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    def test_privacy_request_is_put_in_awaiting_email_new_workflow(
        self,
        db,
        privacy_request_with_consent_policy,
        run_privacy_request_task,
        dsr_version,
        request,
        privacy_preference_history,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        identity = Identity(email="customer_1#@example.com", ljt_readerID="12345")
        privacy_request_with_consent_policy.cache_identity(identity)
        privacy_preference_history.privacy_request_id = (
            privacy_request_with_consent_policy.id
        )
        privacy_preference_history.save(db)
        privacy_request_with_consent_policy.save(db)

        run_privacy_request_task.delay(
            privacy_request_id=privacy_request_with_consent_policy.id,
            from_step=None,
        ).get(timeout=PRIVACY_REQUEST_TASK_TIMEOUT)
        db.refresh(privacy_request_with_consent_policy)
        assert (
            privacy_request_with_consent_policy.status
            == PrivacyRequestStatus.awaiting_email_send
        )
        assert privacy_request_with_consent_policy.awaiting_email_send_at is not None

    def test_needs_batch_email_send_no_consent_preferences(
        self, db, privacy_request_with_consent_policy
    ):
        assert not needs_batch_email_send(
            db, {"email": "customer-1@example.com"}, privacy_request_with_consent_policy
        )

    def test_needs_batch_email_send_no_email_consent_connections_old_workflow(
        self, db, privacy_request_with_consent_policy
    ):
        privacy_request_with_consent_policy.consent_preferences = [
            Consent(data_use="marketing.advertising", opt_in=False).model_dump(
                mode="json"
            )
        ]
        privacy_request_with_consent_policy.save(db)
        assert not needs_batch_email_send(
            db, {"email": "customer-1@example.com"}, privacy_request_with_consent_policy
        )

    def test_needs_batch_email_send_no_email_consent_connections_new_workflow(
        self, db, privacy_request_with_consent_policy, privacy_preference_history
    ):
        privacy_preference_history.privacy_request_id = (
            privacy_request_with_consent_policy.id
        )
        privacy_preference_history.save(db)
        assert not needs_batch_email_send(
            db, {"email": "customer-1@example.com"}, privacy_request_with_consent_policy
        )

    @pytest.mark.usefixtures("sovrn_email_connection_config")
    def test_needs_batch_email_send_no_relevant_identities_old_workflow(
        self, db, privacy_request_with_consent_policy
    ):
        privacy_request_with_consent_policy.consent_preferences = [
            Consent(data_use="marketing.advertising", opt_in=False).model_dump(
                mode="json"
            )
        ]
        privacy_request_with_consent_policy.save(db)
        assert not needs_batch_email_send(
            db, {"email": "customer-1@example.com"}, privacy_request_with_consent_policy
        )

    @pytest.mark.usefixtures("sovrn_email_connection_config")
    def test_needs_batch_email_send_no_relevant_identities_new_workflow(
        self, db, privacy_request_with_consent_policy, privacy_preference_history
    ):
        privacy_preference_history.privacy_request_id = (
            privacy_request_with_consent_policy.id
        )
        privacy_preference_history.save(db)
        assert not needs_batch_email_send(
            db, {"email": "customer-1@example.com"}, privacy_request_with_consent_policy
        )

    @pytest.mark.usefixtures("sovrn_email_connection_config")
    def test_needs_batch_email_send_old_workflow(
        self, db, privacy_request_with_consent_policy
    ):
        privacy_request_with_consent_policy.consent_preferences = [
            Consent(data_use="marketing.advertising", opt_in=False).model_dump(
                mode="json"
            )
        ]
        privacy_request_with_consent_policy.save(db)
        assert needs_batch_email_send(
            db,
            {"email": "customer-1@example.com", "ljt_readerID": "12345"},
            privacy_request_with_consent_policy,
        )

    @pytest.mark.usefixtures("sovrn_email_connection_config")
    def test_needs_batch_email_send_system_and_notice_data_use_mismatch(
        self,
        db,
        privacy_request_with_consent_policy,
        system,
        privacy_preference_history_us_ca_provide,
        sovrn_email_connection_config,
    ):
        sovrn_email_connection_config.system_id = system.id
        sovrn_email_connection_config.save(db)

        privacy_preference_history_us_ca_provide.privacy_request_id = (
            privacy_request_with_consent_policy.id
        )
        privacy_preference_history_us_ca_provide.save(db)
        assert not needs_batch_email_send(
            db,
            {"email": "customer-1@example.com", "ljt_readerID": "12345"},
            privacy_request_with_consent_policy,
        )

    @pytest.mark.usefixtures("sovrn_email_connection_config")
    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    def test_skipped_batch_email_send_updates_privacy_preferences_with_system_status(
        self,
        db,
        privacy_request_with_consent_policy,
        system,
        dsr_version,
        request,
        privacy_preference_history_us_ca_provide,
        sovrn_email_connection_config,
        run_privacy_request_task,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        sovrn_email_connection_config.system_id = system.id
        sovrn_email_connection_config.save(db)

        privacy_preference_history_us_ca_provide.privacy_request_id = (
            privacy_request_with_consent_policy.id
        )
        privacy_preference_history_us_ca_provide.save(db)

        identity = Identity(email="customer_1#@example.com", ljt_readerID="12345")
        privacy_request_with_consent_policy.cache_identity(identity)

        run_privacy_request_task.delay(
            privacy_request_id=privacy_request_with_consent_policy.id,
            from_step=None,
        ).get(timeout=PRIVACY_REQUEST_TASK_TIMEOUT)
        db.refresh(privacy_request_with_consent_policy)
        assert (
            privacy_request_with_consent_policy.status == PrivacyRequestStatus.complete
        )
        assert privacy_request_with_consent_policy.awaiting_email_send_at is None
        db.refresh(privacy_request_with_consent_policy.privacy_preferences[0])

        assert privacy_request_with_consent_policy.privacy_preferences[
            0
        ].affected_system_status == {system.fides_key: "skipped"}

    @pytest.mark.usefixtures("sovrn_email_connection_config")
    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    def test_needs_batch_email_send_new_workflow(
        self,
        db,
        privacy_request_with_consent_policy,
        privacy_preference_history,
        dsr_version,
        request,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        privacy_preference_history.privacy_request_id = (
            privacy_request_with_consent_policy.id
        )
        privacy_preference_history.save(db)
        assert needs_batch_email_send(
            db,
            {"email": "customer-1@example.com", "ljt_readerID": "12345"},
            privacy_request_with_consent_policy,
        )


class TestAsyncCallbacks:
    @mock.patch("fides.api.service.connectors.saas_connector.AuthenticatedClient.send")
    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    def test_async_callback_access_request(
        self,
        mock_send,
        api_client,
        saas_example_async_dataset_config,
        saas_async_example_connection_config: Dict[str, str],
        db,
        policy,
        dsr_version,
        request,
        run_privacy_request_task,
    ):
        """Demonstrate end-to-end support for tasks expecting async callbacks for DSR 3.0"""
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0
        mock_send().json.return_value = {"id": "123"}

        pr = get_privacy_request_results(
            db,
            policy,
            run_privacy_request_task,
            {"identity": {"email": "customer-1@example.com"}},
            task_timeout=120,
        )
        db.refresh(pr)

        if dsr_version == "use_dsr_3_0":
            assert pr.status == PrivacyRequestStatus.in_processing

            request_tasks = pr.access_tasks
            assert request_tasks[0].status == ExecutionLogStatus.complete

            # SaaS Request was marked as needing async results, so the Request
            # Task was put in a paused state
            assert request_tasks[1].status == ExecutionLogStatus.awaiting_processing
            assert request_tasks[1].collection_address == "saas_async_config:user"

            # Terminator task is downstream so it is still in a pending state
            assert request_tasks[2].status == ExecutionLogStatus.pending

            jwe_token = mock_send.call_args[0][0].headers["reply-to-token"]
            auth_header = {"Authorization": "Bearer " + jwe_token}
            # Post to callback URL to supply access results async
            # This requeues task and proceeds downstream
            api_client.post(
                V1_URL_PREFIX + REQUEST_TASK_CALLBACK,
                headers=auth_header,
                json={"access_results": [{"id": 1, "user_id": "abcde", "state": "VA"}]},
            )
            db.refresh(pr)
            assert pr.status == PrivacyRequestStatus.complete
            assert pr.get_raw_access_results() == {
                "saas_async_config:user": [{"id": 1, "user_id": "abcde", "state": "VA"}]
            }
            # User data supplied async was filtered before being returned to the end user
            assert pr.get_filtered_final_upload() == {
                "access_request_rule": {
                    "saas_async_config:user": [{"state": "VA", "id": 1}]
                }
            }
        else:
            # Async Access Requests not supported for DSR 2.0 - the given
            # node cannot be paused
            assert pr.status == PrivacyRequestStatus.complete

    @mock.patch("fides.api.service.connectors.saas_connector.AuthenticatedClient.send")
    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    def test_async_callback_erasure_request(
        self,
        mock_send,
        saas_example_async_dataset_config,
        saas_async_example_connection_config: Dict[str, str],
        db,
        api_client,
        erasure_policy,
        dsr_version,
        request,
        run_privacy_request_task,
    ):
        """Demonstrate end-to-end support for erasure tasks expecting async callbacks for DSR 3.0"""
        mock_send().json.return_value = {"id": "123"}

        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        pr = get_privacy_request_results(
            db,
            erasure_policy,
            run_privacy_request_task,
            {"identity": {"email": "customer-1@example.com"}},
            task_timeout=120,
        )

        if dsr_version == "use_dsr_3_0":
            # Access async task fired first
            assert pr.access_tasks[1].status == ExecutionLogStatus.awaiting_processing
            jwe_token = mock_send.call_args[0][0].headers["reply-to-token"]
            auth_header = {"Authorization": "Bearer " + jwe_token}
            # Post to callback URL to supply access results async
            # This requeues task and proceeds downstream
            response = api_client.post(
                V1_URL_PREFIX + REQUEST_TASK_CALLBACK,
                headers=auth_header,
                json={"access_results": [{"id": 1, "user_id": "abcde", "state": "VA"}]},
            )
            assert response.status_code == 200

            # Erasure task is also expected async results and is now paused
            assert pr.erasure_tasks[1].status == ExecutionLogStatus.awaiting_processing
            jwe_token = mock_send.call_args[0][0].headers["reply-to-token"]
            auth_header = {"Authorization": "Bearer " + jwe_token}
            # Post to callback URL to supply erasure results async
            # This requeues task and proceeds downstream to complete privacy request
            response = api_client.post(
                V1_URL_PREFIX + REQUEST_TASK_CALLBACK,
                headers=auth_header,
                json={"rows_masked": 2},
            )
            assert response.status_code == 200

            db.refresh(pr)
            assert pr.status == PrivacyRequestStatus.complete

            assert pr.erasure_tasks[1].rows_masked == 2
            assert pr.erasure_tasks[1].status == ExecutionLogStatus.complete

        else:
            # Async Erasure Requests not supported for DSR 2.0 - the given
            # node cannot be paused
            db.refresh(pr)
            assert pr.status == PrivacyRequestStatus.complete
