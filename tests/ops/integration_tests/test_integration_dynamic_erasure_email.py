from unittest import mock
from unittest.mock import ANY, Mock

import pytest as pytest

from fides.api.email_templates import get_email_template
from fides.api.models.connectionconfig import AccessLevel
from fides.api.models.privacy_request import ExecutionLog
from fides.api.schemas.messaging.messaging import (
    EmailForActionType,
    MessagingActionType,
)
from fides.api.schemas.privacy_request import (
    CustomPrivacyRequestField,
    ExecutionLogStatus,
    PrivacyRequestStatus,
)
from fides.api.service.connectors.dynamic_erasure_email_connector import (
    DynamicErasureEmailConnectorException,
)
from fides.api.service.privacy_request.email_batch_service import (
    EmailExitState,
    send_email_batch,
)
from tests.ops.service.privacy_request.test_request_runner_service import (
    get_privacy_request_results,
)


@pytest.mark.integration
@pytest.mark.integration_postgres
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
@mock.patch(
    "fides.api.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
)
@mock.patch("fides.api.service.messaging.message_dispatch_service._mailgun_dispatcher")
async def test_erasure_email(
    mock_mailgun_dispatcher: Mock,
    mock_requeue_privacy_requests: Mock,
    # Need to populate the postgres integration DB
    postgres_integration_db,
    # Need to allow custom privacy request fields
    allow_custom_privacy_request_field_collection_enabled,
    allow_custom_privacy_request_fields_in_request_execution_enabled,
    db,
    dsr_version,
    request,
    erasure_policy,
    # Need to create a dynamic erasure email connector
    test_dynamic_erasure_email_connector,
    run_privacy_request_task,
    # Need a messaging config
    messaging_config,
) -> None:
    """
    Run an erasure privacy request with only a dynamic erasure email connector.
    Verify the privacy request is set to "awaiting email send" and that one email
    is sent when the send_email_batch job is executed manually
    """
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    pr = get_privacy_request_results(
        db,
        erasure_policy,
        run_privacy_request_task,
        {
            "requested_at": "2021-08-30T16:09:37.359Z",
            "policy_key": erasure_policy.key,
            "identity": {"email": "customer-1@example.com"},
        },
    )

    db.refresh(pr)
    pr.persist_custom_privacy_request_fields(
        db,
        {
            "tenant_id": CustomPrivacyRequestField(
                label="Tenant Custom Field", value="site-id-1"
            )
        },
    )

    # the privacy request will be in an "awaiting email send" state until the "send email batch" job executes
    assert pr.status == PrivacyRequestStatus.awaiting_email_send
    assert pr.awaiting_email_send_at is not None

    # execute send email batch job without waiting for it to be scheduled
    exit_state = send_email_batch.delay().get()
    assert exit_state == EmailExitState.complete

    # verify the email was sent
    erasure_email_template = get_email_template(
        MessagingActionType.MESSAGE_ERASURE_REQUEST_FULFILLMENT
    )
    mock_mailgun_dispatcher.assert_called_once_with(
        ANY,
        EmailForActionType(
            subject="Notification of user erasure requests from Test Org",
            body=erasure_email_template.render(
                {
                    "controller": "Test Org",
                    "third_party_vendor_name": "Vendor 1",
                    "identities": ["customer-1@example.com"],
                }
            ),
        ),
        "test@test.com",
    )

    # verify the privacy request was queued for further processing
    mock_requeue_privacy_requests.assert_called()


