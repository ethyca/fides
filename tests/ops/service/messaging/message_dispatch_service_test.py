from unittest import mock
from unittest.mock import Mock

import pytest
import requests_mock
from sqlalchemy.orm import Session
from tests.fixtures.messaging_fixtures import mailgun_post_body, mailgun_urls

from fides.api.common_exceptions import MessageDispatchException
from fides.api.models.application_config import ApplicationConfig
from fides.api.models.messaging import MessagingConfig
from fides.api.models.privacy_notice import (
    ConsentMechanism,
    EnforcementLevel,
    UserConsentPreference,
)
from fides.api.schemas.messaging.messaging import (
    AccessRequestCompleteBodyParams,
    ConsentEmailFulfillmentBodyParams,
    ConsentPreferencesByUser,
    EmailForActionType,
    FidesopsMessage,
    MessagingActionType,
    MessagingMethod,
    MessagingServiceDetails,
    MessagingServiceSecrets,
    MessagingServiceType,
    RequestReviewDenyBodyParams,
    SubjectIdentityVerificationBodyParams,
    UserInviteBodyParams,
)
from fides.api.schemas.privacy_notice import PrivacyNoticeHistorySchema
from fides.api.schemas.privacy_preference import MinimalPrivacyPreferenceHistorySchema
from fides.api.schemas.privacy_request import Consent
from fides.api.schemas.redis_cache import Identity
from fides.api.service.messaging.message_dispatch_service import (
    _PROVIDER_MAP,
    dispatch_message,
)
from fides.api.service.messaging.messaging_providers.base import (
    BaseEmailProviderService,
    BaseMessageProviderService,
)
from fides.api.service.messaging.messaging_providers.mailchimp_transactional_service import (
    MailchimpTransactionalService,
)
from fides.api.service.messaging.messaging_providers.mailgun_service import (
    MailgunService,
)
from fides.api.service.messaging.messaging_providers.twilio_email_service import (
    TwilioEmailService,
)
from fides.api.service.messaging.messaging_providers.twilio_sms_service import (
    TwilioSmsService,
)
from fides.config import CONFIG


