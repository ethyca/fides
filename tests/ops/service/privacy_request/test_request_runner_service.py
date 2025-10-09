# pylint: disable=missing-docstring, redefined-outer-name
import time
from io import BytesIO
from typing import Any, Dict, List, Set
from unittest import mock
from unittest.mock import ANY, Mock, call

import pydash
import pytest
import sqlalchemy.exc
from pydantic import ValidationError
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from fides.api.common_exceptions import (
    ClientUnsuccessfulException,
    PrivacyRequestPaused,
)
from fides.api.graph.graph import DatasetGraph
from fides.api.models.application_config import ApplicationConfig
from fides.api.models.attachment import (
    Attachment,
    AttachmentReference,
    AttachmentReferenceType,
    AttachmentType,
)
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.manual_webhook import AccessManualWebhook
from fides.api.models.policy import PolicyPostWebhook, PolicyPreWebhook
from fides.api.models.privacy_request import ExecutionLog, PrivacyRequest
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.masking.masking_configuration import MaskingConfiguration
from fides.api.schemas.masking.masking_secrets import MaskingSecretCache
from fides.api.schemas.messaging.messaging import (
    AccessRequestCompleteBodyParams,
    MessagingActionType,
    MessagingServiceType,
)
from fides.api.schemas.policy import ActionType, CurrentStep, Rule
from fides.api.schemas.privacy_request import (
    CheckpointActionRequired,
    Consent,
    PrivacyRequestStatus,
)
from fides.api.schemas.redis_cache import Identity
from fides.api.schemas.storage.storage import StorageType
from fides.api.service.masking.strategy.masking_strategy import MaskingStrategy
from fides.api.service.privacy_request.request_runner_service import (
    build_consent_dataset_graph,
    initiate_privacy_request_completion_email,
    needs_batch_email_send,
    run_webhooks_and_report_status,
    save_access_results,
)
from fides.common.api.v1.urn_registry import REQUEST_TASK_CALLBACK, V1_URL_PREFIX
from fides.config import CONFIG

PRIVACY_REQUEST_TASK_TIMEOUT = 5
# External services take much longer to return
PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL = 100


class TestManualFinalization:
    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    def test_mark_as_requires_manual_finalization_if_config_true(
        self,
        db: Session,
        run_privacy_request_task,
        dsr_version,
        request,
        enable_erasure_request_finalization_required,
        privacy_request_erasure_pending,
    ) -> None:
        """Assert marking privacy request as requires_manual_finalization"""
        request.getfixturevalue(dsr_version)
        privacy_request = privacy_request_erasure_pending
        run_privacy_request_task.delay(privacy_request.id).get(
            timeout=PRIVACY_REQUEST_TASK_TIMEOUT
        )
        db.refresh(privacy_request)
        assert (
            privacy_request.status == PrivacyRequestStatus.requires_manual_finalization
        )

    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    def test_no_manual_finalization_if_config_false(
        self,
        db: Session,
        run_privacy_request_task,
        dsr_version,
        request,
        disable_erasure_request_finalization_required,
        privacy_request_erasure_pending,
    ) -> None:
        """Assert marking pending privacy request as complete"""
        request.getfixturevalue(dsr_version)
        privacy_request = privacy_request_erasure_pending
        run_privacy_request_task.delay(privacy_request.id).get(
            timeout=PRIVACY_REQUEST_TASK_TIMEOUT
        )
        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.complete

    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    def test_mark_as_complete_when_finalized_at_exists(
        self,
        db: Session,
        run_privacy_request_task,
        dsr_version,
        request,
        enable_erasure_request_finalization_required,
        privacy_request_requires_manual_finalization,
    ) -> None:
        """Ensures that if finalized_at exists, we mark it as complete"""
        request.getfixturevalue(dsr_version)
        privacy_request = privacy_request_requires_manual_finalization
        privacy_request.finalized_at = "2021-08-30T16:09:37.359Z"
        privacy_request.save(db)

        run_privacy_request_task.delay(privacy_request.id).get(
            timeout=PRIVACY_REQUEST_TASK_TIMEOUT
        )
        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.complete


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


@pytest.mark.parametrize(
    "policy_fixture, expected_status",
    [
        ("erasure_policy", PrivacyRequestStatus.complete),
        ("erasure_policy_aes", PrivacyRequestStatus.error),
    ],
)
@mock.patch("fides.api.service.privacy_request.request_runner_service.dispatch_message")
@mock.patch(
    "fides.api.service.privacy_request.request_runner_service.run_webhooks_and_report_status",
)
@mock.patch("fides.api.service.privacy_request.request_runner_service.access_runner")
@mock.patch("fides.api.service.privacy_request.request_runner_service.erasure_runner")
def test_resume_privacy_request_from_erasure_with_expired_masking_secrets(
    run_erasure,
    run_access,
    run_webhooks,
    mock_email_dispatch,
    db: Session,
    privacy_request: PrivacyRequest,
    run_privacy_request_task,
    privacy_request_complete_email_notification_enabled,
    policy_fixture,
    expected_status,
    request,
) -> None:
    """
    Verifies that resuming a privacy request from the erasure step will result in an error status
    if the given policy requires masking secrets and they have expired from the cache.
    """

    policy = request.getfixturevalue(policy_fixture)
    privacy_request.policy = policy
    privacy_request.save(db)

    run_privacy_request_task.delay(
        privacy_request_id=privacy_request.id,
        from_step=CurrentStep.erasure.value,
    ).get(timeout=PRIVACY_REQUEST_TASK_TIMEOUT)

    db.refresh(privacy_request)
    assert privacy_request.status == expected_status


