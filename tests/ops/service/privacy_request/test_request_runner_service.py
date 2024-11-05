# pylint: disable=missing-docstring, redefined-outer-name
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Set
from unittest import mock
from unittest.mock import ANY, Mock, call
from uuid import uuid4

import pydash
import pytest
from boto3.dynamodb.types import TypeDeserializer
from pydantic import ValidationError
from sqlalchemy import column, select, table
from sqlalchemy.orm import Session

from fides.api.common_exceptions import (
    ClientUnsuccessfulException,
    PrivacyRequestPaused,
)
from fides.api.graph.config import CollectionAddress, FieldPath
from fides.api.graph.graph import DatasetGraph
from fides.api.models.application_config import ApplicationConfig
from fides.api.models.audit_log import AuditLog, AuditLogAction
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
from fides.api.schemas.masking.masking_configuration import (
    HmacMaskingConfiguration,
    MaskingConfiguration,
)
from fides.api.schemas.masking.masking_secrets import MaskingSecretCache
from fides.api.schemas.messaging.messaging import (
    AccessRequestCompleteBodyParams,
    MessagingActionType,
    MessagingServiceType,
)
from fides.api.schemas.policy import Rule
from fides.api.schemas.privacy_request import Consent
from fides.api.schemas.redis_cache import Identity
from fides.api.schemas.saas.saas_config import SaaSRequest
from fides.api.schemas.saas.shared_schemas import HTTPMethod, SaaSRequestParams
from fides.api.service.connectors.dynamodb_connector import DynamoDBConnector
from fides.api.service.connectors.redshift_connector import RedshiftConnector
from fides.api.service.connectors.saas_connector import SaaSConnector
from fides.api.service.connectors.snowflake_connector import SnowflakeConnector
from fides.api.service.masking.strategy.masking_strategy import MaskingStrategy
from fides.api.service.masking.strategy.masking_strategy_hmac import HmacMaskingStrategy
from fides.api.service.privacy_request.request_runner_service import (
    build_consent_dataset_graph,
    needs_batch_email_send,
    run_webhooks_and_report_status,
)
from fides.api.util.data_category import DataCategory
from fides.common.api.v1.urn_registry import REQUEST_TASK_CALLBACK, V1_URL_PREFIX
from fides.config import CONFIG

PRIVACY_REQUEST_TASK_TIMEOUT = 5
# External services take much longer to return
PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL = 60


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


@pytest.mark.integration_postgres
@pytest.mark.integration
@mock.patch("fides.api.service.privacy_request.request_runner_service.upload")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_upload_access_results_has_data_category_field_mapping(
    upload_mock: Mock,
    postgres_example_test_dataset_config_read_access,
    postgres_integration_db,
    db,
    policy,
    dsr_version,
    request,
    run_privacy_request_task,
):
    """
    Ensure we are passing along a correctly populated data_category_field_mapping to the 'upload' function
    that publishes the access request output.
    """
    upload_mock.return_value = "http://www.data-download-url"

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

    # sanity check that acccess results returned as expected
    results = pr.get_raw_access_results()
    assert len(results.keys()) == 11

    # what we're really testing - ensure data_category_field_mapping arg is well-populated
    args, kwargs = upload_mock.call_args
    data_category_field_mapping = kwargs["data_category_field_mapping"]

    # make sure the category field mapping generally looks as we expect
    address_mapping = data_category_field_mapping[
        CollectionAddress.from_string("postgres_example_test_dataset:address")
    ]
    assert len(address_mapping) >= 5
    assert address_mapping["user.contact.address.street"] == [
        FieldPath("house"),
        FieldPath("street"),
    ]
    product_mapping = data_category_field_mapping[
        CollectionAddress.from_string("postgres_example_test_dataset:product")
    ]
    assert len(product_mapping) >= 1
    assert product_mapping["system.operations"] == [
        FieldPath(
            "id",
        ),
        FieldPath(
            "name",
        ),
        FieldPath(
            "price",
        ),
    ]


@pytest.mark.integration_postgres
@pytest.mark.integration
@mock.patch("fides.api.service.privacy_request.request_runner_service.upload")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_upload_access_results_has_data_use_map(
    upload_mock: Mock,
    postgres_example_test_dataset_config_read_access,
    postgres_integration_db,
    db,
    policy,
    dsr_version,
    request,
    run_privacy_request_task,
):
    """
    Ensure we are passing along a correctly populated data_use_map to the 'upload' function
    that publishes the access request output.
    """
    upload_mock.return_value = "http://www.data-download-url"

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

    # sanity check that access results returned as expected
    results = pr.get_raw_access_results()
    assert len(results.keys()) == 11

    # what we're really testing - ensure data_use_map arg is well-populated
    args, kwargs = upload_mock.call_args
    data_use_map = kwargs["data_use_map"]

    assert data_use_map == {
        "postgres_example_test_dataset:report": "{'marketing.advertising'}",
        "postgres_example_test_dataset:employee": "{'marketing.advertising'}",
        "postgres_example_test_dataset:customer": "{'marketing.advertising'}",
        "postgres_example_test_dataset:service_request": "{'marketing.advertising'}",
        "postgres_example_test_dataset:visit": "{'marketing.advertising'}",
        "postgres_example_test_dataset:address": "{'marketing.advertising'}",
        "postgres_example_test_dataset:login": "{'marketing.advertising'}",
        "postgres_example_test_dataset:orders": "{'marketing.advertising'}",
        "postgres_example_test_dataset:payment_card": "{'marketing.advertising'}",
        "postgres_example_test_dataset:order_item": "{'marketing.advertising'}",
        "postgres_example_test_dataset:product": "{'marketing.advertising'}",
    }


