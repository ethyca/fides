from unittest import mock
from unittest.mock import ANY, Mock

import pytest as pytest

from fides.api.email_templates import get_email_template
from fides.api.models.connectionconfig import AccessLevel
from fides.api.models.privacy_request import PrivacyRequestStatus
from fides.api.schemas.messaging.messaging import (
    EmailForActionType,
    MessagingActionType,
)
from fides.api.service.privacy_request.email_batch_service import (
    EmailExitState,
    send_email_batch,
)
from tests.ops.service.privacy_request.test_request_runner_service import (
    get_privacy_request_results,
)


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
async def test_erasure_email(
    mock_mailgun_dispatcher: Mock,
    mock_requeue_privacy_requests: Mock,
    db,
    dsr_version,
    request,
    erasure_policy,
    attentive_email_connection_config,
    run_privacy_request_task,
    test_fides_org,
    messaging_config,
) -> None:
    """
    Run an erasure privacy request with only an email (Attentive) connector.
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
                    "third_party_vendor_name": "Attentive Email",
                    "identities": ["customer-1@example.com"],
                }
            ),
        ),
        "attentive@example.com",
    )

    # verify the privacy request was queued for further processing
    mock_requeue_privacy_requests.assert_called()


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
async def test_erasure_email_no_messaging_config(
    mock_mailgun_dispatcher: Mock,
    mock_requeue_privacy_requests: Mock,
    db,
    dsr_version,
    request,
    erasure_policy,
    attentive_email_connection_config,
    run_privacy_request_task,
    test_fides_org,
) -> None:
    """
    Run an erasure privacy request with only an email (Attentive) connector.
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
async def test_erasure_email_no_write_permissions(
    db,
    dsr_version,
    request,
    erasure_policy,
    attentive_email_connection_config,
    run_privacy_request_task,
    test_fides_org,
) -> None:
    """
    Run an erasure privacy request with only an email (Attentive) connector.
    Verify we don't send an email for a connector with read-only access.
    """
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    attentive_email_connection_config.update(
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

    # the privacy request will be in an "complete" state since we didn't need to wait for a batch email to go out
    assert pr.status == PrivacyRequestStatus.complete
    # no email scheduled
    assert pr.awaiting_email_send_at is None


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
    attentive_email_connection_config,
    run_privacy_request_task,
    test_fides_org,
) -> None:
    """
    Run an erasure privacy request with only an email (Attentive) connector.
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
    db,
    dsr_version,
    request,
    erasure_policy,
    attentive_email_connection_config,
    run_privacy_request_task,
    test_fides_org,
    messaging_config,
) -> None:
    """
    Run an erasure privacy request with only an email (Attentive) connector.
    Verify the privacy request is set to "awaiting email send" and that one email
    is sent when the send_email_batch job is executed manually
    """
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    attentive_email_connection_config.update(
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

    db.refresh(pr)

    # the privacy request will be in an "complete" state because the erasure email connector was disabled
    assert pr.status == PrivacyRequestStatus.complete
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
async def test_erasure_email_unsupported_identity(
    mock_mailgun_dispatcher: Mock,
    mock_requeue_privacy_requests: Mock,
    db,
    dsr_version,
    request,
    erasure_policy,
    attentive_email_connection_config,
    run_privacy_request_task,
    test_fides_org,
    messaging_config,
) -> None:
    """
    Run an erasure privacy request with only an email (Attentive) connector.
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

    db.refresh(pr)

    # the privacy request will be in an "complete" state because
    # the phone number identity is not supported by this connector
    assert pr.status == PrivacyRequestStatus.complete
    assert pr.awaiting_email_send_at is None