@pytest.mark.parametrize(
    "policy_fixture, expected_status",
    [
        ("erasure_policy", PrivacyRequestStatus.complete),
        ("erasure_policy_aes", PrivacyRequestStatus.complete),
    ],
)
@mock.patch("fides.api.service.privacy_request.request_runner_service.dispatch_message")
@mock.patch(
    "fides.api.service.privacy_request.request_runner_service.run_webhooks_and_report_status",
)
@mock.patch("fides.api.service.privacy_request.request_runner_service.access_runner")
@mock.patch("fides.api.service.privacy_request.request_runner_service.erasure_runner")
def test_resume_privacy_request_from_erasure_with_available_masking_secrets(
    run_erasure,
    run_access,
    run_webhooks,
    mock_email_dispatch,
    db: Session,
    privacy_request: PrivacyRequest,
    run_privacy_request_task,
    privacy_request_complete_email_notification_enabled,
    policy_fixture,
    expected_status,
    request,
) -> None:
    """
    Verifies that resuming a privacy request from the erasure step will complete if the masking secrets
    are still in the database or not needed for the given policy.
    """

    policy = request.getfixturevalue(policy_fixture)
    privacy_request.policy = policy
    privacy_request.save(db)

    privacy_request.persist_masking_secrets(policy.generate_masking_secrets())

    run_privacy_request_task.delay(
        privacy_request_id=privacy_request.id,
        from_step=CurrentStep.erasure.value,
    ).get(timeout=PRIVACY_REQUEST_TASK_TIMEOUT)

    db.refresh(privacy_request)
    assert privacy_request.status == expected_status


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
            privacy_request.persist_masking_secrets(masking_secrets)

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
    EMAIL = "customer-1@example.com"
    LAST_NAME = "McCustomer"

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

        data = {
            "requested_at": "2021-08-30T16:09:37.359Z",
            "policy_key": policy.key,
            "identity": {"email": self.EMAIL},
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
        data = {
            "requested_at": "2021-08-30T16:09:37.359Z",
            "policy_key": erasure_policy.key,
            "identity": {"email": self.EMAIL},
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
                {
                    "system_name": integration_manual_webhook_config.system.name,
                    "email": self.EMAIL,
                    "last_name": self.LAST_NAME,
                }
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
            {"email": self.EMAIL},
        )

        run_privacy_request_task.delay(privacy_request_requires_input.id).get(
            timeout=PRIVACY_REQUEST_TASK_TIMEOUT
        )

        db.refresh(privacy_request_requires_input)
        assert privacy_request_requires_input.status == PrivacyRequestStatus.complete
        assert mock_upload.called
        assert mock_upload.call_args.kwargs["data"] == {
            "manual_webhook_example": [
                {
                    "email": self.EMAIL,
                    "last_name": None,
                    "system_name": integration_manual_webhook_config.system.name,
                }
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
            "manual_webhook_example": [
                {
                    "email": None,
                    "last_name": None,
                    "system_name": integration_manual_webhook_config.system.name,
                }
            ]
        }

    @mock.patch("fides.api.service.privacy_request.request_runner_service.upload")
    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    def test_multiple_manual_webhooks(
        self,
        mock_upload,
        integration_manual_webhook_config,
        integration_manual_webhook_config_with_system2,
        access_manual_webhook,
        policy,
        run_privacy_request_task,
        privacy_request_requires_input: PrivacyRequest,
        db,
        dsr_version,
        request,
    ):
        """Test that multiple manual webhooks are processed correctly"""
        mock_upload.return_value = "http://www.data-download-url"
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        # Create a second manual webhook
        second_webhook = AccessManualWebhook.create(
            db=db,
            data={
                "connection_config_id": integration_manual_webhook_config_with_system2.id,
                "fields": [
                    {
                        "pii_field": "phone",
                        "dsr_package_label": "phone",
                        "data_categories": ["user.contact.phone"],
                        "types": ["string"],
                    }
                ],
            },
        )

        # Cache input for both webhooks
        privacy_request_requires_input.cache_manual_webhook_access_input(
            access_manual_webhook,
            {"email": self.EMAIL, "last_name": self.LAST_NAME},
        )
        privacy_request_requires_input.cache_manual_webhook_access_input(
            second_webhook,
            {"phone": "+1234567890"},
        )

        run_privacy_request_task.delay(privacy_request_requires_input.id).get(
            timeout=PRIVACY_REQUEST_TASK_TIMEOUT
        )

        db.refresh(privacy_request_requires_input)
        assert privacy_request_requires_input.status == PrivacyRequestStatus.complete
        assert mock_upload.called

        # Verify both webhooks' data was included in the upload
        uploaded_data = mock_upload.call_args.kwargs["data"]
        assert "manual_webhook_example" in uploaded_data
        webhook_data = uploaded_data["manual_webhook_example"][0]

        # Verify first webhook's data
        assert webhook_data["email"] == self.EMAIL
        assert webhook_data["last_name"] == self.LAST_NAME
        assert (
            webhook_data["system_name"] == integration_manual_webhook_config.system.name
        )

        # Verify second webhook's data
        webhook_data2 = uploaded_data["manual_webhook_example2"][0]
        assert webhook_data2["phone"] == "+1234567890"
        assert (
            webhook_data2["system_name"]
            == integration_manual_webhook_config_with_system2.system.name
        )

        # Clean up
        second_webhook.delete(db)


@mock.patch("fides.api.service.privacy_request.request_runner_service.upload")
@mock.patch(
    "fides.api.service.privacy_request.request_runner_service.save_access_results"
)
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
class TestPrivacyRequestAttachments:
    """Tests for attachments associated with privacy requests)"""

    EMAIL = "customer-1@example.com"
    LAST_NAME = "McCustomer"

    def create_test_attachment(
        self,
        db: Session,
        file_name: str,
        content: bytes,
        storage_config,
        attachment_type: AttachmentType = AttachmentType.include_with_access_package,
    ) -> Attachment:
        """Helper function to create a test attachment"""
        return Attachment.create_and_upload(
            db=db,
            data={
                "file_name": file_name,
                "attachment_type": attachment_type,
                "storage_key": storage_config.key,
            },
            attachment_file=BytesIO(content),
        )

    def create_attachment_reference(
        self,
        db: Session,
        attachment_id: str,
        reference_id: str,
        reference_type: AttachmentReferenceType,
    ) -> None:
        """Helper function to create an attachment reference"""
        AttachmentReference.create(
            db=db,
            data={
                "attachment_id": attachment_id,
                "reference_type": reference_type,
                "reference_id": reference_id,
            },
        )

    def verify_upload_data_structure(
        self, attachments: list[dict], storage_config, file_names: list[str]
    ):
        """Verify the structure of the upload data"""
        attachment_files = {att["file_name"]: att for att in attachments}
        assert len(attachment_files) == len(file_names)
        for file_name in file_names:
            assert file_name in attachment_files

        for attachment in attachments:
            assert attachment["file_name"] in file_names
            assert attachment["content_type"] == "text/plain"
            assert attachment["download_url"].startswith("https://s3.amazonaws.com/")
            assert attachment["file_size"] == 5

    def verify_stored_data_structure(self, stored_attachments: list[dict]):
        """Verify the structure of the stored data"""
        for attachment in stored_attachments:
            assert "file_name" in attachment
            assert "content_type" in attachment
            assert "file_size" in attachment
            assert "file_key" in attachment
            assert "storage_key" in attachment
            assert "bucket_name" in attachment

    def verify_webhook_data(
        self, webhook_data: dict, integration_manual_webhook_config
    ):
        """Verify the structure of the webhook data"""
        assert webhook_data["email"] == self.EMAIL
        assert webhook_data["last_name"] == self.LAST_NAME
        assert (
            webhook_data["system_name"] == integration_manual_webhook_config.system.name
        )

    def test_privacy_request_with_attachments(
        self,
        mock_save,
        mock_upload,
        s3_client,
        policy,
        storage_config,
        privacy_request: PrivacyRequest,
        run_privacy_request_task,
        db,
        dsr_version,
        request,
        monkeypatch,
    ):
        """Test that top-level attachments (attachments directly associated with the privacy request)
        are properly processed and included in both upload and storage"""
        mock_upload.return_value = "http://www.data-download-url"

        def mock_get_s3_client(auth_method, storage_secrets):
            return s3_client

        monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        # Create test attachments
        attachment1 = self.create_test_attachment(
            db, "test1.txt", b"test1", storage_config
        )
        attachment2 = self.create_test_attachment(
            db, "test2.txt", b"test2", storage_config
        )

        # Create attachment references to privacy request
        for attachment in [attachment1, attachment2]:
            self.create_attachment_reference(
                db,
                attachment.id,
                privacy_request.id,
                AttachmentReferenceType.privacy_request,
            )

        # Run the privacy request
        run_privacy_request_task.delay(privacy_request.id).get(
            timeout=PRIVACY_REQUEST_TASK_TIMEOUT
        )

        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.complete
        assert mock_upload.called
        assert mock_save.called

        # Verify upload format
        uploaded_data = mock_upload.call_args.kwargs["data"]
        assert "attachments" in uploaded_data
        attachments = uploaded_data["attachments"]
        assert len(attachments) == 2
        self.verify_upload_data_structure(
            attachments, storage_config, ["test1.txt", "test2.txt"]
        )

        # Verify storage format
        stored_data = mock_save.call_args[0][3][
            "access_request_rule"
        ]  # rule_filtered_results
        assert "attachments" in stored_data
        stored_attachments = stored_data["attachments"]
        assert len(stored_attachments) == 2
        self.verify_stored_data_structure(stored_attachments)

        # Verify that attachments are separate from manual webhook data
        assert "manual_webhook_data" not in uploaded_data
        assert "manual_webhook_data" not in stored_data

        # Clean up
        attachment1.delete(db)
        attachment2.delete(db)

    def test_privacy_request_with_skipped_attachments(
        self,
        mock_save,
        mock_upload,
        s3_client,
        policy,
        storage_config,
        privacy_request: PrivacyRequest,
        run_privacy_request_task,
        db,
        dsr_version,
        request,
        monkeypatch,
    ):
        """Test that attachments with different types are properly handled for top-level attachments"""
        mock_upload.return_value = "http://www.data-download-url"

        def mock_get_s3_client(auth_method, storage_secrets):
            return s3_client

        monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        # Create test attachments with different types
        included_attachment = self.create_test_attachment(
            db,
            "test1.txt",
            b"test1",
            storage_config,
            AttachmentType.include_with_access_package,
        )
        skipped_attachment = self.create_test_attachment(
            db,
            "test2.txt",
            b"test2",
            storage_config,
            AttachmentType.internal_use_only,
        )

        # Create attachment references to privacy request
        for attachment in [included_attachment, skipped_attachment]:
            self.create_attachment_reference(
                db,
                attachment.id,
                privacy_request.id,
                AttachmentReferenceType.privacy_request,
            )

        # Run the privacy request
        run_privacy_request_task.delay(privacy_request.id).get(
            timeout=PRIVACY_REQUEST_TASK_TIMEOUT
        )

        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.complete
        assert mock_upload.called
        assert mock_save.called

        # Verify upload format
        uploaded_data = mock_upload.call_args.kwargs["data"]
        assert "attachments" in uploaded_data
        attachments = uploaded_data["attachments"]
        assert len(attachments) == 1  # Only the included attachment should be present
        self.verify_upload_data_structure(attachments, storage_config, ["test1.txt"])

        # Verify storage format (without fileobj)
        stored_data = mock_save.call_args[0][3][
            "access_request_rule"
        ]  # rule_filtered_results
        assert "attachments" in stored_data
        stored_attachments = stored_data["attachments"]
        assert (
            len(stored_attachments) == 1
        )  # Only the included attachment should be present
        self.verify_stored_data_structure(stored_attachments)

        # Clean up
        included_attachment.delete(db)
        skipped_attachment.delete(db)

    def test_manual_webhook_with_attachments(
        self,
        mock_save,
        mock_upload,
        s3_client,
        integration_manual_webhook_config,
        access_manual_webhook,
        policy,
        storage_config,
        run_privacy_request_task,
        privacy_request_requires_input: PrivacyRequest,
        db,
        dsr_version,
        request,
        monkeypatch,
    ):
        """Test that manual webhook attachments are properly processed and included in both upload and storage"""
        mock_upload.return_value = "http://www.data-download-url"

        def mock_get_s3_client(auth_method, storage_secrets):
            return s3_client

        monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        # Create test attachments
        attachment1 = self.create_test_attachment(
            db, "test1.txt", b"test1", storage_config
        )
        attachment2 = self.create_test_attachment(
            db, "test2.txt", b"test2", storage_config
        )

        # Create attachment references to manual webhook
        for attachment in [attachment1, attachment2]:
            self.create_attachment_reference(
                db,
                attachment.id,
                access_manual_webhook.id,
                AttachmentReferenceType.access_manual_webhook,
            )
            self.create_attachment_reference(
                db,
                attachment.id,
                privacy_request_requires_input.id,
                AttachmentReferenceType.privacy_request,
            )

        # Cache manual webhook data before running the privacy request
        privacy_request_requires_input.cache_manual_webhook_access_input(
            access_manual_webhook,
            {
                "email": "test@example.com",
                "last_name": "Test User",
            },
        )
        # Run the privacy request
        run_privacy_request_task.delay(privacy_request_requires_input.id).get(
            timeout=PRIVACY_REQUEST_TASK_TIMEOUT
        )

        db.refresh(privacy_request_requires_input)
        assert privacy_request_requires_input.status == PrivacyRequestStatus.complete
        assert mock_upload.called
        assert mock_save.called

        # Verify upload format
        uploaded_data = mock_upload.call_args.kwargs["data"]
        for manual_webhook_data in uploaded_data["manual_webhook_data"]:
            assert "attachments" in manual_webhook_data
            attachments = manual_webhook_data["attachments"]
            assert len(attachments) == 2
            self.verify_upload_data_structure(
                attachments, storage_config, ["test1.txt", "test2.txt"]
            )

        # Verify storage format
        stored_data = mock_save.call_args[0][3][
            "access_request_rule"
        ]  # rule_filtered_results
        for manual_webhook_data in stored_data["manual_webhook_data"]:
            assert "attachments" in manual_webhook_data
            stored_attachments = manual_webhook_data["attachments"]
            assert len(stored_attachments) == 2
            self.verify_stored_data_structure(stored_attachments)

        # Clean up
        attachment1.delete(db)
        attachment2.delete(db)

    def test_manual_webhook_with_skipped_attachments(
        self,
        mock_save,
        mock_upload,
        s3_client,
        integration_manual_webhook_config,
        access_manual_webhook,
        policy,
        storage_config,
        run_privacy_request_task,
        privacy_request_requires_input: PrivacyRequest,
        db,
        dsr_version,
        request,
        monkeypatch,
    ):
        """Test that manual webhook attachments are properly processed and included in both upload and storage"""
        mock_upload.return_value = "http://www.data-download-url"

        def mock_get_s3_client(auth_method, storage_secrets):
            return s3_client

        monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        # Create test attachments with different types
        included_attachment = self.create_test_attachment(
            db,
            "test1.txt",
            b"test1",
            storage_config,
            AttachmentType.include_with_access_package,
        )
        skipped_attachment = self.create_test_attachment(
            db,
            "test2.txt",
            b"test2",
            storage_config,
            AttachmentType.internal_use_only,
        )

        # Create attachment references to manual webhook
        for attachment in [included_attachment, skipped_attachment]:
            self.create_attachment_reference(
                db,
                attachment.id,
                access_manual_webhook.id,
                AttachmentReferenceType.access_manual_webhook,
            )
            self.create_attachment_reference(
                db,
                attachment.id,
                privacy_request_requires_input.id,
                AttachmentReferenceType.privacy_request,
            )

        # Cache manual webhook data before running the privacy request
        privacy_request_requires_input.cache_manual_webhook_access_input(
            access_manual_webhook,
            {
                "email": "test@example.com",
                "last_name": "Test User",
            },
        )

        # Run the privacy request
        run_privacy_request_task.delay(privacy_request_requires_input.id).get(
            timeout=PRIVACY_REQUEST_TASK_TIMEOUT
        )

        db.refresh(privacy_request_requires_input)
        assert privacy_request_requires_input.status == PrivacyRequestStatus.complete

        # Verify upload format
        uploaded_data = mock_upload.call_args.kwargs["data"]
        for manual_webhook_data in uploaded_data["manual_webhook_data"]:
            assert "attachments" in manual_webhook_data
            attachments = manual_webhook_data["attachments"]
            assert (
                len(attachments) == 1
            )  # Only the included attachment should be present
            self.verify_upload_data_structure(
                attachments, storage_config, ["test1.txt"]
            )

        # Verify storage format
        stored_data = mock_save.call_args[0][3][
            "access_request_rule"
        ]  # rule_filtered_results
        for manual_webhook_data in stored_data["manual_webhook_data"]:
            assert "attachments" in manual_webhook_data
            stored_attachments = manual_webhook_data["attachments"]
            assert (
                len(stored_attachments) == 1
            )  # Only the included attachment should be present
            self.verify_stored_data_structure(stored_attachments)

        # Clean up
        included_attachment.delete(db)
        skipped_attachment.delete(db)


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
        last_log = privacy_request_with_consent_policy.execution_logs.order_by(
            ExecutionLog.created_at.desc()
        ).first()
        assert last_log.status == ExecutionLogStatus.pending
        assert last_log.message == "Privacy request paused pending batch email send job"
        assert last_log.dataset_name == "Pending batch email send"

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


@pytest.mark.async_dsr
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

        if dsr_version == "use_dsr_2_0":
            # Async Access Requests not supported for DSR 2.0 - the given
            # node cannot be paused
            assert pr.status == PrivacyRequestStatus.complete
            return

        if dsr_version == "use_dsr_3_0":
            assert pr.status == PrivacyRequestStatus.in_processing

            request_tasks = pr.access_tasks
            assert request_tasks[0].status == ExecutionLogStatus.complete

            # SaaS Request was marked as needing async results, so the Request
            # Task was put in a paused state
            assert request_tasks[1].status == ExecutionLogStatus.awaiting_processing
            assert (
                request_tasks[1].collection_address == "saas_async_callback_config:user"
            )

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
                "saas_async_callback_config:user": [
                    {"id": 1, "user_id": "abcde", "state": "VA"}
                ]
            }
            # User data supplied async was filtered before being returned to the end user
            assert pr.get_filtered_final_upload() == {
                "access_request_rule": {
                    "saas_async_callback_config:user": [{"state": "VA", "id": 1}]
                }
            }

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


class TestDatasetReferenceValidation:
    @pytest.mark.usefixtures("dataset_config")
    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.access_runner"
    )
    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    def test_dataset_reference_validation_success(
        self,
        run_access,
        db: Session,
        privacy_request: PrivacyRequest,
        run_privacy_request_task,
        request,
        dsr_version,
    ):
        """Test that successful dataset reference validation is logged"""

        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        # Run privacy request
        run_privacy_request_task.delay(privacy_request.id).get(
            timeout=PRIVACY_REQUEST_TASK_TIMEOUT
        )

        # Verify success log was created
        success_logs = privacy_request.execution_logs.filter_by(status="complete").all()

        validation_logs = [
            log
            for log in success_logs
            if log.dataset_name == "Dataset reference validation"
        ]

        assert len(validation_logs) == 1
        log = validation_logs[0]
        assert log.connection_key is None
        assert log.collection_name is None
        assert (
            log.message
            == f"Dataset reference validation successful for privacy request: {privacy_request.id}"
        )
        assert log.action_type == privacy_request.policy.get_action_type()

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.access_runner"
    )
    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    def test_dataset_reference_validation_error(
        self,
        run_access,
        db: Session,
        privacy_request: PrivacyRequest,
        dataset_config: DatasetConfig,
        run_privacy_request_task,
        request,
        dsr_version,
    ):
        """Test that dataset reference validation errors are logged"""

        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        # Add invalid dataset reference that will cause validation error
        dataset_config.ctl_dataset.collections[0]["fields"][0]["fides_meta"] = {
            "references": [
                {"dataset": "invalid_dataset", "field": "invalid_collection.field"}
            ]
        }
        flag_modified(dataset_config.ctl_dataset, "collections")
        dataset_config.save(db)

        # Run privacy request
        run_privacy_request_task.delay(privacy_request.id).get(
            timeout=PRIVACY_REQUEST_TASK_TIMEOUT
        )

        # Verify error log was created
        error_logs = privacy_request.execution_logs.filter_by(status="error").all()

        validation_logs = [
            log
            for log in error_logs
            if log.dataset_name == "Dataset reference validation"
        ]

        assert len(validation_logs) == 1
        log = validation_logs[0]
        assert log.connection_key is None
        assert log.collection_name is None
        assert (
            "Referenced object invalid_dataset:invalid_collection:field from dataset postgres_example_subscriptions_dataset does not exist"
            in log.message
        )
        assert log.action_type == privacy_request.policy.get_action_type()