@pytest.mark.integration
@pytest.mark.integration_postgres
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
@mock.patch(
    "fides.api.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
)
@mock.patch("fides.api.service.messaging.message_dispatch_service._mailgun_dispatcher")
async def test_erasure_email_multiple_requests(
    mock_mailgun_dispatcher: Mock,
    mock_requeue_privacy_requests: Mock,
    # Need to populate the postgres integration DB
    postgres_integration_db,
    # Need to allow custom privacy request fields
    allow_custom_privacy_request_field_collection_enabled,
    allow_custom_privacy_request_fields_in_request_execution_enabled,
    db,
    dsr_version,
    request,
    erasure_policy,
    # Need to create a dynamic erasure email connector
    test_dynamic_erasure_email_connector,
    run_privacy_request_task,
    # Need a messaging config
    messaging_config,
) -> None:
    """
    Run two erasure privacy requesta with only a dynamic erasure email connector, each
    request has a different custom field value.
    Verify the privacy requesta are set to "awaiting email send" and that one email
    per privacy request is sent when the send_email_batch job is executed manually
    """
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    pr1 = get_privacy_request_results(
        db,
        erasure_policy,
        run_privacy_request_task,
        {
            "requested_at": "2021-08-30T16:09:37.359Z",
            "policy_key": erasure_policy.key,
            "identity": {"email": "customer-1@example.com"},
        },
    )

    db.refresh(pr1)
    pr1.persist_custom_privacy_request_fields(
        db,
        {
            "tenant_id": CustomPrivacyRequestField(
                label="Tenant Custom Field", value="site-id-1"
            )
        },
    )

    pr2 = get_privacy_request_results(
        db,
        erasure_policy,
        run_privacy_request_task,
        {
            "requested_at": "2021-08-30T16:09:37.359Z",
            "policy_key": erasure_policy.key,
            "identity": {"email": "customer-2@example.com"},
        },
    )

    db.refresh(pr2)
    pr2.persist_custom_privacy_request_fields(
        db,
        {
            "tenant_id": CustomPrivacyRequestField(
                label="Tenant Custom Field", value="site-id-2"
            )
        },
    )

    # the privacy request will be in an "awaiting email send" state until the "send email batch" job executes
    assert pr1.status == PrivacyRequestStatus.awaiting_email_send
    assert pr1.awaiting_email_send_at is not None
    assert pr2.status == PrivacyRequestStatus.awaiting_email_send
    assert pr2.awaiting_email_send_at is not None

    # execute send email batch job without waiting for it to be scheduled
    exit_state = send_email_batch.delay().get()
    assert exit_state == EmailExitState.complete

    # verify the email was sent
    erasure_email_template = get_email_template(
        MessagingActionType.MESSAGE_ERASURE_REQUEST_FULFILLMENT
    )

    mock_mailgun_dispatcher.call_args_list == [
        (
            ANY,
            EmailForActionType(
                subject="Notification of user erasure requests from Test Org",
                body=erasure_email_template.render(
                    {
                        "controller": "Test Org",
                        "third_party_vendor_name": "Vendor 1",
                        "identities": ["customer-1@example.com"],
                    }
                ),
            ),
            "test@test.com",
        ),
        (
            ANY,
            EmailForActionType(
                subject="Notification of user erasure requests from Test Org",
                body=erasure_email_template.render(
                    {
                        "controller": "Test Org",
                        "third_party_vendor_name": "Vendor 2",
                        "identities": ["customer-2@example.com"],
                    }
                ),
            ),
            "test2@test.com",
        ),
    ]

    # verify the privacy requesta were queued for further processing
    mock_requeue_privacy_requests.assert_called()
    mock_requeue_privacy_requests.call_count == 2


@pytest.mark.integration
@pytest.mark.integration_postgres
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
@mock.patch(
    "fides.api.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
)
@mock.patch("fides.api.service.messaging.message_dispatch_service._mailgun_dispatcher")
async def test_erasure_email_multiple_requests_same_email_different_vendor(
    mock_mailgun_dispatcher: Mock,
    mock_requeue_privacy_requests: Mock,
    # Need to populate the postgres integration DB
    postgres_integration_db,
    # Need to allow custom privacy request fields
    allow_custom_privacy_request_field_collection_enabled,
    allow_custom_privacy_request_fields_in_request_execution_enabled,
    db,
    dsr_version,
    request,
    erasure_policy,
    # Need to create a dynamic erasure email connector
    test_dynamic_erasure_email_connector,
    run_privacy_request_task,
    # Need a messaging config
    messaging_config,
) -> None:
    """
    Run two erasure privacy requesta with only a dynamic erasure email connector, each
    request has a different custom field value that yields the same email but different
    vendor names. Verify the privacy requests are set to "awaiting email send" and that
    two different emails are sent.
    """
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    pr1 = get_privacy_request_results(
        db,
        erasure_policy,
        run_privacy_request_task,
        {
            "requested_at": "2021-08-30T16:09:37.359Z",
            "policy_key": erasure_policy.key,
            "identity": {"email": "customer-1@example.com"},
        },
    )

    db.refresh(pr1)
    pr1.persist_custom_privacy_request_fields(
        db,
        {
            "tenant_id": CustomPrivacyRequestField(
                label="Tenant Custom Field", value="site-id-1"
            )
        },
    )

    pr2 = get_privacy_request_results(
        db,
        erasure_policy,
        run_privacy_request_task,
        {
            "requested_at": "2021-08-30T16:09:37.359Z",
            "policy_key": erasure_policy.key,
            "identity": {"email": "customer-2@example.com"},
        },
    )

    db.refresh(pr2)
    pr2.persist_custom_privacy_request_fields(
        db,
        {
            "tenant_id": CustomPrivacyRequestField(
                label="Tenant Custom Field", value="site-id-3"
            )
        },
    )

    # the privacy request will be in an "awaiting email send" state until the "send email batch" job executes
    assert pr1.status == PrivacyRequestStatus.awaiting_email_send
    assert pr1.awaiting_email_send_at is not None
    assert pr2.status == PrivacyRequestStatus.awaiting_email_send
    assert pr2.awaiting_email_send_at is not None

    # execute send email batch job without waiting for it to be scheduled
    exit_state = send_email_batch.delay().get()
    assert exit_state == EmailExitState.complete

    # verify the email was sent
    erasure_email_template = get_email_template(
        MessagingActionType.MESSAGE_ERASURE_REQUEST_FULFILLMENT
    )

    mock_mailgun_dispatcher.call_args_list == [
        (
            ANY,
            EmailForActionType(
                subject="Notification of user erasure requests from Test Org",
                body=erasure_email_template.render(
                    {
                        "controller": "Test Org",
                        "third_party_vendor_name": "Vendor 1",
                        "identities": ["customer-1@example.com"],
                    }
                ),
            ),
            "test@test.com",
        ),
        (
            ANY,
            EmailForActionType(
                subject="Notification of user erasure requests from Test Org",
                body=erasure_email_template.render(
                    {
                        "controller": "Test Org",
                        "third_party_vendor_name": "Vendor 5",
                        "identities": ["customer-2@example.com"],
                    }
                ),
            ),
            "test@test.com",
        ),
    ]

    # verify the privacy requesta were queued for further processing
    mock_requeue_privacy_requests.assert_called()
    mock_requeue_privacy_requests.call_count == 2