@pytest.mark.unit
class TestMessageDispatchService:
    def test_email_dispatch_mailgun_success(
        self,
        db: Session,
        messaging_config,
        mock_mailgun_http,
    ) -> None:
        dispatch_message(
            db=db,
            action_type=MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
            to_identity=Identity(**{"email": "test@email.com"}),
            service_type=MessagingServiceType.mailgun.value,
            message_body_params=SubjectIdentityVerificationBodyParams(
                verification_code="2348", verification_code_ttl_seconds=600
            ),
        )
        assert mock_mailgun_http.called
        body = mailgun_post_body(mock_mailgun_http.request_history)
        assert body["to"] == ["test@email.com"]
        assert body["subject"] == ["Your one-time code is 2348"]

    """
    Test scenario:
    ✅︎ Property-specific messaging is enabled
    ❌ No template configured for action type

    Result: Email is not sent. An explicit messaging template with matching action type is needed to send emails for
    property-specific messaging
    """

    def test_email_dispatch_property_specific_templates_enabled_no_template(
        self,
        db: Session,
        messaging_config,
        mock_mailgun_http,
        set_property_specific_messaging_enabled,
    ) -> None:
        dispatch_message(
            db=db,
            action_type=MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
            to_identity=Identity(**{"email": "test@email.com"}),
            service_type=MessagingServiceType.mailgun.value,
            message_body_params=SubjectIdentityVerificationBodyParams(
                verification_code="2348", verification_code_ttl_seconds=600
            ),
            property_id=None,
        )
        assert not mock_mailgun_http.called

    """
    Test scenario:
    ❌ Property-specific messaging is disabled
    ✅︎ Has template configured for action type

    Result: Email sent the template configured with matching action type.
    """

    def test_email_dispatch_property_specific_templates_disabled_with_template(
        self,
        db: Session,
        messaging_config,
        mock_mailgun_http,
        messaging_template_no_property,
    ) -> None:
        dispatch_message(
            db=db,
            action_type=MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
            to_identity=Identity(**{"email": "test@email.com"}),
            service_type=MessagingServiceType.mailgun.value,
            message_body_params=SubjectIdentityVerificationBodyParams(
                verification_code="2348", verification_code_ttl_seconds=600
            ),
            property_id=None,
        )
        body = mailgun_post_body(mock_mailgun_http.request_history)
        assert body["to"] == ["test@email.com"]
        assert body["subject"] == ["Here is your code 2348"]

    """
    Test scenario:
    ❌ Property-specific messaging is disabled
    ❌ No template configured for action type

    Result: Email sent with default messaging template.
    """

    def test_email_dispatch_property_specific_templates_disabled_no_template(
        self,
        db: Session,
        messaging_config,
        mock_mailgun_http,
    ) -> None:
        dispatch_message(
            db=db,
            action_type=MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
            to_identity=Identity(**{"email": "test@email.com"}),
            service_type=MessagingServiceType.mailgun.value,
            message_body_params=SubjectIdentityVerificationBodyParams(
                verification_code="2348", verification_code_ttl_seconds=600
            ),
            property_id=None,
        )
        body = mailgun_post_body(mock_mailgun_http.request_history)
        assert body["to"] == ["test@email.com"]
        assert body["subject"] == ["Your one-time code is 2348"]

    """
    Test scenario:
    ✅︎ Property-specific messaging is enabled
    ✅︎ Has template configured for action type
    ❌ No property id attached to template
    ❌ No property id in request

    Result: Email not sent. There was no explicit property id linked to the template with matching action type.
    """

    def test_email_dispatch_property_specific_templates_enabled_with_template_no_property(
        self,
        db: Session,
        messaging_config,
        set_property_specific_messaging_enabled,
        messaging_template_no_property,
    ) -> None:
        dispatch_message(
            db=db,
            action_type=MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
            to_identity=Identity(**{"email": "test@email.com"}),
            service_type=MessagingServiceType.mailgun.value,
            message_body_params=SubjectIdentityVerificationBodyParams(
                verification_code="2348", verification_code_ttl_seconds=600
            ),
            property_id=None,
        )

    """
    Test scenario:
    ✅︎ Property-specific messaging is enabled
    ✅︎ Has template configured for action type
    ✅︎ Default property id attached to template
    ❌ No property id in request

    Result: Email sent using template linked to default property id. If no property id was received, we assume
    the default property id to look up the associated messaging template.
    """

    def test_email_dispatch_property_specific_templates_enabled_with_template_has_property(
        self,
        db: Session,
        messaging_config,
        mock_mailgun_http,
        set_property_specific_messaging_enabled,
        # The property created by the below fixture gets implicitly marked as the default as it's the first created
        messaging_template_subject_identity_verification,
    ) -> None:
        dispatch_message(
            db=db,
            action_type=MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
            to_identity=Identity(**{"email": "test@email.com"}),
            service_type=MessagingServiceType.mailgun.value,
            message_body_params=SubjectIdentityVerificationBodyParams(
                verification_code="2348", verification_code_ttl_seconds=600
            ),
            property_id=None,
        )
        body = mailgun_post_body(mock_mailgun_http.request_history)
        assert body["to"] == ["test@email.com"]
        # this text is built from the property-specific messaging template
        assert body["subject"] == ["Here is your code 2348"]

    """
    Test scenario:
    ✅︎ Property-specific messaging is enabled
    ✅︎ Has template configured for action type
    ❌ No property attached to template
    ✅ Default property id in request

    Result: Email not sent. There was no explicit property id linked to the template with matching action type.
    """

    def test_email_dispatch_property_specific_templates_enabled_with_template_no_property_default_request(
        self,
        db: Session,
        messaging_config,
        mock_mailgun_http,
        set_property_specific_messaging_enabled,
        messaging_template_no_property,
        property_a,
    ) -> None:
        dispatch_message(
            db=db,
            action_type=MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
            to_identity=Identity(**{"email": "test@email.com"}),
            service_type=MessagingServiceType.mailgun.value,
            message_body_params=SubjectIdentityVerificationBodyParams(
                verification_code="2348", verification_code_ttl_seconds=600
            ),
            property_id=property_a.id,
        )
        assert not mock_mailgun_http.called

    """
   Test scenario:
   ✅︎ Property-specific messaging is enabled
   ✅︎ Has template configured for action type
   ✅ Property attached to template
   ✅ Matching property id in request

   Result: Email sent using template with with property id
   """

    def test_email_dispatch_property_specific_templates_enabled_with_property_matching_template(
        self,
        db: Session,
        messaging_config,
        mock_mailgun_http,
        set_property_specific_messaging_enabled,
        property_a,
        messaging_template_subject_identity_verification,
    ) -> None:
        dispatch_message(
            db=db,
            action_type=MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
            to_identity=Identity(**{"email": "test@email.com"}),
            service_type=MessagingServiceType.mailgun.value,
            message_body_params=SubjectIdentityVerificationBodyParams(
                verification_code="2348", verification_code_ttl_seconds=600
            ),
            property_id=property_a.id,
        )
        body = mailgun_post_body(mock_mailgun_http.request_history)
        assert body["to"] == ["test@email.com"]
        # this text is built from the property-specific messaging template
        assert body["subject"] == ["Here is your code 2348"]

    def test_email_dispatch_mailgun_privacy_request_complete_access(
        self, db: Session, messaging_config, mock_mailgun_http
    ) -> None:
        download_link = "https://localhost"
        days = 5
        dispatch_message(
            db=db,
            action_type=MessagingActionType.PRIVACY_REQUEST_COMPLETE_ACCESS,
            to_identity=Identity(**{"email": "test@email.com"}),
            service_type=MessagingServiceType.mailgun.value,
            message_body_params=AccessRequestCompleteBodyParams(
                download_links=[download_link],
                subject_request_download_time_in_days=days,
            ),
        )
        body = mailgun_post_body(mock_mailgun_http.request_history)
        assert body["to"] == ["test@email.com"]
        assert body["subject"] == ["Your data is ready to be downloaded"]

    def test_email_dispatch_mailgun_privacy_request_complete_consent(
        self, db: Session, messaging_config, mock_mailgun_http
    ) -> None:
        dispatch_message(
            db=db,
            action_type=MessagingActionType.PRIVACY_REQUEST_COMPLETE_CONSENT,
            to_identity=Identity(**{"email": "test@email.com"}),
            service_type=MessagingServiceType.mailgun.value,
            message_body_params=None,
        )
        body = mailgun_post_body(mock_mailgun_http.request_history)
        assert body["to"] == ["test@email.com"]
        assert body["subject"] == ["Your consent preferences have been saved"]

    def test_email_dispatch_mailgun_privacy_request_review_deny(
        self, db: Session, messaging_config, mock_mailgun_http
    ) -> None:
        denial_reason = "Accounts with an unpaid balance cannot be deleted."
        dispatch_message(
            db=db,
            action_type=MessagingActionType.PRIVACY_REQUEST_REVIEW_DENY,
            to_identity=Identity(**{"email": "test@email.com"}),
            service_type=MessagingServiceType.mailgun.value,
            message_body_params=RequestReviewDenyBodyParams(
                rejection_reason=denial_reason
            ),
        )
        body = mailgun_post_body(mock_mailgun_http.request_history)
        assert body["to"] == ["test@email.com"]
        assert body["subject"] == ["Your privacy request has been denied"]

    def test_email_dispatch_mailgun_config_not_found(self, db: Session) -> None:
        with pytest.raises(MessageDispatchException) as exc:
            dispatch_message(
                db=db,
                action_type=MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
                to_identity=Identity(**{"email": "test@email.com"}),
                service_type=MessagingServiceType.mailgun.value,
                message_body_params=SubjectIdentityVerificationBodyParams(
                    verification_code="2348", verification_code_ttl_seconds=600
                ),
            )
        assert (
            exc.value.args[0] == "No messaging config found for service_type mailgun."
        )

    def test_email_dispatch_mailgun_config_no_secrets(self, db: Session) -> None:
        messaging_config = MessagingConfig.create(
            db=db,
            data={
                "name": "mailgun config",
                "key": "my_mailgun_messaging_config",
                "service_type": MessagingServiceType.mailgun,
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
                service_type=MessagingServiceType.mailgun.value,
                message_body_params=SubjectIdentityVerificationBodyParams(
                    verification_code="2348", verification_code_ttl_seconds=600
                ),
            )
        assert (
            exc.value.args[0]
            == "Messaging secrets not found for config with key: my_mailgun_messaging_config"
        )

        messaging_config.delete(db)

    def test_email_dispatch_mailgun_failed_email(
        self, db: Session, messaging_config
    ) -> None:
        template_url, send_url = mailgun_urls(messaging_config)
        with requests_mock.Mocker() as m:
            m.get(template_url, status_code=404)
            m.post(
                send_url,
                json={
                    "message": "Rejected: IP <id-address> can't be used to send the message",
                    "id": "<20111114174239.25659.5817@samples.mailgun.org>",
                },
                status_code=403,
            )
            with pytest.raises(MessageDispatchException) as exc:
                dispatch_message(
                    db=db,
                    action_type=MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
                    to_identity=Identity(**{"email": "test@email.com"}),
                    service_type=MessagingServiceType.mailgun.value,
                    message_body_params=SubjectIdentityVerificationBodyParams(
                        verification_code="2348", verification_code_ttl_seconds=600
                    ),
                )
            assert exc.value.args[0] == "Email failed to send with status code 403"

    def test_email_dispatch_mailgun_test_message(
        self, db, messaging_config, mock_mailgun_http
    ):
        dispatch_message(
            db=db,
            action_type=MessagingActionType.TEST_MESSAGE,
            to_identity=Identity(email="test@email.com"),
            service_type=MessagingServiceType.mailgun.value,
        )
        body = mailgun_post_body(mock_mailgun_http.request_history)
        assert body["to"] == ["test@email.com"]
        assert body["subject"] == ["Test message from fides"]

    @mock.patch(
        "fides.api.service.messaging.messaging_providers.twilio_email_service.sendgrid.SendGridAPIClient",
    )
    def test_email_dispatch_twilio_email_test_message(
        self, mock_sendgrid_cls, db, messaging_config_twilio_email
    ):
        mock_client = mock_sendgrid_cls.return_value
        mock_client.client.templates.get.return_value = Mock(body=b'{"result": []}')
        mock_client.client.mail.send.post.return_value = Mock(status_code=202)
        dispatch_message(
            db=db,
            action_type=MessagingActionType.TEST_MESSAGE,
            to_identity=Identity(email="test@email.com"),
            service_type=MessagingServiceType.twilio_email.value,
        )
        mock_client.client.mail.send.post.assert_called_once()

    @mock.patch(
        "fides.api.service.messaging.messaging_providers.twilio_sms_service.Client",
        autospec=True,
    )
    def test_email_dispatch_twilio_sms_test_message(
        self, mock_twilio_client_cls, db, messaging_config_twilio_sms
    ):
        dispatch_message(
            db=db,
            action_type=MessagingActionType.TEST_MESSAGE,
            to_identity=Identity(phone_number="+19198675309"),
            service_type=MessagingServiceType.twilio_text.value,
        )
        mock_client = mock_twilio_client_cls.return_value
        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["to"] == "+19198675309"

    def test_email_dispatch_aws_ses_email_test_message(
        self, db, messaging_config_aws_ses
    ):

        mock_aws_ses_cls = Mock()
        mock_aws_ses_cls.return_value = Mock(spec=BaseEmailProviderService)
        with mock.patch.dict(
            _PROVIDER_MAP, {MessagingServiceType.aws_ses: mock_aws_ses_cls}
        ):
            dispatch_message(
                db=db,
                action_type=MessagingActionType.TEST_MESSAGE,
                to_identity=Identity(email="test@email.com"),
                service_type=MessagingServiceType.aws_ses.value,
            )
        body = '<!DOCTYPE html>\n<html lang="en">\n  <head>\n    <meta charset="UTF-8" />\n    <title>Fides Test message</title>\n  </head>\n  <body>\n    <main>\n      <p>This is a test message from Fides.</p>\n    </main>\n  </body>\n</html>'
        mock_aws_ses_cls.assert_called_once_with(messaging_config_aws_ses)
        call_args = mock_aws_ses_cls.return_value.send_email.call_args
        assert call_args[0][0] == "test@email.com"
        assert call_args[0][1].subject == "Test message from fides"
        assert call_args[0][1].body == body

    def test_email_dispatch_aws_ses_email_raises_exception(
        self, db, messaging_config_aws_ses
    ):

        mock_aws_ses_cls = Mock()
        mock_instance = Mock(spec=BaseEmailProviderService)
        mock_instance.send_email.side_effect = MessageDispatchException(
            "AWS SES email failed to send due to: Oops! Something went wrong"
        )
        mock_aws_ses_cls.return_value = mock_instance
        with mock.patch.dict(
            _PROVIDER_MAP, {MessagingServiceType.aws_ses: mock_aws_ses_cls}
        ):
            with pytest.raises(MessageDispatchException) as exc:
                dispatch_message(
                    db=db,
                    action_type=MessagingActionType.TEST_MESSAGE,
                    to_identity=Identity(email="test@email.com"),
                    service_type=MessagingServiceType.aws_ses.value,
                )

        body = '<!DOCTYPE html>\n<html lang="en">\n  <head>\n    <meta charset="UTF-8" />\n    <title>Fides Test message</title>\n  </head>\n  <body>\n    <main>\n      <p>This is a test message from Fides.</p>\n    </main>\n  </body>\n</html>'
        mock_aws_ses_cls.assert_called_once_with(messaging_config_aws_ses)
        call_args = mock_instance.send_email.call_args
        assert call_args[0][0] == "test@email.com"
        assert call_args[0][1].subject == "Test message from fides"
        assert call_args[0][1].body == body

        assert "AWS SES email failed to send due to: Oops! Something went wrong" in str(
            exc.value
        )

    def test_fidesops_email_model_validateect(self):
        FidesopsMessage.model_validate(
            {
                "action_type": MessagingActionType.MESSAGE_ERASURE_REQUEST_FULFILLMENT,
                "body_params": {
                    "controller": "Test Organization",
                    "third_party_vendor_name": "System",
                    "identities": ["test@example.com"],
                },
            }
        )

        FidesopsMessage.model_validate(
            {
                "action_type": MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
                "body_params": {
                    "verification_code": "123456",
                    "verification_code_ttl_seconds": 1000,
                },
            }
        )

    @mock.patch(
        "fides.api.service.messaging.messaging_providers.twilio_sms_service.Client",
        autospec=True,
    )
    def test_sms_dispatch_twilio_success(
        self, mock_twilio_client_cls: Mock, db: Session, messaging_config_twilio_sms
    ) -> None:
        dispatch_message(
            db=db,
            action_type=MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
            to_identity=Identity(**{"phone_number": "+12312341231"}),
            service_type=MessagingServiceType.twilio_text.value,
            message_body_params=SubjectIdentityVerificationBodyParams(
                verification_code="2348", verification_code_ttl_seconds=600
            ),
        )
        mock_client = mock_twilio_client_cls.return_value
        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["to"] == "+12312341231"
        assert "2348" in call_kwargs["body"]

    def test_sms_dispatch_twilio_no_to(self, db, messaging_config_twilio_sms):
        with pytest.raises(MessageDispatchException) as err:
            dispatch_message(
                db=db,
                action_type=MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
                to_identity=Identity(phone_number=None),
                service_type=MessagingServiceType.twilio_text.value,
                message_body_params=SubjectIdentityVerificationBodyParams(
                    verification_code="2348", verification_code_ttl_seconds=600
                ),
            )

        assert "No phone identity supplied." in str(err.value)

    def test_sms_dispatch_twilio_config_not_found(self, db: Session) -> None:
        with pytest.raises(MessageDispatchException) as exc:
            dispatch_message(
                db=db,
                action_type=MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
                to_identity=Identity(**{"phone_number": "+12312341231"}),
                service_type=MessagingServiceType.twilio_text.value,
                message_body_params=SubjectIdentityVerificationBodyParams(
                    verification_code="2348", verification_code_ttl_seconds=600
                ),
            )
        assert (
            exc.value.args[0]
            == "No messaging config found for service_type twilio_text."
        )

    def test_sms_dispatch_twilio_config_no_secrets(self, db: Session) -> None:
        messaging_config = MessagingConfig.create(
            db=db,
            data={
                "name": "twilio sms config",
                "key": "my_twilio_sms_config",
                "service_type": MessagingServiceType.twilio_text.value,
            },
        )

        with pytest.raises(MessageDispatchException) as exc:
            dispatch_message(
                db=db,
                action_type=MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
                to_identity=Identity(**{"phone_number": "+12312341231"}),
                service_type=MessagingServiceType.twilio_text.value,
                message_body_params=SubjectIdentityVerificationBodyParams(
                    verification_code="2348", verification_code_ttl_seconds=600
                ),
            )
        assert (
            exc.value.args[0]
            == "Messaging secrets not found for config with key: my_twilio_sms_config"
        )

        messaging_config.delete(db)

    def test_dispatch_no_identity(self, db: Session) -> None:
        with pytest.raises(MessageDispatchException) as exc:
            dispatch_message(
                db=db,
                action_type=MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
                to_identity=None,
                service_type=MessagingServiceType.twilio_text.value,
                message_body_params=SubjectIdentityVerificationBodyParams(
                    verification_code="2348", verification_code_ttl_seconds=600
                ),
            )

        assert "No identity supplied" in exc.value.args[0]

    def test_email_dispatch_mailgun_no_identity_for_type(
        self,
        db: Session,
        messaging_config,
    ) -> None:
        with pytest.raises(MessageDispatchException) as err:
            dispatch_message(
                db=db,
                action_type=MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
                to_identity=Identity(
                    **{"phone_number": "+12312341231"}
                ),  # Identity only has phone number
                service_type=MessagingServiceType.mailgun.value,
                message_body_params=SubjectIdentityVerificationBodyParams(
                    verification_code="2348", verification_code_ttl_seconds=600
                ),
            )

        assert "No email identity supplied." in str(err.value)

    def test_email_dispatch_twilio_sms_no_identity_for_type(
        self,
        db: Session,
        messaging_config_twilio_sms,
    ) -> None:
        with pytest.raises(MessageDispatchException) as err:
            dispatch_message(
                db=db,
                action_type=MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
                to_identity=Identity(
                    **{"email": "test@test.com"}
                ),  # Identity only has email
                service_type=MessagingServiceType.twilio_text.value,
                message_body_params=SubjectIdentityVerificationBodyParams(
                    verification_code="2348", verification_code_ttl_seconds=600
                ),
            )

        assert "No phone identity supplied." in str(err.value)

    def test_email_dispatch_twilio_email_no_identity_for_type(
        self,
        db: Session,
        messaging_config_twilio_email,
    ) -> None:
        with pytest.raises(MessageDispatchException) as err:
            dispatch_message(
                db=db,
                action_type=MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
                to_identity=Identity(
                    **{"phone_number": "+12312341231"}
                ),  # Identity only has phone
                service_type=MessagingServiceType.twilio_email.value,
                message_body_params=SubjectIdentityVerificationBodyParams(
                    verification_code="2348", verification_code_ttl_seconds=600
                ),
            )

        assert "No email identity supplied." in str(err.value)

    @mock.patch(
        "fides.api.service.messaging.message_dispatch_service.AwsSesService",
        autospec=True,
    )
    def test_email_dispatch_aws_ses_no_identity_for_type(
        self,
        mock_aws_ses_cls: Mock,
        db: Session,
        messaging_config_aws_ses,
    ) -> None:
        with pytest.raises(MessageDispatchException) as err:
            dispatch_message(
                db=db,
                action_type=MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
                to_identity=Identity(
                    **{"phone_number": "+12312341231"}
                ),  # Identity only has phone
                service_type=MessagingServiceType.aws_ses.value,
                message_body_params=SubjectIdentityVerificationBodyParams(
                    verification_code="2348", verification_code_ttl_seconds=600
                ),
            )

        assert "No email identity supplied." in str(err.value)
        mock_aws_ses_cls.return_value.send_email.assert_not_called()

    def test_dispatch_no_service_type(self, db: Session) -> None:
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

    def test_dispatch_invalid_action_type(self, db):
        with pytest.raises(MessageDispatchException):
            dispatch_message(db, "bad", to_identity=None, service_type=None)

    def test_email_dispatch_consent_request_email_fulfillment_for_sovrn_old_workflow(
        self, db: Session, messaging_config, mock_mailgun_http
    ) -> None:
        dispatch_message(
            db=db,
            action_type=MessagingActionType.CONSENT_REQUEST_EMAIL_FULFILLMENT,
            to_identity=Identity(**{"email": "sovrn_test@example.com"}),
            service_type=MessagingServiceType.mailgun.value,
            message_body_params=ConsentEmailFulfillmentBodyParams(
                controller="Test Organization",
                third_party_vendor_name="Sovrn",
                required_identities=["ljt_readerID"],
                requested_changes=[
                    ConsentPreferencesByUser(
                        identities={"ljt_readerID": "test_user_id"},
                        consent_preferences=[
                            Consent(data_use="marketing.advertising", opt_in=False),
                            Consent(
                                data_use="marketing.advertising.first_party",
                                opt_in=True,
                            ),
                        ],
                        privacy_preferences=[],
                    )
                ],
            ),
        )
        body = mailgun_post_body(mock_mailgun_http.request_history)
        assert body["to"] == ["sovrn_test@example.com"]
        assert body["subject"] == ["Notification of users' consent preference changes"]

    def test_email_dispatch_consent_request_email_fulfillment_for_sovrn_new_workflow(
        self, db: Session, messaging_config, mock_mailgun_http
    ) -> None:
        dispatch_message(
            db=db,
            action_type=MessagingActionType.CONSENT_REQUEST_EMAIL_FULFILLMENT,
            to_identity=Identity(**{"email": "sovrn_test@example.com"}),
            service_type=MessagingServiceType.mailgun.value,
            message_body_params=ConsentEmailFulfillmentBodyParams(
                controller="Test Organization",
                third_party_vendor_name="Sovrn",
                required_identities=["ljt_readerID"],
                requested_changes=[
                    ConsentPreferencesByUser(
                        identities={"ljt_readerID": "test_user_id"},
                        consent_preferences=[],
                        privacy_preferences=[
                            MinimalPrivacyPreferenceHistorySchema(
                                id="test_privacy_preference_3",
                                preference=UserConsentPreference.opt_out,
                                privacy_notice_history=PrivacyNoticeHistorySchema(
                                    name="Analytics",
                                    notice_key="analytics",
                                    id="test_3",
                                    translation_id="39391",
                                    consent_mechanism=ConsentMechanism.opt_in,
                                    data_uses=["functional.service.improve"],
                                    enforcement_level=EnforcementLevel.system_wide,
                                    version=1.0,
                                ),
                            )
                        ],
                    )
                ],
            ),
        )
        body = mailgun_post_body(mock_mailgun_http.request_history)
        assert body["to"] == ["sovrn_test@example.com"]
        assert body["subject"] == ["Notification of users' consent preference changes"]

    @pytest.fixture
    def mock_config_admin_ui_url(self, db):
        original_value = CONFIG.admin_ui.url
        CONFIG.admin_ui.url = "http://localhost:3000"
        ApplicationConfig.update_config_set(db, CONFIG)
        yield
        CONFIG.admin_ui.url = original_value
        ApplicationConfig.update_config_set(db, CONFIG)

    @pytest.mark.usefixtures("mock_config_admin_ui_url")
    def test_email_dispatch_user_invite_email(
        self,
        db: Session,
        messaging_config,
        mock_mailgun_http,
    ) -> None:
        dispatch_message(
            db=db,
            action_type=MessagingActionType.USER_INVITE,
            to_identity=Identity(**{"email": "test@example.com"}),
            service_type=MessagingServiceType.mailgun.value,
            message_body_params=UserInviteBodyParams(
                username="test", invite_code="123"
            ),
        )
        body = mailgun_post_body(mock_mailgun_http.request_history)
        assert body["to"] == ["test@example.com"]
        assert body["subject"] == ["Welcome to Fides"]


class TestMailgunServiceErrors:
    def test_send_email_generic_exception(self, messaging_config):
        from fides.api.service.messaging.messaging_providers.mailgun_service import (
            MailgunService,
        )

        service = MailgunService(messaging_config)
        with requests_mock.Mocker() as m:
            m.get(requests_mock.ANY, exc=ConnectionError("DNS resolution failed"))
            with pytest.raises(MessageDispatchException, match="DNS resolution failed"):
                service.send_email(
                    "test@email.com",
                    EmailForActionType(subject="Test", body="body"),
                )


class TestInitGuard:
    def test_missing_provider_name_raises_type_error(self, messaging_config):
        class BadProvider(BaseMessageProviderService):
            def validate_config(self) -> None:
                pass

        with pytest.raises(TypeError, match="must define 'provider_name'"):
            BadProvider(messaging_config)


class TestProviderConfigValidation:
    """Tests that providers raise MessageDispatchException (not KeyError) for
    configs with wrong keys."""

    @pytest.mark.parametrize(
        "fixture_name,provider_cls,field,match",
        [
            ("messaging_config", MailgunService, "details", "missing required detail"),
            (
                "messaging_config_mailchimp_transactional",
                MailchimpTransactionalService,
                "secrets",
                "missing required secret",
            ),
            (
                "messaging_config_twilio_sms",
                TwilioSmsService,
                "secrets",
                "missing required secret",
            ),
            (
                "messaging_config_twilio_email",
                TwilioEmailService,
                "details",
                "missing required detail",
            ),
        ],
        ids=[
            "mailgun-detail",
            "mailchimp-secret",
            "twilio_sms-secret",
            "twilio_email-detail",
        ],
    )
    def test_wrong_config_keys_raise_dispatch_exception(
        self, fixture_name, provider_cls, field, match, request
    ):
        config = request.getfixturevalue(fixture_name)
        setattr(config, field, {"wrong_key": "value"})
        with pytest.raises(MessageDispatchException, match=match):
            provider_cls(config)


_DISPATCH_MODULE = "fides.api.service.messaging.message_dispatch_service"


class TestDispatchGuards:
    """Tests for defensive guards in the provider dispatch path."""

    def test_unknown_service_type_raises(self, db: Session, messaging_config):
        """Provider map guard rejects an unmapped service type."""
        with mock.patch(f"{_DISPATCH_MODULE}._PROVIDER_MAP", {}):
            with pytest.raises(
                MessageDispatchException,
                match="Dispatcher has not been implemented",
            ):
                dispatch_message(
                    db=db,
                    action_type=MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
                    to_identity=Identity(email="test@email.com"),
                    service_type=MessagingServiceType.mailgun.value,
                    message_body_params=SubjectIdentityVerificationBodyParams(
                        verification_code="2348", verification_code_ttl_seconds=600
                    ),
                )

    def test_email_provider_rejects_str_body(self, db: Session, messaging_config):
        """Email provider guard rejects a str message body."""
        with mock.patch(f"{_DISPATCH_MODULE}._build_email", return_value="plain text"):
            with pytest.raises(
                MessageDispatchException,
                match="Expected EmailForActionType for email provider",
            ):
                dispatch_message(
                    db=db,
                    action_type=MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
                    to_identity=Identity(email="test@email.com"),
                    service_type=MessagingServiceType.mailgun.value,
                    message_body_params=SubjectIdentityVerificationBodyParams(
                        verification_code="2348", verification_code_ttl_seconds=600
                    ),
                )

    @mock.patch(
        "fides.api.service.messaging.messaging_providers.twilio_sms_service.Client",
        autospec=True,
    )
    def test_sms_provider_rejects_email_body(
        self, mock_twilio_client_cls, db: Session, messaging_config_twilio_sms
    ):
        """SMS provider guard rejects an EmailForActionType message body."""
        with mock.patch(
            f"{_DISPATCH_MODULE}._build_sms",
            return_value=EmailForActionType(subject="oops", body="wrong type"),
        ):
            with pytest.raises(
                MessageDispatchException, match="Expected str body for SMS provider"
            ):
                dispatch_message(
                    db=db,
                    action_type=MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
                    to_identity=Identity(phone_number="+15551234567"),
                    service_type=MessagingServiceType.twilio_text.value,
                    message_body_params=SubjectIdentityVerificationBodyParams(
                        verification_code="2348", verification_code_ttl_seconds=600
                    ),
                )


class TestSubjectOverride:
    def test_subject_override_for_email(
        self, db: Session, messaging_config, mock_mailgun_http
    ) -> None:
        dispatch_message(
            db=db,
            action_type=MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
            to_identity=Identity(**{"email": "test@email.com"}),
            service_type=MessagingServiceType.mailgun.value,
            message_body_params=SubjectIdentityVerificationBodyParams(
                verification_code="2348", verification_code_ttl_seconds=600
            ),
            subject_override="Testing subject override",
        )
        body = mailgun_post_body(mock_mailgun_http.request_history)
        assert body["to"] == ["test@email.com"]
        assert body["subject"] == ["Testing subject override"]

    @mock.patch(
        "fides.api.service.messaging.messaging_providers.twilio_sms_service.Client",
        autospec=True,
    )
    def test_sms_subject_override_ignored(
        self, mock_twilio_client_cls: Mock, db: Session, messaging_config_twilio_sms
    ) -> None:
        dispatch_message(
            db=db,
            action_type=MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
            to_identity=Identity(**{"phone_number": "+12312341231"}),
            service_type=MessagingServiceType.twilio_text.value,
            message_body_params=SubjectIdentityVerificationBodyParams(
                verification_code="2348", verification_code_ttl_seconds=600
            ),
            subject_override="override subject",
        )
        mock_client = mock_twilio_client_cls.return_value
        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["to"] == "+12312341231"
        assert "2348" in call_kwargs["body"]