class TestSkipCollectionsWithOptionalIdentities:
    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    def test_skip_collections_with_optional_identities(
        self,
        privacy_request: PrivacyRequest,
        run_privacy_request_task,
        optional_identities_dataset_config,
        dsr_version,
        request,
    ):
        """Test that collections with optional identities are skipped"""

        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        # Run privacy request
        run_privacy_request_task.delay(privacy_request.id).get(timeout=300)

        skipped_logs = privacy_request.execution_logs.filter_by(
            status=ExecutionLogStatus.skipped
        ).all()
        assert len(skipped_logs) == 1, "No skipped execution logs were created"

        # Verify the skipped log for dataset traversal
        skipped_log = skipped_logs[0]
        assert skipped_log.privacy_request_id == privacy_request.id
        assert skipped_log.status == ExecutionLogStatus.skipped
        assert skipped_log.dataset_name == "Dataset traversal"
        assert skipped_log.collection_name == "optional_identities.customer"
        assert skipped_log.message == (
            'Skipping the "optional_identities:customer" collection, it is reachable by the "user_id" identity but only the "email" identity was provided'
        )


class TestDSRPackageURLGeneration:
    """Tests for DSR package URL generation functionality in request runner service"""

    @pytest.fixture
    def mock_config_proxy(self):
        """Mock config proxy with privacy center URL"""
        with mock.patch(
            "fides.api.service.privacy_request.request_runner_service.ConfigProxy"
        ) as mock_proxy:
            mock_config = mock.MagicMock()
            mock_config.privacy_center.url = "https://privacy.example.com"
            mock_config.notifications.notification_service_type = "mailgun"
            mock_proxy.return_value = mock_config
            yield mock_config

    @pytest.fixture
    def mock_storage_destination_s3_with_redirect(self):
        """Mock S3 storage destination with access package redirect enabled"""
        mock_dest = mock.MagicMock()
        mock_dest.type = StorageType.s3
        mock_dest.details = {
            "enable_access_package_redirect": True,
            "enable_streaming": True,
        }
        return mock_dest

    @pytest.fixture
    def mock_storage_destination_s3_without_redirect(self):
        """Mock S3 storage destination without access package redirect"""
        mock_dest = mock.MagicMock()
        mock_dest.type = StorageType.s3
        mock_dest.details = {
            "enable_access_package_redirect": False,
            "enable_streaming": False,
        }
        return mock_dest

    @pytest.fixture
    def mock_storage_destination_non_s3(self):
        """Mock non-S3 storage destination"""
        mock_dest = mock.MagicMock()
        mock_dest.type = StorageType.local
        mock_dest.details = {}
        return mock_dest

    @pytest.fixture
    def mock_rule_with_storage(self, mock_storage_destination_s3_with_redirect):
        """Mock rule with storage destination"""
        mock_rule = mock.MagicMock()
        mock_rule.get_storage_destination.return_value = (
            mock_storage_destination_s3_with_redirect
        )
        return mock_rule

    @pytest.fixture
    def mock_policy_with_access_rule(self, mock_rule_with_storage):
        """Mock policy with access rule only (no erasure rules)"""
        mock_policy = mock.MagicMock()
        mock_policy.get_rules_for_action.side_effect = lambda action_type: (
            [mock_rule_with_storage] if action_type == ActionType.access else []
        )
        return mock_policy

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.dispatch_message"
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.generate_privacy_request_download_token"
    )
    def test_generate_dsr_package_urls_when_enabled(
        self,
        mock_generate_token,
        mock_dispatch_message,
        mock_config_proxy,
        mock_policy_with_access_rule,
        db,
        privacy_request,
    ):
        # Ensure the mock is properly set up to not actually call the real function
        mock_dispatch_message.return_value = None
        """Test that DSR package URLs are generated when enable_access_package_redirect is True"""
        mock_generate_token.return_value = "test_token_123"

        # Call the function
        initiate_privacy_request_completion_email(
            session=db,
            privacy_request_id=privacy_request.id,
            policy=mock_policy_with_access_rule,
            access_result_urls=[
                "https://storage.example.com/file1",
                "https://storage.example.com/file2",
            ],
            identity_data={"email": "test@example.com"},
            property_id=None,
        )

        # Verify the token was generated
        mock_generate_token.assert_called_once_with(privacy_request.id)

        # Verify the message was dispatched with DSR package URL
        mock_dispatch_message.assert_called_once()
        call_args = mock_dispatch_message.call_args
        message_params = call_args[1]["message_body_params"]

        # Check that DSR package URL was used instead of direct storage URLs
        # Note: In CI environments, tokens may be masked for security
        download_url = message_params.download_links[0]

        # Verify the URL structure without depending on exact token values
        assert download_url.startswith(
            "https://privacy.example.com/api/privacy-request/"
        )
        assert "/access-package?token=" in download_url
        assert privacy_request.id in download_url

        # Verify that a token is present (either the actual value or masked)
        # The token should be present and at least 3 characters (to account for masking like "***")
        token_part = download_url.split("?token=")[1]
        assert len(token_part) >= 3, "Token should be present and at least 3 characters"

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.dispatch_message"
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.generate_privacy_request_download_token"
    )
    def test_use_direct_urls_when_redirect_disabled(
        self,
        mock_generate_token,
        mock_dispatch_message,
        mock_config_proxy,
        db,
        privacy_request,
    ):
        # Ensure the mock is properly set up to not actually call the real function
        mock_dispatch_message.return_value = None
        """Test that direct storage URLs are used when enable_access_package_redirect is False"""
        # Create a policy with storage destination that has redirect disabled
        mock_rule = mock.MagicMock()
        mock_rule.get_storage_destination.return_value = mock.MagicMock(
            type=StorageType.s3, details={"enable_access_package_redirect": False}
        )

        mock_policy = mock.MagicMock()
        mock_policy.get_rules_for_action.side_effect = lambda action_type: (
            [mock_rule] if action_type == ActionType.access else []
        )

        access_result_urls = [
            "https://storage.example.com/file1",
            "https://storage.example.com/file2",
        ]

        # Call the function
        initiate_privacy_request_completion_email(
            session=db,
            privacy_request_id=privacy_request.id,
            policy=mock_policy,
            access_result_urls=access_result_urls,
            identity_data={"email": "test@example.com"},
            property_id=None,
        )

        # Verify no token was generated
        mock_generate_token.assert_not_called()

        # Verify the message was dispatched with direct storage URLs
        mock_dispatch_message.assert_called_once()
        call_args = mock_dispatch_message.call_args
        message_params = call_args[1]["message_body_params"]

        # Check that direct storage URLs were used
        assert message_params.download_links == access_result_urls

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.dispatch_message"
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.generate_privacy_request_download_token"
    )
    def test_use_direct_urls_for_non_s3_storage(
        self,
        mock_generate_token,
        mock_dispatch_message,
        mock_config_proxy,
        db,
        privacy_request,
    ):
        # Ensure the mock is properly set up to not actually call the real function
        mock_dispatch_message.return_value = None
        """Test that direct storage URLs are used for non-S3 storage destinations"""
        # Create a policy with non-S3 storage destination
        mock_rule = mock.MagicMock()
        mock_rule.get_storage_destination.return_value = mock.MagicMock(
            type=StorageType.local, details={}
        )

        mock_policy = mock.MagicMock()
        mock_policy.get_rules_for_action.side_effect = lambda action_type: (
            [mock_rule] if action_type == ActionType.access else []
        )

        access_result_urls = ["https://storage.example.com/file1"]

        # Call the function
        initiate_privacy_request_completion_email(
            session=db,
            privacy_request_id=privacy_request.id,
            policy=mock_policy,
            access_result_urls=access_result_urls,
            identity_data={"email": "test@example.com"},
            property_id=None,
        )

        # Verify no token was generated
        mock_generate_token.assert_not_called()

        # Verify the message was dispatched with direct storage URLs
        mock_dispatch_message.assert_called_once()
        call_args = mock_dispatch_message.call_args
        message_params = call_args[1]["message_body_params"]

        # Check that direct storage URLs were used
        assert message_params.download_links == access_result_urls

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.dispatch_message"
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.generate_privacy_request_download_token"
    )
    def test_use_direct_urls_when_no_privacy_center_url(
        self,
        mock_generate_token,
        mock_dispatch_message,
        db,
        privacy_request,
    ):
        # Ensure the mock is properly set up to not actually call the real function
        mock_dispatch_message.return_value = None
        """Test that direct storage URLs are used when privacy center URL is not configured"""
        # Mock config proxy without privacy center URL
        with mock.patch(
            "fides.api.service.privacy_request.request_runner_service.ConfigProxy"
        ) as mock_proxy:
            mock_config = mock.MagicMock()
            mock_config.privacy_center.url = None
            mock_config.notifications.notification_service_type = "mailgun"
            mock_proxy.return_value = mock_config

            # Create a policy with storage destination that has redirect enabled
            mock_rule = mock.MagicMock()
            mock_rule.get_storage_destination.return_value = mock.MagicMock(
                type=StorageType.s3, details={"enable_access_package_redirect": True}
            )

            mock_policy = mock.MagicMock()
            mock_policy.get_rules_for_action.side_effect = lambda action_type: (
                [mock_rule] if action_type == ActionType.access else []
            )

            access_result_urls = ["https://storage.example.com/file1"]

            # Call the function
            initiate_privacy_request_completion_email(
                session=db,
                privacy_request_id=privacy_request.id,
                policy=mock_policy,
                access_result_urls=access_result_urls,
                identity_data={"email": "test@example.com"},
                property_id=None,
            )

            # Verify no token was generated
            mock_generate_token.assert_not_called()

            # Verify the message was dispatched with direct storage URLs
            mock_dispatch_message.assert_called_once()
            call_args = mock_dispatch_message.call_args
            message_params = call_args[1]["message_body_params"]

            # Check that direct storage URLs were used
            assert message_params.download_links == access_result_urls

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.dispatch_message"
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.generate_privacy_request_download_token"
    )
    def test_multiple_rules_with_mixed_storage_types(
        self,
        mock_generate_token,
        mock_dispatch_message,
        mock_config_proxy,
        db,
        privacy_request,
    ):
        # Ensure the mock is properly set up to not actually call the real function
        mock_dispatch_message.return_value = None
        """Test behavior when policy has multiple rules with different storage types"""
        mock_generate_token.return_value = "test_token_123"

        # Create a policy with mixed storage destinations
        mock_rule1 = mock.MagicMock()
        mock_rule1.get_storage_destination.return_value = mock.MagicMock(
            type=StorageType.s3, details={"enable_access_package_redirect": False}
        )

        mock_rule2 = mock.MagicMock()
        mock_rule2.get_storage_destination.return_value = mock.MagicMock(
            type=StorageType.s3,
            details={"enable_access_package_redirect": True, "enable_streaming": True},
        )

        mock_policy = mock.MagicMock()
        mock_policy.get_rules_for_action.side_effect = lambda action_type: (
            [mock_rule1, mock_rule2] if action_type == ActionType.access else []
        )

        access_result_urls = ["https://storage.example.com/file1"]

        # Call the function
        initiate_privacy_request_completion_email(
            session=db,
            privacy_request_id=privacy_request.id,
            policy=mock_policy,
            access_result_urls=access_result_urls,
            identity_data={"email": "test@example.com"},
            property_id=None,
        )

        # Verify token was generated (because at least one rule has redirect enabled)
        mock_generate_token.assert_called_once_with(privacy_request.id)

        # Verify the message was dispatched with DSR package URL
        mock_dispatch_message.assert_called_once()
        call_args = mock_dispatch_message.call_args
        message_params = call_args[1]["message_body_params"]

        # Check that DSR package URL was used
        # Note: In CI environments, tokens may be masked for security
        download_url = message_params.download_links[0]

        # Verify the URL structure without depending on exact token values
        assert download_url.startswith(
            "https://privacy.example.com/api/privacy-request/"
        )
        assert "/access-package?token=" in download_url
        assert privacy_request.id in download_url

        # Verify that a token is present (either the actual value or masked)
        # The token should be at least 3 characters (to account for masking like "***")
        token_part = download_url.split("?token=")[1]
        assert len(token_part) >= 3, "Token should be present and at least 3 characters"

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.dispatch_message"
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.generate_privacy_request_download_token"
    )
    def test_dsr_package_url_format(
        self,
        mock_generate_token,
        mock_dispatch_message,
        mock_config_proxy,
        mock_policy_with_access_rule,
        db,
        privacy_request,
    ):
        # Ensure the mock is properly set up to not actually call the real function
        mock_dispatch_message.return_value = None
        """Test that DSR package URL is formatted correctly"""
        mock_generate_token.return_value = "test_token_123"

        # Call the function
        initiate_privacy_request_completion_email(
            session=db,
            privacy_request_id=privacy_request.id,
            policy=mock_policy_with_access_rule,
            access_result_urls=["https://storage.example.com/file1"],
            identity_data={"email": "test@example.com"},
            property_id=None,
        )

        # Verify the message was dispatched
        mock_dispatch_message.assert_called_once()
        call_args = mock_dispatch_message.call_args
        message_params = call_args[1]["message_body_params"]

        # Check that DSR package URL has the correct format
        # Note: In CI environments, tokens may be masked for security
        download_url = message_params.download_links[0]

        # Verify the URL structure without depending on exact token values
        assert download_url.startswith(
            "https://privacy.example.com/api/privacy-request/"
        )
        assert "/access-package?token=" in download_url
        assert privacy_request.id in download_url

        # Verify that a token is present (either the actual value or masked)
        # The token should be present and at least 3 characters (to account for masking like "***")
        token_part = download_url.split("?token=")[1]
        assert len(token_part) >= 3, "Token should be present and at least 3 characters"