@pytest.mark.integration
@pytest.mark.integration_postgres
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
@mock.patch(
    "fides.api.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
)
@mock.patch("fides.api.service.messaging.message_dispatch_service._mailgun_dispatcher")
async def test_erasure_email_multiple_requests_same_email(
    mock_mailgun_dispatcher: Mock,
    mock_requeue_privacy_requests: Mock,
    # Need to populate the postgres integration DB
    postgres_integration_db,
    # Need to allow custom privacy request fields
    allow_custom_privacy_request_field_collection_enabled,
    allow_custom_privacy_request_fields_in_request_execution_enabled,
    db,
    dsr_version,
    request,
    erasure_policy,
    # Need to create a dynamic erasure email connector
    test_dynamic_erasure_email_connector,
    run_privacy_request_task,
    # Need a messaging config
    messaging_config,
) -> None:
    """
    Run two erasure privacy requesta with only a dynamic erasure email connector, each
    request has the same custom field value.
    Verify the privacy requests are set to "awaiting email send" and that one single email
    is sent for both privacy requests.
    """
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    pr1 = get_privacy_request_results(
        db,
        erasure_policy,
        run_privacy_request_task,
        {
            "requested_at": "2021-08-30T16:09:37.359Z",
            "policy_key": erasure_policy.key,
            "identity": {"email": "customer-1@example.com"},
        },
    )

    db.refresh(pr1)
    pr1.persist_custom_privacy_request_fields(
        db,
        {
            "tenant_id": CustomPrivacyRequestField(
                label="Tenant Custom Field", value="site-id-1"
            )
        },
    )

    pr2 = get_privacy_request_results(
        db,
        erasure_policy,
        run_privacy_request_task,
        {
            "requested_at": "2021-08-30T16:09:37.359Z",
            "policy_key": erasure_policy.key,
            "identity": {"email": "customer-2@example.com"},
        },
    )

    db.refresh(pr2)
    pr2.persist_custom_privacy_request_fields(
        db,
        {
            "tenant_id": CustomPrivacyRequestField(
                label="Tenant Custom Field", value="site-id-1"
            )
        },
    )

    # the privacy request will be in an "awaiting email send" state until the "send email batch" job executes
    assert pr1.status == PrivacyRequestStatus.awaiting_email_send
    assert pr1.awaiting_email_send_at is not None
    assert pr2.status == PrivacyRequestStatus.awaiting_email_send
    assert pr2.awaiting_email_send_at is not None

    # execute send email batch job without waiting for it to be scheduled
    exit_state = send_email_batch.delay().get()
    assert exit_state == EmailExitState.complete

    # verify the email was sent
    erasure_email_template = get_email_template(
        MessagingActionType.MESSAGE_ERASURE_REQUEST_FULFILLMENT
    )
    mock_mailgun_dispatcher.assert_called_once_with(
        ANY,
        EmailForActionType(
            subject="Notification of user erasure requests from Test Org",
            body=erasure_email_template.render(
                {
                    "controller": "Test Org",
                    "third_party_vendor_name": "Vendor 1",
                    "identities": ["customer-1@example.com", "customer-2@example.com"],
                }
            ),
        ),
        "test@test.com",
    )

    # verify the privacy request was queued for further processing
    mock_requeue_privacy_requests.assert_called()


@pytest.mark.integration
@pytest.mark.integration_postgres
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
@mock.patch(
    "fides.api.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
)
@mock.patch("fides.api.service.messaging.message_dispatch_service._mailgun_dispatcher")
@mock.patch(
    "fides.api.service.connectors.dynamic_erasure_email_connector.logger",
    autospec=True,
)
async def test_erasure_email_invalid_dataset(
    logger_mock,
    mock_mailgun_dispatcher: Mock,
    mock_requeue_privacy_requests: Mock,
    # Need to populate the postgres integration DB
    postgres_integration_db,
    # Need to allow custom privacy request fields
    allow_custom_privacy_request_field_collection_enabled,
    allow_custom_privacy_request_fields_in_request_execution_enabled,
    db,
    dsr_version,
    request,
    erasure_policy,
    # Need to create an invalid dynamic erasure email connector
    dynamic_erasure_email_connector_config_invalid_dataset,
    run_privacy_request_task,
    # Need a messaging config
    messaging_config,
) -> None:
    """
    Run an erasure privacy request with only a dynamic erasure email connector
    that has been misconfigured with an invalid dataset. Verify that the privacy
    request is set to "error" and that an error log is created.
    """
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    pr = get_privacy_request_results(
        db,
        erasure_policy,
        run_privacy_request_task,
        {
            "requested_at": "2021-08-30T16:09:37.359Z",
            "policy_key": erasure_policy.key,
            "identity": {"email": "customer-1@example.com"},
        },
    )

    db.refresh(pr)
    pr.persist_custom_privacy_request_fields(
        db,
        {
            "tenant_id": CustomPrivacyRequestField(
                label="Tenant Custom Field", value="site-id-1"
            )
        },
    )

    # the privacy request will be in an "awaiting email send" state until the "send email batch" job executes
    assert pr.status == PrivacyRequestStatus.awaiting_email_send
    assert pr.awaiting_email_send_at is not None

    # execute send email batch job without waiting for it to be scheduled
    # we expect the job to raise an exception because the connector is misconfigured
    with pytest.raises(DynamicErasureEmailConnectorException) as exc:
        send_email_batch.delay().get()
        assert (
            str(exc.value)
            == "DatasetConfig with key nonexistent_dataset not found. Failed to send dynamic erasure emails for connector: my_dynamic_erasure_email_invalid_config.",
        )

    # assert error was logged
    logger_mock.error.assert_called_once_with(
        "DatasetConfig with key nonexistent_dataset not found. Failed to send dynamic erasure emails for connector: my_dynamic_erasure_email_invalid_config.",
    )
    # assert privacy request was marked as error
    db.refresh(pr)
    assert pr.status == PrivacyRequestStatus.error

    # and that an error ExecutionLog was created
    error_log = pr.execution_logs.filter(
        ExecutionLog.status == ExecutionLogStatus.error
    )
    assert error_log.count() == 1
    assert (
        error_log.first().message
        == "Connector configuration references DatasetConfig with key nonexistent_dataset, but no such DatasetConfig was found."
    )

    # verify the email was not sent
    mock_mailgun_dispatcher.assert_not_called()


