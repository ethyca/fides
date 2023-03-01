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
    ConsentEmailFulfillmentBodyParams,
    ConsentPreferencesByUser,
    EmailForActionType,
    FidesopsMessage,
    MessagingActionType,
    MessagingServiceDetails,
    MessagingServiceSecrets,
    MessagingServiceType,
    SubjectIdentityVerificationBodyParams,
)
from fides.api.ops.schemas.privacy_request import Consent
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.messaging.message_dispatch_service import (
    _get_dispatcher_from_config_type,
    _twilio_email_dispatcher,
    _twilio_sms_dispatcher,
    dispatch_message,
)
from fides.core.config import CONFIG


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

    @mock.patch(
        "fides.api.ops.service.messaging.message_dispatch_service._mailgun_dispatcher"
    )
    def test_email_dispatch_mailgun_test_message(
        self, mock_mailgun_dispatcher, db, messaging_config
    ):
        dispatch_message(
            db=db,
            action_type=MessagingActionType.TEST_MESSAGE,
            to_identity=Identity(email="test@email.com"),
            service_type=MessagingServiceType.MAILGUN.value,
        )
        body = '<!DOCTYPE html>\n<html lang="en">\n  <head>\n    <meta charset="UTF-8" />\n    <title>Fides Test message</title>\n  </head>\n  <body>\n    <main>\n      <p>This is a test message from Fides.</p>\n    </main>\n  </body>\n</html>'
        mock_mailgun_dispatcher.assert_called_with(
            messaging_config,
            EmailForActionType(
                subject="Test message from fides",
                body=body,
            ),
            "test@email.com",
        )

    @mock.patch(
        "fides.api.ops.service.messaging.message_dispatch_service._twilio_email_dispatcher"
    )
    def test_email_dispatch_twilio_email_test_message(
        self, mock_twilio_dispatcher, db, messaging_config_twilio_email
    ):
        dispatch_message(
            db=db,
            action_type=MessagingActionType.TEST_MESSAGE,
            to_identity=Identity(email="test@email.com"),
            service_type=MessagingServiceType.TWILIO_EMAIL.value,
        )
        body = '<!DOCTYPE html>\n<html lang="en">\n  <head>\n    <meta charset="UTF-8" />\n    <title>Fides Test message</title>\n  </head>\n  <body>\n    <main>\n      <p>This is a test message from Fides.</p>\n    </main>\n  </body>\n</html>'
        mock_twilio_dispatcher.assert_called_with(
            messaging_config_twilio_email,
            EmailForActionType(
                subject="Test message from fides",
                body=body,
            ),
            "test@email.com",
        )

    @mock.patch(
        "fides.api.ops.service.messaging.message_dispatch_service._twilio_sms_dispatcher"
    )
    def test_email_dispatch_twilio_sms_test_message(
        self, mock_twilio_dispatcher, db, messaging_config_twilio_sms
    ):
        dispatch_message(
            db=db,
            action_type=MessagingActionType.TEST_MESSAGE,
            to_identity=Identity(phone_number="+19198675309"),
            service_type=MessagingServiceType.TWILIO_TEXT.value,
        )
        body = '<!DOCTYPE html>\n<html lang="en">\n  <head>\n    <meta charset="UTF-8" />\n    <title>Fides Test message</title>\n  </head>\n  <body>\n    <main>\n      <p>This is a test message from Fides.</p>\n    </main>\n  </body>\n</html>'
        mock_twilio_dispatcher.assert_called_with(
            messaging_config_twilio_sms,
            "Test message from Fides.",
            "+19198675309",
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

    def test_dispatch_invalid_action_type(self, db):
        with pytest.raises(MessageDispatchException):
            dispatch_message(db, "bad", None, None)

    def test_dispatcher_from_config_type_unknown(self):
        assert _get_dispatcher_from_config_type("bad") is None


class TestTwilioEmailDispatcher:
    def test_dispatch_no_to(self, messaging_config_twilio_email):
        with pytest.raises(MessageDispatchException) as exc:
            _twilio_email_dispatcher(messaging_config_twilio_email, "test", None)

        assert "No email identity" in str(exc.value)

    def test_dispatch_no_secrets(self, messaging_config_twilio_email):
        messaging_config_twilio_email.secrets = None
        with pytest.raises(MessageDispatchException) as exc:
            _twilio_email_dispatcher(
                messaging_config_twilio_email,
                EmailForActionType(subject="test", body="test body"),
                "test@email.com",
            )

        assert "No twilio email config details or secrets" in str(exc.value)


class TestTwilioSmsDispatcher:
    def test_dispatch_no_to(self, messaging_config_twilio_sms):
        with pytest.raises(MessageDispatchException) as exc:
            _twilio_sms_dispatcher(messaging_config_twilio_sms, "test", None)

        assert "No phone identity" in str(exc.value)

    def test_dispatch_no_secrets(self, messaging_config_twilio_sms):
        messaging_config_twilio_sms.secrets = None
        with pytest.raises(MessageDispatchException) as exc:
            _twilio_sms_dispatcher(messaging_config_twilio_sms, "test", "+9198675309")

        assert "No config secrets" in str(exc.value)

    def test_dispatch_no_sender(self, messaging_config_twilio_sms):
        messaging_config_twilio_sms.secrets[
            MessagingServiceSecrets.TWILIO_MESSAGING_SERVICE_SID.value
        ] = None
        messaging_config_twilio_sms.secrets[
            MessagingServiceSecrets.TWILIO_SENDER_PHONE_NUMBER.value
        ] = None
        with pytest.raises(MessageDispatchException) as exc:
            _twilio_sms_dispatcher(messaging_config_twilio_sms, "test", "+9198675309")

        assert "must be provided" in str(exc.value)

    @mock.patch(
        "fides.api.ops.service.messaging.message_dispatch_service._mailgun_dispatcher"
    )
    def test_subject_override_for_email(
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
            subject_override="Testing subject override",
        )
        body = '<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n    <title>ID Code</title>\n</head>\n<body>\n<main>\n    <p>\n        Your privacy request verification code is 2348.\n        Please return to the Privacy Center and enter the code to\n        continue. This code will expire in 10 minutes\n    </p>\n</main>\n</body>\n</html>'
        mock_mailgun_dispatcher.assert_called_with(
            messaging_config,
            EmailForActionType(
                subject="Testing subject override",
                body=body,
            ),
            "test@email.com",
        )

    @mock.patch(
        "fides.api.ops.service.messaging.message_dispatch_service._twilio_sms_dispatcher"
    )
    def test_sms_subject_override_ignored(
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
            subject_override="override subject",
        )
        mock_twilio_dispatcher.assert_called_with(
            messaging_config_twilio_sms,
            f"Your privacy request verification code is 2348. "
            + f"Please return to the Privacy Center and enter the code to continue. "
            + f"This code will expire in 10 minutes",
            "+12312341231",
        )

    @mock.patch(
        "fides.api.ops.service.messaging.message_dispatch_service._mailgun_dispatcher"
    )
    def test_email_dispatch_consent_request_email_fulfillment_for_sovrn(
        self, mock_mailgun_dispatcher: Mock, db: Session, messaging_config
    ) -> None:
        dispatch_message(
            db=db,
            action_type=MessagingActionType.CONSENT_REQUEST_EMAIL_FULFILLMENT,
            to_identity=Identity(**{"email": "sovrn_test@example.com"}),
            service_type=MessagingServiceType.MAILGUN.value,
            message_body_params=ConsentEmailFulfillmentBodyParams(
                controller="Test Organization",
                third_party_vendor_name="Sovrn",
                required_identities=["ljt_readerID"],
                requested_changes=[
                    ConsentPreferencesByUser(
                        identities={"ljt_readerID": "test_user_id"},
                        consent_preferences=[
                            Consent(data_use="advertising", opt_in=False),
                            Consent(data_use="advertising.first_party", opt_in=True),
                        ],
                    )
                ],
            ),
        )

        body = '<!DOCTYPE html>\n<html lang="en">\n   <head>\n      <meta charset="UTF-8">\n      <title>Notification of users\' consent preference changes from Test Organization</title>\n      <style>\n         .consent_preferences {\n           padding: 5px;\n           border-bottom: 1px solid #121439;\n           text-align: left;\n         }\n         .identity_column {\n           padding-right: 15px;\n         }\n      </style>\n   </head>\n   <body>\n      <main>\n         <p> The following users of Test Organization have made changes to their consent preferences. You are notified of the changes because\n            Sovrn has been identified as a third-party processor to Test Organization that processes user information. </p>\n\n         <p> Please find below the updated list of users and their consent preferences:\n            <table>\n               <tr>\n                 <th class="identity_column"> ljt_readerID</th>\n                 <th>Preferences</th>\n               </tr>\n               <tr class="consent_preferences">\n                     <td class="identity_column"> test_user_id</td>\n                     <td>\n                        Advertising, Marketing or Promotion: Opt-out, First Party Advertising: Opt-in\n                     </td>\n                  </tr>\n            </table>\n         </p>\n\n         <p> You are legally obligated to honor the users\' consent preferences. </p>\n\n      </main>\n   </body>\n</html>'
        mock_mailgun_dispatcher.assert_called_with(
            messaging_config,
            EmailForActionType(
                subject="Notification of users' consent preference changes",
                body=body,
            ),
            "sovrn_test@example.com",
        )
