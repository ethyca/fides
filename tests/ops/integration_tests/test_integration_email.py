from unittest import mock
from unittest.mock import ANY, Mock

import pytest as pytest

from fides.api.ops.email_templates import get_email_template
from fides.api.ops.models.privacy_request import PrivacyRequestStatus
from fides.api.ops.schemas.messaging.messaging import (
    EmailForActionType,
    MessagingActionType,
)
from fides.api.ops.service.privacy_request.email_batch_service import (
    ConsentEmailExitState,
    send_email_batch,
)
from tests.ops.service.privacy_request.test_request_runner_service import (
    get_privacy_request_results,
)


@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch(
    "fides.api.ops.service.privacy_request.email_batch_service.requeue_privacy_requests_after_email_send",
)
@mock.patch(
    "fides.api.ops.service.messaging.message_dispatch_service._mailgun_dispatcher"
)
async def test_erasure_email_delayed_send(
    mock_mailgun_dispatcher: Mock,
    mock_requeue_privacy_requests: Mock,
    db,
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
    assert exit_state == ConsentEmailExitState.complete

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
                    "third_party_vendor_name": "Attentive",
                    "identities": ["customer-1@example.com"],
                }
            ),
        ),
        "attentive@example.com",
    )

    # verify the privacy request was queued for further processing
    mock_requeue_privacy_requests.assert_called()