@pytest.mark.integration
@pytest.mark.integration_postgres
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
@mock.patch(
    "fides.api.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
)
@mock.patch("fides.api.service.messaging.message_dispatch_service._mailgun_dispatcher")
@mock.patch(
    "fides.api.service.connectors.dynamic_erasure_email_connector.logger",
    autospec=True,
)
async def test_erasure_email_invalid_field(
    logger_mock,
    mock_mailgun_dispatcher: Mock,
    mock_requeue_privacy_requests: Mock,
    # Need to populate the postgres integration DB
    postgres_integration_db,
    # Need to allow custom privacy request fields
    allow_custom_privacy_request_field_collection_enabled,
    allow_custom_privacy_request_fields_in_request_execution_enabled,
    db,
    dsr_version,
    request,
    erasure_policy,
    # Need to create an invalid dynamic erasure email connector
    dynamic_erasure_email_connector_config_invalid_field,
    run_privacy_request_task,
    # Need a messaging config
    messaging_config,
) -> None:
    """
    Run an erasure privacy request with only a dynamic erasure email connector
    that has been misconfigured with an invalid field. Verify that the privacy
    request is set to "error" and that an error log is created.
    """
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    pr = get_privacy_request_results(
        db,
        erasure_policy,
        run_privacy_request_task,
        {
            "requested_at": "2021-08-30T16:09:37.359Z",
            "policy_key": erasure_policy.key,
            "identity": {"email": "customer-1@example.com"},
        },
    )

    db.refresh(pr)
    pr.persist_custom_privacy_request_fields(
        db,
        {
            "tenant_id": CustomPrivacyRequestField(
                label="Tenant Custom Field", value="site-id-1"
            )
        },
    )

    # the privacy request will be in an "awaiting email send" state until the "send email batch" job executes
    assert pr.status == PrivacyRequestStatus.awaiting_email_send
    assert pr.awaiting_email_send_at is not None

    # execute send email batch job without waiting for it to be scheduled
    # we expect the job to raise an exception because the connector is misconfigured
    with pytest.raises(DynamicErasureEmailConnectorException) as exc:
        send_email_batch.delay().get()
        assert (
            str(exc.value)
            == "Invalid dataset reference field weird-field-no-dots for dataset postgres_example_custom_request_field_dataset. Failed to send dynamic erasure emails for connector: my_dynamic_erasure_email_invalid_config."
        )

    # assert error was logged
    logger_mock.error.assert_called_once_with(
        "Invalid dataset reference field weird-field-no-dots for dataset postgres_example_custom_request_field_dataset. Failed to send dynamic erasure emails for connector: my_dynamic_erasure_email_invalid_config."
    )

    # assert privacy request was marked as error
    db.refresh(pr)
    assert pr.status == PrivacyRequestStatus.error

    # and that an error ExecutionLog was created
    error_log = pr.execution_logs.filter(
        ExecutionLog.status == ExecutionLogStatus.error
    )
    assert error_log.count() == 1
    assert (
        error_log.first().message
        == "Connector configuration references invalid dataset field weird-field-no-dots for dataset postgres_example_custom_request_field_dataset."
    )

    # verify the email was not sent
    mock_mailgun_dispatcher.assert_not_called()