@pytest.mark.integration_postgres
@pytest.mark.integration
@mock.patch("fides.api.models.privacy_request.PrivacyRequest.trigger_policy_webhook")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_access_request_postgres(
    trigger_webhook_mock,
    postgres_example_test_dataset_config_read_access,
    postgres_integration_db,
    db,
    cache,
    dsr_version,
    request,
    policy,
    policy_pre_execution_webhooks,
    policy_post_execution_webhooks,
    run_privacy_request_task,
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

    results = pr.get_raw_access_results()
    assert len(results.keys()) == 11

    for key in results.keys():
        assert results[key] is not None
        assert results[key] != {}

    result_key_prefix = f"postgres_example_test_dataset:"
    customer_key = result_key_prefix + "customer"
    assert results[customer_key][0]["email"] == customer_email

    visit_key = result_key_prefix + "visit"
    assert results[visit_key][0]["email"] == customer_email
    log_id = pr.execution_logs[0].id
    pr_id = pr.id

    finished_audit_log: AuditLog = AuditLog.filter(
        db=db,
        conditions=(
            (AuditLog.privacy_request_id == pr_id)
            & (AuditLog.action == AuditLogAction.finished)
        ),
    ).first()

    assert finished_audit_log is not None

    # Both pre-execution webhooks and both post-execution webhooks were called
    assert trigger_webhook_mock.call_count == 4

    for webhook in policy_pre_execution_webhooks:
        webhook.delete(db=db)

    for webhook in policy_post_execution_webhooks:
        webhook.delete(db=db)

    policy.delete(db=db)
    pr.delete(db=db)
    assert not pr in db  # Check that `pr` has been expunged from the session
    assert ExecutionLog.get(db, object_id=log_id).privacy_request_id == pr_id


@pytest.mark.integration_postgres
@pytest.mark.integration
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
@mock.patch("fides.api.models.privacy_request.PrivacyRequest.trigger_policy_webhook")
def test_create_and_process_access_request_with_custom_identities_postgres(
    trigger_webhook_mock,
    postgres_example_test_dataset_config_read_access,
    postgres_example_test_extended_dataset_config,
    postgres_integration_db,
    db,
    cache,
    policy,
    dsr_version,
    request,
    policy_pre_execution_webhooks,
    policy_post_execution_webhooks,
    run_privacy_request_task,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    customer_email = "customer-1@example.com"
    loyalty_id = "CH-1"
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": policy.key,
        "identity": {
            "email": customer_email,
            "loyalty_id": {"label": "Loyalty ID", "value": loyalty_id},
        },
    }

    pr = get_privacy_request_results(
        db,
        policy,
        run_privacy_request_task,
        data,
    )

    results = pr.get_raw_access_results()
    assert len(results.keys()) == 12

    for key in results.keys():
        assert results[key] is not None
        assert results[key] != {}

    result_key_prefix = f"postgres_example_test_dataset:"
    customer_key = result_key_prefix + "customer"
    assert results[customer_key][0]["email"] == customer_email

    visit_key = result_key_prefix + "visit"
    assert results[visit_key][0]["email"] == customer_email

    loyalty_key = f"postgres_example_test_extended_dataset:loyalty"
    assert results[loyalty_key][0]["id"] == loyalty_id

    log_id = pr.execution_logs[0].id
    pr_id = pr.id

    finished_audit_log: AuditLog = AuditLog.filter(
        db=db,
        conditions=(
            (AuditLog.privacy_request_id == pr_id)
            & (AuditLog.action == AuditLogAction.finished)
        ),
    ).first()

    assert finished_audit_log is not None

    # Both pre-execution webhooks and both post-execution webhooks were called
    assert trigger_webhook_mock.call_count == 4

    for webhook in policy_pre_execution_webhooks:
        webhook.delete(db=db)

    for webhook in policy_post_execution_webhooks:
        webhook.delete(db=db)

    policy.delete(db=db)
    pr.delete(db=db)
    assert not pr in db  # Check that `pr` has been expunged from the session
    assert ExecutionLog.get(db, object_id=log_id).privacy_request_id == pr_id


@pytest.mark.integration_postgres
@pytest.mark.integration
@pytest.mark.usefixtures(
    "postgres_example_test_dataset_config_skipped_login_collection",
    "postgres_integration_db",
    "cache",
)
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_access_request_with_valid_skipped_collection(
    db,
    policy,
    run_privacy_request_task,
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

    results = pr.get_raw_access_results()
    assert len(results.keys()) == 10

    assert "login" not in results.keys()

    result_key_prefix = f"postgres_example_test_dataset:"
    customer_key = result_key_prefix + "customer"
    assert results[customer_key][0]["email"] == customer_email

    assert AuditLog.filter(
        db=db,
        conditions=(
            (AuditLog.privacy_request_id == pr.id)
            & (AuditLog.action == AuditLogAction.finished)
        ),
    ).first()


@pytest.mark.integration_postgres
@pytest.mark.integration
@pytest.mark.usefixtures(
    "postgres_example_test_dataset_config_skipped_address_collection",
    "postgres_integration_db",
    "cache",
)
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_access_request_with_invalid_skipped_collection(
    db,
    policy,
    dsr_version,
    request,
    run_privacy_request_task,
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

    results = pr.get_raw_access_results()
    assert len(results.keys()) == 0

    db.refresh(pr)

    assert pr.status == PrivacyRequestStatus.error


@pytest.mark.integration
@mock.patch("fides.api.models.privacy_request.PrivacyRequest.trigger_policy_webhook")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_access_request_mssql(
    trigger_webhook_mock,
    mssql_example_test_dataset_config,
    mssql_integration_db,
    db,
    cache,
    policy,
    dsr_version,
    request,
    policy_pre_execution_webhooks,
    policy_post_execution_webhooks,
    run_privacy_request_task,
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

    results = pr.get_raw_access_results()
    assert len(results.keys()) == 11

    for key in results.keys():
        assert results[key] is not None
        assert results[key] != {}

    result_key_prefix = f"mssql_example_test_dataset:"
    customer_key = result_key_prefix + "customer"
    assert results[customer_key][0]["email"] == customer_email

    visit_key = result_key_prefix + "visit"
    assert results[visit_key][0]["email"] == customer_email
    # Both pre-execution webhooks and both post-execution webhooks were called
    assert trigger_webhook_mock.call_count == 4
    pr.delete(db=db)


@pytest.mark.integration
@pytest.mark.integration_mysql
@mock.patch("fides.api.models.privacy_request.PrivacyRequest.trigger_policy_webhook")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_access_request_mysql(
    trigger_webhook_mock,
    mysql_example_test_dataset_config,
    mysql_integration_db,
    db,
    cache,
    policy,
    dsr_version,
    request,
    policy_pre_execution_webhooks,
    policy_post_execution_webhooks,
    run_privacy_request_task,
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

    results = pr.get_raw_access_results()
    assert len(results.keys()) == 12

    for key in results.keys():
        assert results[key] is not None
        assert results[key] != {}

    result_key_prefix = f"mysql_example_test_dataset:"
    customer_key = result_key_prefix + "customer"
    assert results[customer_key][0]["email"] == customer_email

    visit_key = result_key_prefix + "visit"
    assert results[visit_key][0]["email"] == customer_email
    # Both pre-execution webhooks and both post-execution webhooks were called
    assert trigger_webhook_mock.call_count == 4
    pr.delete(db=db)


@pytest.mark.integration
@pytest.mark.integration_scylladb
@mock.patch("fides.api.models.privacy_request.PrivacyRequest.trigger_policy_webhook")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_access_request_scylladb(
    trigger_webhook_mock,
    scylladb_test_dataset_config,
    scylla_reset_db,
    db,
    cache,
    policy,
    dsr_version,
    request,
    policy_pre_execution_webhooks,
    policy_post_execution_webhooks,
    run_privacy_request_task,
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

    results = pr.get_raw_access_results()
    assert len(results.keys()) == 4

    assert "scylladb_example_test_dataset:users" in results
    assert len(results["scylladb_example_test_dataset:users"]) == 1
    assert results["scylladb_example_test_dataset:users"][0]["email"] == customer_email
    assert results["scylladb_example_test_dataset:users"][0]["age"] == 41
    assert results["scylladb_example_test_dataset:users"][0][
        "alternative_contacts"
    ] == {"phone": "+1 (531) 988-5905", "work_email": "customer-1@example.com"}

    assert "scylladb_example_test_dataset:user_activity" in results
    assert len(results["scylladb_example_test_dataset:user_activity"]) == 3

    for activity in results["scylladb_example_test_dataset:user_activity"]:
        assert activity["user_id"]
        assert activity["timestamp"]
        assert activity["activity_type"]
        assert activity["user_agent"]

    assert "scylladb_example_test_dataset:payment_methods" in results
    assert len(results["scylladb_example_test_dataset:payment_methods"]) == 2
    for payment_method in results["scylladb_example_test_dataset:payment_methods"]:
        assert payment_method["payment_method_id"]
        assert payment_method["card_number"]
        assert payment_method["expiration_date"]

    assert "scylladb_example_test_dataset:orders" in results
    assert len(results["scylladb_example_test_dataset:orders"]) == 2
    for payment_method in results["scylladb_example_test_dataset:orders"]:
        assert payment_method["order_amount"]
        assert payment_method["order_date"]
        assert payment_method["order_description"]

    # Both pre-execution webhooks and both post-execution webhooks were called
    assert trigger_webhook_mock.call_count == 4
    pr.delete(db=db)


@pytest.mark.integration
@pytest.mark.integration_scylladb
@mock.patch("fides.api.models.privacy_request.PrivacyRequest.trigger_policy_webhook")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0"],
)
def test_create_and_process_access_request_scylladb_no_keyspace(
    trigger_webhook_mock,
    scylladb_test_dataset_config_no_keyspace,
    scylla_reset_db,
    db,
    cache,
    policy,
    dsr_version,
    request,
    policy_pre_execution_webhooks,
    policy_post_execution_webhooks,
    run_privacy_request_task,
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

    assert (
        pr.access_tasks.count() == 6
    )  # There's 4 tables plus the root and terminal "dummy" tasks

    # Root task should be completed
    assert pr.access_tasks.first().collection_name == "__ROOT__"
    assert pr.access_tasks.first().status == ExecutionLogStatus.complete

    # All other tasks should be error
    for access_task in pr.access_tasks.offset(1):
        assert access_task.status == ExecutionLogStatus.error

    results = pr.get_raw_access_results()
    assert results == {}


@pytest.mark.integration_external
@pytest.mark.integration_google_cloud_sql_mysql
@mock.patch("fides.api.models.privacy_request.PrivacyRequest.trigger_policy_webhook")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_access_request_google_cloud_sql_mysql(
    trigger_webhook_mock,
    google_cloud_sql_mysql_example_test_dataset_config,
    google_cloud_sql_mysql_integration_db,
    db: Session,
    cache,
    policy,
    dsr_version,
    request,
    policy_pre_execution_webhooks,
    policy_post_execution_webhooks,
    run_privacy_request_task,
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
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )

    results = pr.get_raw_access_results()
    assert len(results.keys()) == 11

    for key in results.keys():
        assert results[key] is not None
        assert results[key] != {}

    result_key_prefix = "google_cloud_sql_mysql_example_test_dataset:"
    customer_key = result_key_prefix + "customer"
    assert results[customer_key][0]["email"] == customer_email

    visit_key = result_key_prefix + "visit"
    assert results[visit_key][0]["email"] == customer_email
    # Both pre-execution webhooks and both post-execution webhooks were called
    assert trigger_webhook_mock.call_count == 4
    pr.delete(db=db)


@pytest.mark.integration_mariadb
@pytest.mark.integration
@mock.patch("fides.api.models.privacy_request.PrivacyRequest.trigger_policy_webhook")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_access_request_mariadb(
    trigger_webhook_mock,
    mariadb_example_test_dataset_config,
    mariadb_integration_db,
    db,
    cache,
    policy,
    dsr_version,
    request,
    policy_pre_execution_webhooks,
    policy_post_execution_webhooks,
    run_privacy_request_task,
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

    results = pr.get_raw_access_results()
    assert len(results.keys()) == 11

    for key in results.keys():
        assert results[key] is not None
        assert results[key] != {}

    result_key_prefix = "mariadb_example_test_dataset:"
    customer_key = result_key_prefix + "customer"
    assert results[customer_key][0]["email"] == customer_email

    visit_key = result_key_prefix + "visit"
    assert results[visit_key][0]["email"] == customer_email
    # Both pre-execution webhooks and both post-execution webhooks were called
    assert trigger_webhook_mock.call_count == 4
    pr.delete(db=db)


@pytest.mark.integration_saas
@mock.patch("fides.api.models.privacy_request.PrivacyRequest.trigger_policy_webhook")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_access_request_saas_mailchimp(
    trigger_webhook_mock,
    mailchimp_connection_config,
    mailchimp_dataset_config,
    db,
    cache,
    policy,
    policy_pre_execution_webhooks,
    policy_post_execution_webhooks,
    dsr_version,
    request,
    mailchimp_identity_email,
    run_privacy_request_task,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    customer_email = mailchimp_identity_email
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
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )
    results = pr.get_raw_access_results()
    assert len(results.keys()) == 3

    for key in results.keys():
        assert results[key] is not None
        assert results[key] != {}

    result_key_prefix = f"mailchimp_instance:"
    member_key = result_key_prefix + "member"
    assert results[member_key][0]["email_address"] == customer_email

    # Both pre-execution webhooks and both post-execution webhooks were called
    assert trigger_webhook_mock.call_count == 4

    pr.delete(db=db)


@pytest.mark.integration_saas
@mock.patch("fides.api.models.privacy_request.PrivacyRequest.trigger_policy_webhook")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_erasure_request_saas(
    _,
    mailchimp_connection_config,
    mailchimp_dataset_config,
    db,
    cache,
    erasure_policy_hmac,
    generate_auth_header,
    dsr_version,
    request,
    mailchimp_identity_email,
    reset_mailchimp_data,
    run_privacy_request_task,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    customer_email = mailchimp_identity_email
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": erasure_policy_hmac.key,
        "identity": {"email": customer_email},
    }

    pr = get_privacy_request_results(
        db,
        erasure_policy_hmac,
        run_privacy_request_task,
        data,
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )

    connector = SaaSConnector(mailchimp_connection_config)
    connector.set_saas_request_state(
        SaaSRequest(path="test_path", method=HTTPMethod.GET)
    )  # dummy request as connector requires it
    request: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.GET,
        path="/3.0/search-members",
        query_params={"query": mailchimp_identity_email},
    )
    resp = connector.create_client().send(request)
    body = resp.json()
    merge_fields = body["exact_matches"]["members"][0]["merge_fields"]

    masking_configuration = HmacMaskingConfiguration()
    masking_strategy = HmacMaskingStrategy(masking_configuration)

    assert (
        merge_fields["FNAME"]
        == masking_strategy.mask(
            [reset_mailchimp_data["merge_fields"]["FNAME"]], pr.id
        )[0]
    )
    assert (
        merge_fields["LNAME"]
        == masking_strategy.mask(
            [reset_mailchimp_data["merge_fields"]["LNAME"]], pr.id
        )[0]
    )

    pr.delete(db=db)


@pytest.mark.integration_saas
@mock.patch("fides.api.models.privacy_request.PrivacyRequest.trigger_policy_webhook")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_access_request_saas_hubspot(
    trigger_webhook_mock,
    connection_config_hubspot,
    dataset_config_hubspot,
    db,
    cache,
    policy,
    policy_pre_execution_webhooks,
    policy_post_execution_webhooks,
    dsr_version,
    request,
    hubspot_identity_email,
    run_privacy_request_task,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    customer_email = hubspot_identity_email
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
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )
    results = pr.get_raw_access_results()
    assert len(results.keys()) == 4

    for key in results.keys():
        assert results[key] is not None
        assert results[key] != {}

    result_key_prefix = f"hubspot_instance:"
    contacts_key = result_key_prefix + "contacts"
    assert results[contacts_key][0]["properties"]["email"] == customer_email

    # Both pre-execution webhooks and both post-execution webhooks were called
    assert trigger_webhook_mock.call_count == 4

    pr.delete(db=db)


@pytest.mark.integration_postgres
@pytest.mark.integration
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_erasure_request_specific_category_postgres(
    postgres_integration_db,
    postgres_example_test_dataset_config,
    cache,
    db,
    generate_auth_header,
    erasure_policy,
    dsr_version,
    request,
    read_connection_config,
    run_privacy_request_task,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    customer_email = "customer-1@example.com"
    customer_id = 1
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": erasure_policy.key,
        "identity": {"email": customer_email},
    }

    stmt = select("*").select_from(table("customer"))
    res = postgres_integration_db.execute(stmt).all()

    pr = get_privacy_request_results(
        db,
        erasure_policy,
        run_privacy_request_task,
        data,
    )
    pr.delete(db=db)

    stmt = select(
        column("id"),
        column("name"),
    ).select_from(table("customer"))
    res = postgres_integration_db.execute(stmt).all()

    customer_found = False
    for row in res:
        if customer_id == row.id:
            customer_found = True
            # Check that the `name` field is `None`
            assert row.name is None
    assert customer_found


@pytest.mark.integration_mssql
@pytest.mark.integration
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_erasure_request_specific_category_mssql(
    mssql_integration_db,
    mssql_example_test_dataset_config,
    cache,
    db,
    dsr_version,
    request,
    generate_auth_header,
    erasure_policy,
    run_privacy_request_task,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    customer_email = "customer-1@example.com"
    customer_id = 1
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

    stmt = select(
        column("id"),
        column("name"),
    ).select_from(table("customer"))
    res = mssql_integration_db.execute(stmt).all()

    customer_found = False
    for row in res:
        if customer_id == row.id:
            customer_found = True
            # Check that the `name` field is `None`
            assert row.name is None
    assert customer_found


@pytest.mark.integration_mysql
@pytest.mark.integration
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_erasure_request_specific_category_mysql(
    mysql_integration_db,
    mysql_example_test_dataset_config,
    cache,
    db,
    dsr_version,
    request,
    generate_auth_header,
    erasure_policy,
    run_privacy_request_task,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    customer_email = "customer-1@example.com"
    customer_id = 1
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

    stmt = select(
        column("id"),
        column("name"),
    ).select_from(table("customer"))
    res = mysql_integration_db.execute(stmt).all()

    customer_found = False
    for row in res:
        if customer_id == row.id:
            customer_found = True
            # Check that the `name` field is `None`
            assert row.name is None
    assert customer_found


@pytest.mark.integration_external
@pytest.mark.integration_google_cloud_sql_mysql
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_erasure_request_google_cloud_sql_mysql(
    google_cloud_sql_mysql_integration_db,
    google_cloud_sql_mysql_example_test_dataset_config,
    cache,
    db,
    dsr_version,
    request,
    generate_auth_header,
    erasure_policy,
    run_privacy_request_task,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    customer_email = "customer-1@example.com"
    customer_id = 1
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
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )
    pr.delete(db=db)

    stmt = select(
        column("id"),
        column("name"),
    ).select_from(table("customer"))
    res = google_cloud_sql_mysql_integration_db.execute(stmt).all()

    customer_found = False
    for row in res:
        if customer_id == row.id:
            customer_found = True
            # Check that the `name` field is `None`
            assert row.name is None
    assert customer_found


@pytest.mark.integration_mariadb
@pytest.mark.integration
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_erasure_request_specific_category_mariadb(
    mariadb_example_test_dataset_config,
    mariadb_integration_db,
    cache,
    db,
    dsr_version,
    request,
    generate_auth_header,
    erasure_policy,
    run_privacy_request_task,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    customer_email = "customer-1@example.com"
    customer_id = 1
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

    stmt = select(
        column("id"),
        column("name"),
    ).select_from(table("customer"))
    res = mariadb_integration_db.execute(stmt).all()

    customer_found = False
    for row in res:
        if customer_id == row.id:
            customer_found = True
            # Check that the `name` field is `None`
            assert row.name is None
    assert customer_found


@pytest.mark.integration_postgres
@pytest.mark.integration
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_erasure_request_generic_category(
    postgres_integration_db,
    postgres_example_test_dataset_config,
    cache,
    db,
    dsr_version,
    request,
    generate_auth_header,
    erasure_policy,
    run_privacy_request_task,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    # It's safe to change this here since the `erasure_policy` fixture is scoped
    # at function level
    target = erasure_policy.rules[0].targets[0]
    target.data_category = DataCategory("user.contact").value
    target.save(db=db)

    email = "customer-2@example.com"
    customer_id = 2
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": erasure_policy.key,
        "identity": {"email": email},
    }

    pr = get_privacy_request_results(
        db,
        erasure_policy,
        run_privacy_request_task,
        data,
    )
    pr.delete(db=db)

    stmt = select(
        column("id"),
        column("email"),
        column("name"),
    ).select_from(table("customer"))
    res = postgres_integration_db.execute(stmt).all()

    customer_found = False
    for row in res:
        if customer_id == row.id:
            customer_found = True
            # Check that the `email` field is `None` and that its data category
            # ("user.contact.email") has been erased by the parent
            # category ("user.contact")
            assert row.email is None
            assert row.name is not None
        else:
            # There are two rows other rows, and they should not have been erased
            assert row.email in ["customer-1@example.com", "jane@example.com"]
    assert customer_found


@pytest.mark.integration_postgres
@pytest.mark.integration
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_erasure_request_aes_generic_category(
    postgres_integration_db,
    postgres_example_test_dataset_config,
    cache,
    db,
    dsr_version,
    request,
    generate_auth_header,
    erasure_policy_aes,
    run_privacy_request_task,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    # It's safe to change this here since the `erasure_policy` fixture is scoped
    # at function level
    target = erasure_policy_aes.rules[0].targets[0]
    target.data_category = DataCategory("user.contact").value
    target.save(db=db)

    email = "customer-2@example.com"
    customer_id = 2
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": erasure_policy_aes.key,
        "identity": {"email": email},
    }

    pr = get_privacy_request_results(
        db,
        erasure_policy_aes,
        run_privacy_request_task,
        data,
    )
    pr.delete(db=db)

    stmt = select(
        column("id"),
        column("email"),
        column("name"),
    ).select_from(table("customer"))
    res = postgres_integration_db.execute(stmt).all()

    customer_found = False
    for row in res:
        if customer_id == row.id:
            customer_found = True
            # Check that the `email` field is not original val and that its data category
            # ("user.contact.email") has been erased by the parent
            # category ("user.contact").
            # masked val for `email` field will change per new privacy request, so the best
            # we can do here is test that the original val has been changed
            assert row[1] != "customer-2@example.com"
            assert row[2] is not None
        else:
            # There are two rows other rows, and they should not have been erased
            assert row[1] in ["customer-1@example.com", "jane@example.com"]
    assert customer_found


@pytest.mark.integration_postgres
@pytest.mark.integration
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_erasure_request_with_table_joins(
    postgres_integration_db,
    postgres_example_test_dataset_config,
    db,
    cache,
    dsr_version,
    request,
    erasure_policy,
    run_privacy_request_task,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    # It's safe to change this here since the `erasure_policy` fixture is scoped
    # at function level
    target = erasure_policy.rules[0].targets[0]
    target.data_category = DataCategory("user.financial").value
    target.save(db=db)

    customer_email = "customer-1@example.com"
    customer_id = 1
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

    stmt = select(
        column("customer_id"),
        column("id"),
        column("ccn"),
        column("code"),
        column("name"),
    ).select_from(table("payment_card"))
    res = postgres_integration_db.execute(stmt).all()

    card_found = False
    for row in res:
        if row.customer_id == customer_id:
            card_found = True
            assert row.ccn is None
            assert row.code is None
            assert row.name is None

    assert card_found is True


@pytest.mark.integration_postgres
@pytest.mark.integration
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_erasure_request_read_access(
    postgres_integration_db,
    postgres_example_test_dataset_config_read_access,
    db,
    cache,
    erasure_policy,
    dsr_version,
    request,
    run_privacy_request_task,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    customer_email = "customer-2@example.com"
    customer_id = 2
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
    errored_execution_logs = pr.execution_logs.filter_by(status="error")
    assert errored_execution_logs.count() == 9
    assert (
        errored_execution_logs[0].message
        == "No values were erased since this connection "
        "my_postgres_db_1_read_config has not been given write access"
    )
    pr.delete(db=db)

    stmt = select(
        column("id"),
        column("name"),
    ).select_from(table("customer"))
    res = postgres_integration_db.execute(stmt).all()

    customer_found = False
    for row in res:
        if customer_id == row.id:
            customer_found = True
            # Check that the `name` field is NOT `None`. We couldn't erase, because the ConnectionConfig only had
            # "read" access
            assert row.name is not None
    assert customer_found


@pytest.fixture(scope="function")
def snowflake_resources(
    snowflake_example_test_dataset_config,
):
    snowflake_connection_config = (
        snowflake_example_test_dataset_config.connection_config
    )
    snowflake_client = SnowflakeConnector(snowflake_connection_config).client()
    uuid = str(uuid4())
    customer_email = f"customer-{uuid}@example.com"
    formatted_customer_email = f"'{customer_email}'"
    customer_name = f"{uuid}"
    formatted_customer_name = f"'{customer_name}'"

    stmt = 'select max("id") from "customer";'
    res = snowflake_client.execute(stmt).all()
    customer_id = res[0][0] + 1

    stmt = f"""
    insert into "customer" ("id", "email", "name", "variant_eg")
    select {customer_id}, {formatted_customer_email}, {formatted_customer_name}, to_variant({formatted_customer_name});
    """
    res = snowflake_client.execute(stmt).all()
    assert res[0][0] == 1
    yield {
        "email": customer_email,
        "formatted_email": formatted_customer_email,
        "name": customer_name,
        "id": customer_id,
        "client": snowflake_client,
    }
    # Remove test data and close Snowflake connection in teardown
    stmt = f'delete from "customer" where "email" = {formatted_customer_email};'
    res = snowflake_client.execute(stmt).all()
    assert res[0][0] == 1


@pytest.mark.integration_external
@pytest.mark.integration_snowflake
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_access_request_snowflake(
    snowflake_resources,
    db,
    cache,
    policy,
    dsr_version,
    request,
    run_privacy_request_task,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    customer_email = snowflake_resources["email"]
    customer_name = snowflake_resources["name"]
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
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )
    results = pr.get_raw_access_results()
    customer_table_key = f"snowflake_example_test_dataset:customer"
    assert len(results[customer_table_key]) == 1
    assert results[customer_table_key][0]["email"] == customer_email
    assert results[customer_table_key][0]["name"] == customer_name

    pr.delete(db=db)


@pytest.mark.integration_external
@pytest.mark.integration_snowflake
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_erasure_request_snowflake(
    snowflake_example_test_dataset_config,
    snowflake_resources,
    integration_config: Dict[str, str],
    db,
    cache,
    dsr_version,
    request,
    erasure_policy,
    run_privacy_request_task,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    customer_email = snowflake_resources["email"]
    snowflake_client = snowflake_resources["client"]
    formatted_customer_email = snowflake_resources["formatted_email"]
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
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )
    pr.delete(db=db)

    stmt = f'select "name", "variant_eg" from "customer" where "email" = {formatted_customer_email};'
    res = snowflake_client.execute(stmt).all()
    for row in res:
        assert row.name is None
        assert row.variant_eg is None


@pytest.fixture(scope="function")
def redshift_resources(
    redshift_example_test_dataset_config,
):
    redshift_connection_config = redshift_example_test_dataset_config.connection_config
    connector = RedshiftConnector(redshift_connection_config)
    redshift_client = connector.client()
    with redshift_client.connect() as connection:
        connector.set_schema(connection)
        uuid = str(uuid4())
        customer_email = f"customer-{uuid}@example.com"
        customer_name = f"{uuid}"

        stmt = "select max(id) from customer;"
        res = connection.execute(stmt)
        customer_id = res.all()[0][0] + 1

        stmt = "select max(id) from address;"
        res = connection.execute(stmt)
        address_id = res.all()[0][0] + 1

        city = "Test City"
        state = "TX"
        stmt = f"""
        insert into address (id, house, street, city, state, zip)
        values ({address_id}, '{111}', 'Test Street', '{city}', '{state}', '55555');
        """
        connection.execute(stmt)

        stmt = f"""
            insert into customer (id, email, name, address_id)
            values ({customer_id}, '{customer_email}', '{customer_name}', '{address_id}');
        """
        connection.execute(stmt)

        yield {
            "email": customer_email,
            "name": customer_name,
            "id": customer_id,
            "client": redshift_client,
            "address_id": address_id,
            "city": city,
            "state": state,
            "connector": connector,
        }
        # Remove test data and close Redshift connection in teardown
        stmt = f"delete from customer where email = '{customer_email}';"
        connection.execute(stmt)

        stmt = f'delete from address where "id" = {address_id};'
        connection.execute(stmt)


@pytest.mark.integration_external
@pytest.mark.integration_redshift
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_access_request_redshift(
    redshift_resources,
    db,
    cache,
    policy,
    run_privacy_request_task,
    dsr_version,
    request,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    customer_email = redshift_resources["email"]
    customer_name = redshift_resources["name"]
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
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )
    results = pr.get_raw_access_results()
    customer_table_key = f"redshift_example_test_dataset:customer"
    assert len(results[customer_table_key]) == 1
    assert results[customer_table_key][0]["email"] == customer_email
    assert results[customer_table_key][0]["name"] == customer_name

    address_table_key = f"redshift_example_test_dataset:address"

    city = redshift_resources["city"]
    state = redshift_resources["state"]
    assert len(results[address_table_key]) == 1
    assert results[address_table_key][0]["city"] == city
    assert results[address_table_key][0]["state"] == state

    pr.delete(db=db)


@pytest.mark.integration_external
@pytest.mark.integration_redshift
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_erasure_request_redshift(
    redshift_example_test_dataset_config,
    redshift_resources,
    integration_config: Dict[str, str],
    db,
    cache,
    erasure_policy,
    dsr_version,
    request,
    run_privacy_request_task,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    customer_email = redshift_resources["email"]
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": erasure_policy.key,
        "identity": {"email": customer_email},
    }

    # Should erase customer name
    pr = get_privacy_request_results(
        db,
        erasure_policy,
        run_privacy_request_task,
        data,
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )
    pr.delete(db=db)

    connector = redshift_resources["connector"]
    redshift_client = redshift_resources["client"]
    with redshift_client.connect() as connection:
        connector.set_schema(connection)
        stmt = f"select name from customer where email = '{customer_email}';"
        res = connection.execute(stmt).all()
        for row in res:
            assert row.name is None

        address_id = redshift_resources["address_id"]
        stmt = f"select 'id', city, state from address where id = {address_id};"
        res = connection.execute(stmt).all()
        for row in res:
            # Not yet masked because these fields aren't targeted by erasure policy
            assert row.city == redshift_resources["city"]
            assert row.state == redshift_resources["state"]

    target = erasure_policy.rules[0].targets[0]
    target.data_category = "user.contact.address.state"
    target.save(db=db)

    # Should erase state fields on address table
    pr = get_privacy_request_results(
        db,
        erasure_policy,
        run_privacy_request_task,
        data,
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )
    pr.delete(db=db)

    connector = redshift_resources["connector"]
    redshift_client = redshift_resources["client"]
    with redshift_client.connect() as connection:
        connector.set_schema(connection)

        address_id = redshift_resources["address_id"]
        stmt = f"select 'id', city, state from address where id = {address_id};"
        res = connection.execute(stmt).all()
        for row in res:
            # State field was targeted by erasure policy but city was not
            assert row.city is not None
            assert row.state is None


@pytest.mark.integration_external
@pytest.mark.integration_bigquery
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_2_0", "use_dsr_3_0"],
)
@pytest.mark.parametrize(
    "bigquery_fixtures",
    ["bigquery_resources", "bigquery_resources_with_namespace_meta"],
)
def test_create_and_process_access_request_bigquery(
    db,
    policy,
    dsr_version,
    request,
    bigquery_fixtures,
    run_privacy_request_task,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0
    bigquery_resources = request.getfixturevalue(bigquery_fixtures)

    customer_email = bigquery_resources["email"]
    customer_name = bigquery_resources["name"]
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": policy.key,
        "identity": {"email": customer_email},
    }
    bigquery_client = bigquery_resources["client"]
    with bigquery_client.connect() as connection:
        stmt = f"select * from fidesopstest.employee where address_id = {bigquery_resources['address_id']};"
        res = connection.execute(stmt).all()
        for row in res:
            assert row.address_id == bigquery_resources["address_id"]
            assert row.id == bigquery_resources["employee_id"]
            assert row.email == bigquery_resources["employee_email"]

    pr = get_privacy_request_results(
        db,
        policy,
        run_privacy_request_task,
        data,
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )
    results = pr.get_raw_access_results()
    customer_table_key = "bigquery_example_test_dataset:customer"
    assert len(results[customer_table_key]) == 1
    assert results[customer_table_key][0]["email"] == customer_email
    assert results[customer_table_key][0]["name"] == customer_name

    address_table_key = "bigquery_example_test_dataset:address"

    city = bigquery_resources["city"]
    state = bigquery_resources["state"]
    assert len(results[address_table_key]) == 1
    assert results[address_table_key][0]["city"] == city
    assert results[address_table_key][0]["state"] == state

    employee_table_key = "bigquery_example_test_dataset:employee"
    assert len(results[employee_table_key]) == 1
    assert results["bigquery_example_test_dataset:employee"] != []
    assert (
        results[employee_table_key][0]["address_id"] == bigquery_resources["address_id"]
    )
    assert (
        results[employee_table_key][0]["email"] == bigquery_resources["employee_email"]
    )
    assert results[employee_table_key][0]["id"] == bigquery_resources["employee_id"]

    # this covers access requests against a partitioned table
    visit_partitioned_table_key = "bigquery_example_test_dataset:visit_partitioned"
    assert len(results[visit_partitioned_table_key]) == 1
    assert (
        results[visit_partitioned_table_key][0]["email"] == bigquery_resources["email"]
    )

    pr.delete(db=db)


@pytest.mark.integration_external
@pytest.mark.integration_bigquery
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_2_0", "use_dsr_3_0"],
)
@pytest.mark.parametrize(
    "bigquery_fixtures",
    ["bigquery_resources", "bigquery_resources_with_namespace_meta"],
)
def test_create_and_process_erasure_request_bigquery(
    db,
    dsr_version,
    request,
    bigquery_fixtures,
    erasure_policy,
    run_privacy_request_task,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0
    bigquery_resources = request.getfixturevalue(bigquery_fixtures)

    bigquery_client = bigquery_resources["client"]
    # Verifying that employee info exists in db
    with bigquery_client.connect() as connection:
        stmt = f"select * from fidesopstest.employee where address_id = {bigquery_resources['address_id']};"
        res = connection.execute(stmt).all()
        for row in res:
            assert row.address_id == bigquery_resources["address_id"]
            assert row.id == bigquery_resources["employee_id"]
            assert row.email == bigquery_resources["employee_email"]

    customer_email = bigquery_resources["email"]
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": erasure_policy.key,
        "identity": {"email": customer_email},
    }

    # Should erase customer name
    pr = get_privacy_request_results(
        db,
        erasure_policy,
        run_privacy_request_task,
        data,
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )
    pr.delete(db=db)

    bigquery_client = bigquery_resources["client"]
    with bigquery_client.connect() as connection:
        stmt = (
            f"select name from fidesopstest.customer where email = '{customer_email}';"
        )
        res = connection.execute(stmt).all()
        for row in res:
            assert row.name is None

        address_id = bigquery_resources["address_id"]
        stmt = f"select 'id', city, state from fidesopstest.address where id = {address_id};"
        res = connection.execute(stmt).all()
        for row in res:
            # Not yet masked because these fields aren't targeted by erasure policy
            assert row.city == bigquery_resources["city"]
            assert row.state == bigquery_resources["state"]

    target = erasure_policy.rules[0].targets[0]
    target.data_category = "user.contact.address.state"
    target.save(db=db)

    # Should erase state fields on address table
    pr = get_privacy_request_results(
        db,
        erasure_policy,
        run_privacy_request_task,
        data,
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )

    bigquery_client = bigquery_resources["client"]
    with bigquery_client.connect() as connection:
        address_id = bigquery_resources["address_id"]
        stmt = f"select 'id', city, state from fidesopstest.address where id = {address_id};"
        res = connection.execute(stmt).all()
        for row in res:
            # State field was targeted by erasure policy but city was not
            assert row.city is not None
            assert row.state is None

        stmt = f"select 'id', city, state from fidesopstest.address where id = {address_id};"
        res = connection.execute(stmt).all()
        for row in res:
            # State field was targeted by erasure policy but city was not
            assert row.city is not None
            assert row.state is None

        stmt = f"select * from fidesopstest.employee where address_id = {bigquery_resources['address_id']};"
        res = connection.execute(stmt).all()

        # Employee records deleted entirely due to collection-level masking strategy override
        assert res == []

    pr.delete(db=db)


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


@pytest.mark.integration_saas
def test_build_consent_dataset_graph(
    postgres_example_test_dataset_config_read_access,
    mysql_example_test_dataset_config,
    mailchimp_transactional_dataset_config,
):
    """Currently returns a DatasetGraph made up of resources that have consent requests defined
    in the saas config"""
    dataset_graph: DatasetGraph = build_consent_dataset_graph(
        [
            postgres_example_test_dataset_config_read_access,
            mysql_example_test_dataset_config,
            mailchimp_transactional_dataset_config,
        ]
    )
    assert len(dataset_graph.nodes.keys()) == 1
    assert [col_addr.value for col_addr in dataset_graph.nodes.keys()] == [
        "mailchimp_transactional_instance:mailchimp_transactional_instance"
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


@pytest.fixture(scope="function")
def dynamodb_resources(
    dynamodb_example_test_dataset_config,
):
    dynamodb_connection_config = dynamodb_example_test_dataset_config.connection_config
    dynamodb_client = DynamoDBConnector(dynamodb_connection_config).client()
    uuid = str(uuid4())
    customer_email = f"customer-{uuid}@example.com"
    customer_name = f"{uuid}"

    ## document and remove remaining comments if we can't get the bigger test running
    items = {
        "customer_identifier": [
            {
                "customer_id": {"S": customer_name},
                "email": {"S": customer_email},
                "name": {"S": customer_name},
                "created": {"S": datetime.now(timezone.utc).isoformat()},
            }
        ],
        "customer": [
            {
                "id": {"S": customer_name},
                "name": {"S": customer_name},
                "email": {"S": customer_email},
                "address_id": {"L": [{"S": customer_name}, {"S": customer_name}]},
                "personal_info": {"M": {"gender": {"S": "male"}, "age": {"S": "99"}}},
                "created": {"S": datetime.now(timezone.utc).isoformat()},
            }
        ],
        "address": [
            {
                "id": {"S": customer_name},
                "city": {"S": "city"},
                "house": {"S": "house"},
                "state": {"S": "state"},
                "street": {"S": "street"},
                "zip": {"S": "zip"},
            }
        ],
        "login": [
            {
                "customer_id": {"S": customer_name},
                "login_date": {"S": "2023-01-01"},
                "name": {"S": customer_name},
                "email": {"S": customer_email},
            },
            {
                "customer_id": {"S": customer_name},
                "login_date": {"S": "2023-01-02"},
                "name": {"S": customer_name},
                "email": {"S": customer_email},
            },
        ],
    }

    for table_name, rows in items.items():
        for item in rows:
            res = dynamodb_client.put_item(
                TableName=table_name,
                Item=item,
            )
            assert res["ResponseMetadata"]["HTTPStatusCode"] == 200

    yield {
        "email": customer_email,
        "formatted_email": customer_email,
        "name": customer_name,
        "customer_id": uuid,
        "client": dynamodb_client,
    }
    # Remove test data and close Dynamodb connection in teardown
    delete_items = {
        "customer_identifier": [{"email": {"S": customer_email}}],
        "customer": [{"id": {"S": customer_name}}],
        "address": [{"id": {"S": customer_name}}],
        "login": [
            {
                "customer_id": {"S": customer_name},
                "login_date": {"S": "2023-01-01"},
            },
            {
                "customer_id": {"S": customer_name},
                "login_date": {"S": "2023-01-02"},
            },
        ],
    }
    for table_name, rows in delete_items.items():
        for item in rows:
            res = dynamodb_client.delete_item(
                TableName=table_name,
                Key=item,
            )
            assert res["ResponseMetadata"]["HTTPStatusCode"] == 200


@pytest.mark.integration_external
@pytest.mark.integration_dynamodb
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_empty_access_request_dynamodb(
    db,
    cache,
    policy,
    dsr_version,
    request,
    run_privacy_request_task,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": policy.key,
        "identity": {"email": "thiscustomerdoesnot@exist.com"},
    }

    pr = get_privacy_request_results(
        db,
        policy,
        run_privacy_request_task,
        data,
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )
    # Here the results should be empty as no data will be located for that identity
    results = pr.get_raw_access_results()
    pr.delete(db=db)
    assert results == {}


@pytest.mark.integration_external
@pytest.mark.integration_dynamodb
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_access_request_dynamodb(
    dynamodb_resources,
    db,
    cache,
    policy,
    run_privacy_request_task,
    dsr_version,
    request,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    customer_email = dynamodb_resources["email"]
    customer_name = dynamodb_resources["name"]
    customer_id = dynamodb_resources["customer_id"]
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
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )
    results = pr.get_raw_access_results()
    customer_table_key = f"dynamodb_example_test_dataset:customer"
    address_table_key = f"dynamodb_example_test_dataset:address"
    login_table_key = f"dynamodb_example_test_dataset:login"
    assert len(results[customer_table_key]) == 1
    assert len(results[address_table_key]) == 1
    assert len(results[login_table_key]) == 2
    assert results[customer_table_key][0]["email"] == customer_email
    assert results[customer_table_key][0]["name"] == customer_name
    assert results[customer_table_key][0]["id"] == customer_id
    assert results[address_table_key][0]["id"] == customer_id
    assert results[login_table_key][0]["name"] == customer_name

    pr.delete(db=db)


@pytest.mark.integration_external
@pytest.mark.integration_dynamodb
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_erasure_request_dynamodb(
    dynamodb_example_test_dataset_config,
    dynamodb_resources,
    integration_config: Dict[str, str],
    db,
    cache,
    erasure_policy,
    dsr_version,
    request,
    run_privacy_request_task,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    customer_email = dynamodb_resources["email"]
    dynamodb_client = dynamodb_resources["client"]
    customer_id = dynamodb_resources["customer_id"]
    customer_name = dynamodb_resources["name"]
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
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )
    pr.delete(db=db)
    deserializer = TypeDeserializer()
    customer = dynamodb_client.get_item(
        TableName="customer",
        Key={"id": {"S": customer_id}},
    )
    customer_identifier = dynamodb_client.get_item(
        TableName="customer_identifier",
        Key={"email": {"S": customer_email}},
    )
    login = dynamodb_client.get_item(
        TableName="login",
        Key={
            "customer_id": {"S": customer_name},
            "login_date": {"S": "2023-01-01"},
        },
    )
    assert deserializer.deserialize(customer["Item"]["name"]) == None
    assert deserializer.deserialize(customer_identifier["Item"]["name"]) == None
    assert deserializer.deserialize(login["Item"]["name"]) == None


@mock.patch("fides.api.service.connectors.saas_connector.AuthenticatedClient.send")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_async_callback_access_request(
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


@pytest.mark.integration_external
@pytest.mark.integration_google_cloud_sql_postgres
@mock.patch("fides.api.models.privacy_request.PrivacyRequest.trigger_policy_webhook")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_access_request_google_cloud_sql_postgres(
    trigger_webhook_mock,
    google_cloud_sql_postgres_example_test_dataset_config,
    google_cloud_sql_postgres_integration_db,
    db: Session,
    cache,
    policy,
    dsr_version,
    request,
    policy_pre_execution_webhooks,
    policy_post_execution_webhooks,
    run_privacy_request_task,
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
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )

    results = pr.get_raw_access_results()
    assert len(results.keys()) == 11

    for key in results.keys():
        assert results[key] is not None
        assert results[key] != {}

    result_key_prefix = "google_cloud_sql_postgres_example_test_dataset:"
    customer_key = result_key_prefix + "customer"
    assert results[customer_key][0]["email"] == customer_email

    visit_key = result_key_prefix + "visit"
    assert results[visit_key][0]["email"] == customer_email
    # Both pre-execution webhooks and both post-execution webhooks were called
    assert trigger_webhook_mock.call_count == 4
    pr.delete(db=db)


@pytest.mark.integration_external
@pytest.mark.integration_google_cloud_sql_postgres
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_erasure_request_google_cloud_sql_postgres(
    google_cloud_sql_postgres_integration_db,
    google_cloud_sql_postgres_example_test_dataset_config,
    cache,
    db,
    dsr_version,
    request,
    generate_auth_header,
    erasure_policy,
    run_privacy_request_task,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    customer_email = "customer-1@example.com"
    customer_id = 1
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
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )
    pr.delete(db=db)

    stmt = select(
        column("id"),
        column("name"),
    ).select_from(table("customer"))

    res = google_cloud_sql_postgres_integration_db.execute(stmt).all()

    customer_found = False
    for row in res:
        if customer_id == row.id:
            customer_found = True
            # Check that the `name` field is `None`
            assert row.name is None
    assert customer_found
