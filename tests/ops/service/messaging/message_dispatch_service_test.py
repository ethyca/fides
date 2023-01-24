from unittest import mock
from unittest.mock import Mock

import pytest
import requests_mock
from sqlalchemy.orm import Session

from fides.api.ops.common_exceptions import MessageDispatchException
from fides.api.ops.graph.config import CollectionAddress
from fides.api.ops.models.messaging import MessagingConfig
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
from fides.core.config import get_config

CONFIG = get_config()


@pytest.mark.unit
class TestMessageDispatchService:
    @mock.patch(
        "fides.api.ops.service.messaging.message_dispatch_service._mailgun_dispatcher"
    )
    def test_email_dispatch_mailgun_success(
        self, mock_mailgun_dispatcher: Mock, db: Session, messaging_config
    ) -> None:
        dispatch_message(
            db=db,
            action_type=MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
            to_identity=Identity(**{"email": "test@email.com"}),
            service_type=MessagingServiceType.MAILGUN.value,
            message_body_params=SubjectIdentityVerificationBodyParams(
                verification_code="2348", verification_code_ttl_seconds=600
            ),
        )
        body = '<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n    <title>ID Code</title>\n</head>\n<body>\n<main>\n    <p>\n        Your privacy request verification code is 2348.\n        Please return to the Privacy Center and enter the code to\n        continue. This code will expire in 10 minutes\n    </p>\n</main>\n</body>\n</html>'
        mock_mailgun_dispatcher.assert_called_with(
            messaging_config,
            EmailForActionType(
                subject="Your one-time code",
                body=body,
            ),
            "test@email.com",
        )

    @mock.patch(
        "fides.api.ops.service.messaging.message_dispatch_service._mailgun_dispatcher"
    )
    def test_email_dispatch_mailgun_config_not_found(
        self, mock_mailgun_dispatcher: Mock, db: Session
    ) -> None:

        with pytest.raises(MessageDispatchException) as exc:
            dispatch_message(
                db=db,
                action_type=MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
                to_identity=Identity(**{"email": "test@email.com"}),
                service_type=MessagingServiceType.MAILGUN.value,
                message_body_params=SubjectIdentityVerificationBodyParams(
                    verification_code="2348", verification_code_ttl_seconds=600
                ),
            )
        assert (
            exc.value.args[0] == "No messaging config found for service_type MAILGUN."
        )

        mock_mailgun_dispatcher.assert_not_called()

    @mock.patch(
        "fides.api.ops.service.messaging.message_dispatch_service._mailgun_dispatcher"
    )
    def test_email_dispatch_mailgun_config_no_secrets(
        self, mock_mailgun_dispatcher: Mock, db: Session
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
                service_type=MessagingServiceType.MAILGUN.value,
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

    def test_email_dispatch_mailgun_failed_email(
        self, db: Session, messaging_config
    ) -> None:
        with requests_mock.Mocker() as mock_response:
            mock_response.get(
                f"https://api.mailgun.net/{messaging_config.details[MessagingServiceDetails.API_VERSION.value]}/{messaging_config.details[MessagingServiceDetails.DOMAIN.value]}/templates/fides",
                status_code=404,
            )
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
                    service_type=MessagingServiceType.MAILGUN.value,
                    message_body_params=SubjectIdentityVerificationBodyParams(
                        verification_code="2348", verification_code_ttl_seconds=600
                    ),
                )
            assert (
                exc.value.args[0]
                == "Email failed to send due to: Email failed to send with status code 403"
            )

    def test_fidesops_email_parse_object(self):
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

    @mock.patch(
        "fides.api.ops.service.messaging.message_dispatch_service._twilio_sms_dispatcher"
    )
    def test_sms_dispatch_twilio_success(
        self, mock_twilio_dispatcher: Mock, db: Session, messaging_config_twilio_sms
    ) -> None:

        dispatch_message(
            db=db,
            action_type=MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
            to_identity=Identity(**{"phone_number": "+12312341231"}),
            service_type=MessagingServiceType.TWILIO_TEXT.value,
            message_body_params=SubjectIdentityVerificationBodyParams(
                verification_code="2348", verification_code_ttl_seconds=600
            ),
        )
        mock_twilio_dispatcher.assert_called_with(
            messaging_config_twilio_sms,
            f"Your privacy request verification code is 2348. "
            + f"Please return to the Privacy Center and enter the code to continue. "
            + f"This code will expire in 10 minutes",
            "+12312341231",
        )

    def test_sms_dispatch_twilio_no_to(self, db, messaging_config_twilio_sms):
        with pytest.raises(MessageDispatchException) as err:
            dispatch_message(
                db=db,
                action_type=MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
                to_identity=Identity(phone_number=None),
                service_type=MessagingServiceType.TWILIO_TEXT.value,
                message_body_params=SubjectIdentityVerificationBodyParams(
                    verification_code="2348", verification_code_ttl_seconds=600
                ),
            )

        assert "No phone identity supplied." in str(err.value)

    @mock.patch(
        "fides.api.ops.service.messaging.message_dispatch_service._twilio_sms_dispatcher"
    )
    def test_sms_dispatch_twilio_config_not_found(
        self, mock_twilio_dispatcher: Mock, db: Session
    ) -> None:

        with pytest.raises(MessageDispatchException) as exc:
            dispatch_message(
                db=db,
                action_type=MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
                to_identity=Identity(**{"phone_number": "+12312341231"}),
                service_type=MessagingServiceType.TWILIO_TEXT.value,
                message_body_params=SubjectIdentityVerificationBodyParams(
                    verification_code="2348", verification_code_ttl_seconds=600
                ),
            )
        assert (
            exc.value.args[0]
            == "No messaging config found for service_type TWILIO_TEXT."
        )

        mock_twilio_dispatcher.assert_not_called()

    @mock.patch(
        "fides.api.ops.service.messaging.message_dispatch_service._twilio_sms_dispatcher"
    )
    def test_sms_dispatch_twilio_config_no_secrets(
        self, mock_mailgun_dispatcher: Mock, db: Session
    ) -> None:

        messaging_config = MessagingConfig.create(
            db=db,
            data={
                "name": "twilio sms config",
                "key": "my_twilio_sms_config",
                "service_type": MessagingServiceType.TWILIO_TEXT,
            },
        )

        with pytest.raises(MessageDispatchException) as exc:
            dispatch_message(
                db=db,
                action_type=MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
                to_identity=Identity(**{"phone_number": "+12312341231"}),
                service_type=MessagingServiceType.TWILIO_TEXT.value,
                message_body_params=SubjectIdentityVerificationBodyParams(
                    verification_code="2348", verification_code_ttl_seconds=600
                ),
            )
        assert (
            exc.value.args[0]
            == "Messaging secrets not found for config with key: my_twilio_sms_config"
        )

        mock_mailgun_dispatcher.assert_not_called()

        messaging_config.delete(db)

    @mock.patch(
        "fides.api.ops.service.messaging.message_dispatch_service._twilio_sms_dispatcher"
    )
    def test_dispatch_no_identity(
        self, mock_mailgun_dispatcher: Mock, db: Session
    ) -> None:
        MessagingConfig.create(
            db=db,
            data={
                "name": "twilio sms config",
                "key": "my_twilio_sms_config",
                "service_type": MessagingServiceType.TWILIO_TEXT,
            },
        )

        with pytest.raises(MessageDispatchException) as exc:
            dispatch_message(
                db=db,
                action_type=MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
                to_identity=None,
                service_type=MessagingServiceType.TWILIO_TEXT.value,
                message_body_params=SubjectIdentityVerificationBodyParams(
                    verification_code="2348", verification_code_ttl_seconds=600
                ),
            )

        assert "No identity supplied" in exc.value.args[0]

        mock_mailgun_dispatcher.assert_not_called()

    @mock.patch(
        "fides.api.ops.service.messaging.message_dispatch_service._twilio_sms_dispatcher"
    )
    def test_dispatch_no_service_type(
        self, mock_mailgun_dispatcher: Mock, db: Session
    ) -> None:
        MessagingConfig.create(
            db=db,
            data={
                "name": "twilio sms config",
                "key": "my_twilio_sms_config",
                "service_type": MessagingServiceType.TWILIO_TEXT,
            },
        )

        with pytest.raises(MessageDispatchException) as exc:
            dispatch_message(
                db=db,
                action_type=MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
                to_identity=Identity(**{"phone_number": "+12312341231"}),
                service_type=None,
                message_body_params=SubjectIdentityVerificationBodyParams(
                    verification_code="2348", verification_code_ttl_seconds=600
                ),
            )

        assert "No notification service type configured" in exc.value.args[0]

        mock_mailgun_dispatcher.assert_not_called()