@pytest.mark.integration
@pytest.mark.integration_postgres
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
@mock.patch(
    "fides.api.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
)
@mock.patch("fides.api.service.messaging.message_dispatch_service._mailgun_dispatcher")
@mock.patch(
    "fides.api.service.connectors.dynamic_erasure_email_connector.logger",
    autospec=True,
)
async def test_erasure_email_mismatched_datasets(
    logger_mock,
    mock_mailgun_dispatcher: Mock,
    mock_requeue_privacy_requests: Mock,
    # Need to populate the postgres integration DB
    postgres_integration_db,
    # Need to allow custom privacy request fields
    allow_custom_privacy_request_field_collection_enabled,
    allow_custom_privacy_request_fields_in_request_execution_enabled,
    db,
    dsr_version,
    request,
    erasure_policy,
    # Need to create an email connector with mismatched datasets
    dynamic_erasure_email_connection_config_different_datasets,
    run_privacy_request_task,
    # Need a messaging config
    messaging_config,
) -> None:
    """
    Run an erasure privacy request with only a dynamic erasure email connector
    that has been misconfigured with the email recipient dataset different from the
    vendor name dataset.
    """
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    pr = get_privacy_request_results(
        db,
        erasure_policy,
        run_privacy_request_task,
        {
            "requested_at": "2021-08-30T16:09:37.359Z",
            "policy_key": erasure_policy.key,
            "identity": {"email": "customer-1@example.com"},
        },
    )

    db.refresh(pr)
    pr.persist_custom_privacy_request_fields(
        db,
        {
            "tenant_id": CustomPrivacyRequestField(
                label="Tenant Custom Field", value="site-id-1"
            )
        },
    )

    # the privacy request will be in an "awaiting email send" state until the "send email batch" job executes
    assert pr.status == PrivacyRequestStatus.awaiting_email_send
    assert pr.awaiting_email_send_at is not None

    # execute send email batch job without waiting for it to be scheduled
    # we expect the job to raise an exception because the connector is misconfigured
    with pytest.raises(DynamicErasureEmailConnectorException) as exc:
        send_email_batch.delay().get()

    assert (
        str(exc.value)
        == "Dynamic Erasure Email Connector with key my_dynamic_erasure_email_config_mismatched_datasets references different datasets for email and vendor fields. Erasure emails not sent."
    )

    # assert error was logged
    logger_mock.error.assert_called_once_with(
        "Dynamic Erasure Email Connector with key my_dynamic_erasure_email_config_mismatched_datasets references different datasets for email and vendor fields. Erasure emails not sent."
    )
    # assert privacy request was marked as error
    db.refresh(pr)
    assert pr.status == PrivacyRequestStatus.error

    # and that an error ExecutionLog was created
    error_log = pr.execution_logs.filter(
        ExecutionLog.status == ExecutionLogStatus.error
    )
    assert error_log.count() == 1
    assert (
        error_log.first().message
        == "Connector configuration references different datasets for email and vendor fields."
    )

    # verify the email was not sent
    mock_mailgun_dispatcher.assert_not_called()


@pytest.mark.integration
@pytest.mark.integration_postgres
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
@mock.patch(
    "fides.api.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
)
@mock.patch("fides.api.service.messaging.message_dispatch_service._mailgun_dispatcher")
@mock.patch(
    "fides.api.service.connectors.dynamic_erasure_email_connector.logger",
    autospec=True,
)
async def test_erasure_email_mismatched_collections(
    logger_mock,
    mock_mailgun_dispatcher: Mock,
    mock_requeue_privacy_requests: Mock,
    # Need to populate the postgres integration DB
    postgres_integration_db,
    # Need to allow custom privacy request fields
    allow_custom_privacy_request_field_collection_enabled,
    allow_custom_privacy_request_fields_in_request_execution_enabled,
    db,
    dsr_version,
    request,
    erasure_policy,
    # Need to create an email connector with mismatched datasets
    dynamic_erasure_email_connection_config_different_collections,
    run_privacy_request_task,
    # Need a messaging config
    messaging_config,
) -> None:
    """
    Run an erasure privacy request with only a dynamic erasure email connector
    that has been misconfigured with the email recipient collection different from the
    vendor name collection.
    """
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    pr = get_privacy_request_results(
        db,
        erasure_policy,
        run_privacy_request_task,
        {
            "requested_at": "2021-08-30T16:09:37.359Z",
            "policy_key": erasure_policy.key,
            "identity": {"email": "customer-1@example.com"},
        },
    )

    db.refresh(pr)
    pr.persist_custom_privacy_request_fields(
        db,
        {
            "tenant_id": CustomPrivacyRequestField(
                label="Tenant Custom Field", value="site-id-1"
            )
        },
    )

    # the privacy request will be in an "awaiting email send" state until the "send email batch" job executes
    assert pr.status == PrivacyRequestStatus.awaiting_email_send
    assert pr.awaiting_email_send_at is not None

    # execute send email batch job without waiting for it to be scheduled
    # we expect the job to raise an exception because the connector is misconfigured
    with pytest.raises(DynamicErasureEmailConnectorException) as exc:
        send_email_batch.delay().get()

    assert (
        str(exc.value)
        == "Dynamic Erasure Email Connector with key my_dynamic_erasure_email_config_mismatched_datasets references different collections for email and vendor fields. Erasure emails not sent."
    )

    # assert error was logged
    logger_mock.error.assert_called_once_with(
        "Dynamic Erasure Email Connector with key my_dynamic_erasure_email_config_mismatched_datasets references different collections for email and vendor fields. Erasure emails not sent."
    )
    # assert privacy request was marked as error
    db.refresh(pr)
    assert pr.status == PrivacyRequestStatus.error

    # and that an error ExecutionLog was created
    error_log = pr.execution_logs.filter(
        ExecutionLog.status == ExecutionLogStatus.error
    )
    assert error_log.count() == 1
    assert (
        error_log.first().message
        == "Connector configuration references different collections for email and vendor fields."
    )

    # verify the email was not sent
    mock_mailgun_dispatcher.assert_not_called()


