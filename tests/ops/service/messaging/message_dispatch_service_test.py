from unittest import mock
from unittest.mock import Mock

import pytest
import requests_mock
from sqlalchemy.orm import Session

from fides.api.ops.common_exceptions import MessageDispatchException
from fides.api.ops.graph.config import CollectionAddress
from fides.api.ops.models.messaging import MessagingConfig, get_messaging_method
from fides.api.ops.models.policy import CurrentStep
from fides.api.ops.models.privacy_request import CheckpointActionRequired, ManualAction
from fides.api.ops.schemas.messaging.messaging import (
    EmailForActionType,
    FidesopsMessage,
    MessagingActionType,
    MessagingServiceDetails,
    MessagingServiceType,
    SubjectIdentityVerificationBodyParams,
)
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.messaging.message_dispatch_service import dispatch_message
from fides.ctl.core.config import get_config

CONFIG = get_config()


@mock.patch(
    "fides.api.ops.service.messaging.message_dispatch_service._mailgun_dispatcher"
)
def test_email_dispatch_mailgun_success(
    mock_mailgun_dispatcher: Mock, db: Session, messaging_config
) -> None:

    dispatch_message(
        db=db,
        action_type=MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
        to_identity=Identity(**{"email": "test@email.com"}),
        messaging_method=get_messaging_method(MessagingServiceType.MAILGUN.value),
        message_body_params=SubjectIdentityVerificationBodyParams(
            verification_code="2348", verification_code_ttl_seconds=600
        ),
    )
    body = '<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n    <title>ID Code</title>\n</head>\n<body>\n<main>\n    <p>\n        Your privacy request verification code is 2348.\n        Please return to the Privacy Center and enter the code to\n        continue. This code will expire in 10 minutes\n    </p>\n</main>\n</body>\n</html>'
    mock_mailgun_dispatcher.assert_called_with(
        messaging_config=messaging_config,
        message=EmailForActionType(
            subject="Your one-time code",
            body=body,
        ),
        to="test@email.com",
    )


@mock.patch(
    "fides.api.ops.service.messaging.message_dispatch_service._mailgun_dispatcher"
)
def test_email_dispatch_mailgun_config_not_found(
    mock_mailgun_dispatcher: Mock, db: Session
) -> None:

    with pytest.raises(MessageDispatchException) as exc:
        dispatch_message(
            db=db,
            action_type=MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
            to_identity=Identity(**{"email": "test@email.com"}),
            messaging_method=get_messaging_method(MessagingServiceType.MAILGUN.value),
            message_body_params=SubjectIdentityVerificationBodyParams(
                verification_code="2348", verification_code_ttl_seconds=600
            ),
        )
    assert exc.value.args[0] == "No messaging config found."

    mock_mailgun_dispatcher.assert_not_called()


@mock.patch(
    "fides.api.ops.service.messaging.message_dispatch_service._mailgun_dispatcher"
)
def test_email_dispatch_mailgun_config_no_secrets(
    mock_mailgun_dispatcher: Mock, db: Session
) -> None:

    messaging_config = MessagingConfig.create(
        db=db,
        data={
            "name": "mailgun config",
            "key": "my_mailgun_messaging_config",
            "service_type": MessagingServiceType.MAILGUN,
            "details": {
                MessagingServiceDetails.DOMAIN.value: "some.domain",
            },
        },
    )

    with pytest.raises(MessageDispatchException) as exc:
        dispatch_message(
            db=db,
            action_type=MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
            to_identity=Identity(**{"email": "test@email.com"}),
            messaging_method=get_messaging_method(MessagingServiceType.MAILGUN.value),
            message_body_params=SubjectIdentityVerificationBodyParams(
                verification_code="2348", verification_code_ttl_seconds=600
            ),
        )
    assert (
        exc.value.args[0]
        == "Messaging secrets not found for config with key: my_mailgun_messaging_config"
    )

    mock_mailgun_dispatcher.assert_not_called()

    messaging_config.delete(db)


def test_email_dispatch_mailgun_failed_email(db: Session, messaging_config) -> None:
    with requests_mock.Mocker() as mock_response:
        mock_response.post(
            f"https://api.mailgun.net/{messaging_config.details[MessagingServiceDetails.API_VERSION.value]}/{messaging_config.details[MessagingServiceDetails.DOMAIN.value]}/messages",
            json={
                "message": "Rejected: IP <id-address> can’t be used to send the message",
                "id": "<20111114174239.25659.5817@samples.mailgun.org>",
            },
            status_code=403,
        )
        with pytest.raises(MessageDispatchException) as exc:
            dispatch_message(
                db=db,
                action_type=MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
                to_identity=Identity(**{"email": "test@email.com"}),
                messaging_method=get_messaging_method(
                    MessagingServiceType.MAILGUN.value
                ),
                message_body_params=SubjectIdentityVerificationBodyParams(
                    verification_code="2348", verification_code_ttl_seconds=600
                ),
            )
        assert (
            exc.value.args[0]
            == "Email failed to send due to: Email failed to send with status code 403"
        )


def test_fidesops_email_parse_object():
    body = [
        CheckpointActionRequired(
            step=CurrentStep.erasure,
            collection=CollectionAddress("email_dataset", "test_collection"),
            action_needed=[
                ManualAction(
                    locators={"email": "test@example.com"},
                    get=None,
                    update={"phone": "null_rewrite"},
                )
            ],
        )
    ]

    FidesopsMessage.parse_obj(
        {
            "action_type": MessagingActionType.MESSAGE_ERASURE_REQUEST_FULFILLMENT,
            "body_params": [action.dict() for action in body],
        }
    )

    FidesopsMessage.parse_obj(
        {
            "action_type": MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
            "body_params": {
                "verification_code": "123456",
                "verification_code_ttl_seconds": 1000,
            },
        }
    )