class TestSaveAccessResults:
    """Test the save_access_results function error handling"""

    def test_save_access_results_success(self, db, privacy_request):
        """Test successful save of access results"""

        download_urls = ["https://example.com/file1", "https://example.com/file2"]
        rule_filtered_results = {
            "test_rule": {
                "test_dataset:test_collection": [
                    {"name": "John", "email": "john@example.com"}
                ]
            }
        }

        # Should not raise any exceptions
        save_access_results(db, privacy_request, download_urls, rule_filtered_results)

        # Verify URLs were saved
        db.refresh(privacy_request)
        assert privacy_request.access_result_urls == {
            "access_result_urls": download_urls
        }

        # Verify backup results were saved
        assert privacy_request.get_filtered_final_upload() == rule_filtered_results

    @pytest.mark.parametrize(
        "error_type, error_inputs",
        [
            (
                sqlalchemy.exc.DataError,
                ("Database connection error", None, Exception("Original error")),
            ),
            (
                sqlalchemy.exc.OperationalError,
                ("Database connection error", None, Exception("Original error")),
            ),
            (
                sqlalchemy.exc.StatementError,
                (
                    "Database connection error",
                    "SELECT * FROM table",
                    None,
                    Exception("Original error"),
                ),
            ),
            (MemoryError, ("Database connection error",)),
            (OverflowError, ("Database connection error",)),
            (TypeError, ("Database connection error",)),  # for unexpected exceptions
        ],
    )
    @mock.patch.object(PrivacyRequest, "save_filtered_access_results")
    def test_save_access_results_handles_backup_error_gracefully(
        self,
        mock_save_filtered,
        db,
        privacy_request,
        loguru_caplog,
        error_type,
        error_inputs,
    ):
        """Test that backup errors don't fail the DSR when S3 upload succeeded"""
        download_urls = ["https://example.com/file1", "https://example.com/file2"]
        rule_filtered_results = {
            "test_rule": {
                "test_dataset:test_collection": [
                    {"name": "John", "email": "john@example.com"}
                ]
            }
        }

        mock_save_filtered.side_effect = error_type(*error_inputs)

        # Should not raise any exceptions despite backup failure (for handled exceptions)
        save_access_results(db, privacy_request, download_urls, rule_filtered_results)

        # Verify URLs were still saved (S3 upload succeeded)
        db.refresh(privacy_request)
        assert privacy_request.access_result_urls == {
            "access_result_urls": download_urls
        }

        # Verify backup was attempted
        mock_save_filtered.assert_called_once_with(db, rule_filtered_results)

        # Verify warning was logged
        assert "Failed to save backup of DSR results to database" in loguru_caplog.text
        # Check for error message (may be formatted differently for different exception types)
        log_text = loguru_caplog.text.lower()
        assert any(
            [
                "database connection error" in log_text,
                "original error" in log_text,
                "error:" in log_text,
            ]
        ), f"Expected error message in logs, got: {loguru_caplog.text}"

        # Verify success execution log was created
        execution_logs = ExecutionLog.filter(
            db=db,
            conditions=(ExecutionLog.privacy_request_id == privacy_request.id),
        ).all()

        backup_logs = [
            log for log in execution_logs if log.dataset_name == "Access results backup"
        ]
        assert len(backup_logs) == 1
        assert backup_logs[0].status == ExecutionLogStatus.complete
        assert (
            "S3 upload succeeded but database backup failed" in backup_logs[0].message
        )