@pytest.mark.integration
@pytest.mark.integration_postgres
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
@mock.patch(
    "fides.api.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
)
@mock.patch("fides.api.service.messaging.message_dispatch_service._mailgun_dispatcher")
async def test_erasure_email_no_email_address(
    mock_mailgun_dispatcher: Mock,
    mock_requeue_privacy_requests: Mock,
    # Need to populate the postgres integration DB
    postgres_integration_db,
    # Need to allow custom privacy request fields
    allow_custom_privacy_request_field_collection_enabled,
    allow_custom_privacy_request_fields_in_request_execution_enabled,
    db,
    dsr_version,
    request,
    erasure_policy,
    # Need to create a dynamic erasure email connector
    test_dynamic_erasure_email_connector,
    run_privacy_request_task,
    # Need a messaging config
    messaging_config,
) -> None:
    """
    Run an erasure privacy request with only a dynamic erasure email connector,
    where the provided custom field does not produce an email address.
    """
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    pr = get_privacy_request_results(
        db,
        erasure_policy,
        run_privacy_request_task,
        {
            "requested_at": "2021-08-30T16:09:37.359Z",
            "policy_key": erasure_policy.key,
            "identity": {"email": "customer-1@example.com"},
        },
    )

    db.refresh(pr)
    pr.persist_custom_privacy_request_fields(
        db,
        {
            "tenant_id": CustomPrivacyRequestField(
                label="Tenant Custom Field",
                value="site-id-8",  # site-id-8 does not exist on the dynamic_email_address_config table
            )
        },
    )

    # the privacy request will be in an "awaiting email send" state until the "send email batch" job executes
    assert pr.status == PrivacyRequestStatus.awaiting_email_send
    assert pr.awaiting_email_send_at is not None

    # execute send email batch job without waiting for it to be scheduled
    exit_state = send_email_batch.delay().get()
    assert exit_state == EmailExitState.complete

    # assert privacy request was marked as error
    db.refresh(pr)
    assert pr.status == PrivacyRequestStatus.error

    # and that an error ExecutionLog was created
    error_log = pr.execution_logs.filter(
        ExecutionLog.status == ExecutionLogStatus.error
    )
    assert error_log.count() == 1
    assert (
        error_log.first().message
        == "Custom request field lookup produced no results: no email address matching custom request fields was found."
    )

    # verify the email was not sent
    mock_mailgun_dispatcher.assert_not_called()


@pytest.mark.integration
@pytest.mark.integration_postgres
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
@mock.patch(
    "fides.api.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
)
@mock.patch("fides.api.service.messaging.message_dispatch_service._mailgun_dispatcher")
async def test_erasure_email_multiple_email_addresses(
    mock_mailgun_dispatcher: Mock,
    mock_requeue_privacy_requests: Mock,
    # Need to populate the postgres integration DB
    postgres_integration_db,
    # Need to allow custom privacy request fields
    allow_custom_privacy_request_field_collection_enabled,
    allow_custom_privacy_request_fields_in_request_execution_enabled,
    db,
    dsr_version,
    request,
    erasure_policy,
    # Need to create a dynamic erasure email connector
    test_dynamic_erasure_email_connector,
    run_privacy_request_task,
    # Need a messaging config
    messaging_config,
) -> None:
    """
    Run an erasure privacy request with only a dynamic erasure email connector,
    where the provided custom field lookup returns more than 1 row.
    """
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    pr = get_privacy_request_results(
        db,
        erasure_policy,
        run_privacy_request_task,
        {
            "requested_at": "2021-08-30T16:09:37.359Z",
            "policy_key": erasure_policy.key,
            "identity": {"email": "customer-1@example.com"},
        },
    )

    db.refresh(pr)
    pr.persist_custom_privacy_request_fields(
        db,
        {
            "tenant_id": CustomPrivacyRequestField(
                label="Tenant Custom Field",
                value="site-id-multiple-emails",
            )
        },
    )

    # the privacy request will be in an "awaiting email send" state until the "send email batch" job executes
    assert pr.status == PrivacyRequestStatus.awaiting_email_send
    assert pr.awaiting_email_send_at is not None

    # execute send email batch job without waiting for it to be scheduled
    exit_state = send_email_batch.delay().get()
    assert exit_state == EmailExitState.complete

    # assert privacy request was marked as error
    db.refresh(pr)
    assert pr.status == PrivacyRequestStatus.error

    # and that an error ExecutionLog was created
    error_log = pr.execution_logs.filter(
        ExecutionLog.status == ExecutionLogStatus.error
    )
    assert error_log.count() == 1
    assert (
        error_log.first().message
        == "Custom request field lookup produced multiple results: multiple email addresses returned for provided custom fields."
    )

    # verify the email was not sent
    mock_mailgun_dispatcher.assert_not_called()


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.integration_postgres
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
@mock.patch(
    "fides.api.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
)
@mock.patch("fides.api.service.messaging.message_dispatch_service._mailgun_dispatcher")
async def test_erasure_email_property_specific_messaging(
    mock_mailgun_dispatcher: Mock,
    mock_requeue_privacy_requests: Mock,
    # Need to populate the postgres integration DB
    postgres_integration_db,
    # Need to allow custom privacy request fields
    allow_custom_privacy_request_field_collection_enabled,
    allow_custom_privacy_request_fields_in_request_execution_enabled,
    db,
    dsr_version,
    request,
    erasure_policy,
    # Need to create a dynamic erasure email connector
    test_dynamic_erasure_email_connector,
    run_privacy_request_task,
    # Need a messaging config
    messaging_config,
    set_property_specific_messaging_enabled,
) -> None:
    """
    Run an erasure privacy request with only a dynamic erasure email connector
    with property specific messaging enabled.
    Verify the privacy request is set to "awaiting email send" and that one email
    is sent when the send_email_batch job is executed manually
    """
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    pr = get_privacy_request_results(
        db,
        erasure_policy,
        run_privacy_request_task,
        {
            "requested_at": "2021-08-30T16:09:37.359Z",
            "policy_key": erasure_policy.key,
            "identity": {"email": "customer-1@example.com"},
        },
    )

    db.refresh(pr)
    pr.persist_custom_privacy_request_fields(
        db,
        {
            "tenant_id": CustomPrivacyRequestField(
                label="Tenant Custom Field", value="site-id-1"
            )
        },
    )

    # the privacy request will be in an "awaiting email send" state until the "send email batch" job executes
    assert pr.status == PrivacyRequestStatus.awaiting_email_send
    assert pr.awaiting_email_send_at is not None

    # execute send email batch job without waiting for it to be scheduled
    exit_state = send_email_batch.delay().get()
    assert exit_state == EmailExitState.complete

    # verify the email was sent
    erasure_email_template = get_email_template(
        MessagingActionType.MESSAGE_ERASURE_REQUEST_FULFILLMENT
    )
    mock_mailgun_dispatcher.assert_called_once_with(
        ANY,
        EmailForActionType(
            subject="Notification of user erasure requests from Test Org",
            body=erasure_email_template.render(
                {
                    "controller": "Test Org",
                    "third_party_vendor_name": "Vendor 1",
                    "identities": ["customer-1@example.com"],
                }
            ),
        ),
        "test@test.com",
    )

    # verify the privacy request was queued for further processing
    mock_requeue_privacy_requests.assert_called()


@pytest.mark.integration
@pytest.mark.integration_postgres
@pytest.mark.asyncio
@mock.patch(
    "fides.api.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
)
@mock.patch("fides.api.service.messaging.message_dispatch_service._mailgun_dispatcher")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_erasure_email_no_messaging_config(
    mock_mailgun_dispatcher: Mock,
    mock_requeue_privacy_requests: Mock,
    # Need to populate the postgres integration DB
    postgres_integration_db,
    # Need to allow custom privacy request fields
    allow_custom_privacy_request_field_collection_enabled,
    allow_custom_privacy_request_fields_in_request_execution_enabled,
    db,
    dsr_version,
    request,
    erasure_policy,
    # Need to create a dynamic erasure email connector
    test_dynamic_erasure_email_connector,
    run_privacy_request_task,
) -> None:
    """
    Run an erasure privacy request with only a dynamic erasure email connector.
    Verify the privacy request is set to "awaiting email send" and that the
    email fails to send because of the missing messaging config.
    """
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    pr = get_privacy_request_results(
        db,
        erasure_policy,
        run_privacy_request_task,
        {
            "requested_at": "2021-08-30T16:09:37.359Z",
            "policy_key": erasure_policy.key,
            "identity": {"email": "customer-1@example.com"},
        },
    )

    db.refresh(pr)
    pr.persist_custom_privacy_request_fields(
        db,
        {
            "tenant_id": CustomPrivacyRequestField(
                label="Tenant Custom Field", value="site-id-1"
            )
        },
    )

    # the privacy request will be in an "awaiting email send" state until the "send email batch" job executes
    assert pr.status == PrivacyRequestStatus.awaiting_email_send
    assert pr.awaiting_email_send_at is not None

    # execute send email batch job without waiting for it to be scheduled
    exit_state = send_email_batch.delay().get()
    # job will fail because there is no messaging config
    assert exit_state == EmailExitState.email_send_failed

    mock_mailgun_dispatcher.assert_not_called()
    mock_requeue_privacy_requests.assert_not_called()


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
@mock.patch("fides.api.service.messaging.message_dispatch_service._mailgun_dispatcher")
async def test_erasure_email_no_write_permissions(
    mock_mailgun_dispatcher: Mock,
    # Need to allow custom privacy request fields
    allow_custom_privacy_request_field_collection_enabled,
    allow_custom_privacy_request_fields_in_request_execution_enabled,
    db,
    dsr_version,
    request,
    erasure_policy,
    dynamic_erasure_email_connection_config,
    # Need to create a dynamic erasure email connector
    test_dynamic_erasure_email_connector,
    run_privacy_request_task,
    # Need a messaging config
    messaging_config,
) -> None:
    """
    Run an erasure privacy request with only a dynamic erasure email connector.
    Verify we don't send an email for a connector with read-only access.
    """
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    dynamic_erasure_email_connection_config.update(
        db=db,
        data={"access": AccessLevel.read},
    )

    pr = get_privacy_request_results(
        db,
        erasure_policy,
        run_privacy_request_task,
        {
            "requested_at": "2021-08-30T16:09:37.359Z",
            "policy_key": erasure_policy.key,
            "identity": {"email": "customer-1@example.com"},
        },
    )

    db.refresh(pr)
    pr.persist_custom_privacy_request_fields(
        db,
        {
            "tenant_id": CustomPrivacyRequestField(
                label="Tenant Custom Field", value="site-id-1"
            )
        },
    )

    # the privacy request will be in an "complete" state since we didn't need to wait for a batch email to go out
    assert pr.status == PrivacyRequestStatus.complete
    # no email scheduled
    assert pr.awaiting_email_send_at is None

    mock_mailgun_dispatcher.assert_not_called()


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_erasure_email_no_updates_needed(
    db,
    dsr_version,
    request,
    policy,
    # Need to create a dynamic erasure email connector
    test_dynamic_erasure_email_connector,
    run_privacy_request_task,
    test_fides_org,
) -> None:
    """
    Run an erasure privacy request with only a dynamic erasure email connector.
    Verify the privacy request is set to "complete" because this is
    an access request and no erasures are needed.
    """
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    pr = get_privacy_request_results(
        db,
        policy,
        run_privacy_request_task,
        {
            "requested_at": "2021-08-30T16:09:37.359Z",
            "policy_key": policy.key,
            "identity": {"email": "customer-1@example.com"},
        },
    )
    db.refresh(pr)

    # the privacy request will be in an "complete" state since we didn't need to wait for a batch email to go out
    assert pr.status == PrivacyRequestStatus.complete
    # no email scheduled
    assert pr.awaiting_email_send_at is None


@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch(
    "fides.api.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
)
@mock.patch("fides.api.service.messaging.message_dispatch_service._mailgun_dispatcher")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_erasure_email_disabled_connector(
    mock_mailgun_dispatcher: Mock,
    mock_requeue_privacy_requests: Mock,
    # Need to allow custom privacy request fields
    allow_custom_privacy_request_field_collection_enabled,
    allow_custom_privacy_request_fields_in_request_execution_enabled,
    db,
    dsr_version,
    request,
    erasure_policy,
    dynamic_erasure_email_connection_config,
    # Need to create a dynamic erasure email connector
    test_dynamic_erasure_email_connector,
    run_privacy_request_task,
    # Need a messaging config
    messaging_config,
) -> None:
    """
    Run an erasure privacy request with only a dynamic erasure email connector.
    Verify the privacy request is set to "awaiting email send" and that one email
    is sent when the send_email_batch job is executed manually
    """
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    dynamic_erasure_email_connection_config.update(
        db=db,
        data={"disabled": True},
    )

    pr = get_privacy_request_results(
        db,
        erasure_policy,
        run_privacy_request_task,
        {
            "requested_at": "2021-08-30T16:09:37.359Z",
            "policy_key": erasure_policy.key,
            "identity": {"email": "customer-1@example.com"},
        },
    )
    pr.persist_custom_privacy_request_fields(
        db,
        {
            "tenant_id": CustomPrivacyRequestField(
                label="Tenant Custom Field", value="site-id-1"
            )
        },
    )

    db.refresh(pr)

    # the privacy request will be in an "complete" state because the erasure email connector was disabled
    assert pr.status == PrivacyRequestStatus.complete
    assert pr.awaiting_email_send_at is None

    mock_mailgun_dispatcher.assert_not_called()
    mock_requeue_privacy_requests.assert_not_called()


@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch(
    "fides.api.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
)
@mock.patch("fides.api.service.messaging.message_dispatch_service._mailgun_dispatcher")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_erasure_email_unsupported_identity(
    mock_mailgun_dispatcher: Mock,
    mock_requeue_privacy_requests: Mock,
    # Need to allow custom privacy request fields
    allow_custom_privacy_request_field_collection_enabled,
    allow_custom_privacy_request_fields_in_request_execution_enabled,
    db,
    dsr_version,
    request,
    erasure_policy,
    # Need to create a dynamic erasure email connector
    test_dynamic_erasure_email_connector,
    run_privacy_request_task,
    # Need a messaging config
    messaging_config,
) -> None:
    """
    Run an erasure privacy request with only a generic erasure email connector.
    Verify the privacy request is set to "complete" because the provided identities are not supported.
    """
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    pr = get_privacy_request_results(
        db,
        erasure_policy,
        run_privacy_request_task,
        {
            "requested_at": "2021-08-30T16:09:37.359Z",
            "policy_key": erasure_policy.key,
            "identity": {"phone_number": "+15551234567"},
        },
    )
    pr.persist_custom_privacy_request_fields(
        db,
        {
            "tenant_id": CustomPrivacyRequestField(
                label="Tenant Custom Field", value="site-id-1"
            )
        },
    )

    db.refresh(pr)

    # the privacy request will be in an "complete" state because
    # the phone number identity is not supported by this connector
    assert pr.status == PrivacyRequestStatus.complete
    assert pr.awaiting_email_send_at is None

    mock_mailgun_dispatcher.assert_not_called()
    mock_requeue_privacy_requests.assert_not_called()
