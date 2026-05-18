from unittest import mock
from unittest.mock import Mock

import pytest
from sendgrid.helpers.mail import Email, To

from fides.api.common_exceptions import MessageDispatchException
from fides.api.schemas.messaging.messaging import EmailForActionType
from fides.api.service.messaging.messaging_providers.twilio_email_service import (
    EMAIL_TEMPLATE_NAME,
    TwilioEmailService,
)


@pytest.fixture
def test_template_response_body():
    yield {
        "result": [
            {
                "id": "d-0507bb6d47cb46f38761f541b9cb8507",
                "name": "fides",
                "generation": "dynamic",
                "updated_at": "2023-02-28 00:43:28",
                "versions": [
                    {
                        "id": "2080ab46-ebd2-40fa-b595-01d3e94e2700",
                        "template_id": "d-0507bb6d47cb46f38761f541b9cb8507",
                        "active": 1,
                        "name": "fides",
                        "generate_plain_content": False,
                        "subject": "DSR Testing",
                        "updated_at": "2023-03-01 13:34:23",
                        "editor": "design",
                    }
                ],
            },
        ]
    }


@pytest.fixture
def test_message_body():
    yield "This is a test DSR message body"


@pytest.mark.unit
class TestTwilioEmailProvider:
    def test_dispatch_no_secrets(self, messaging_config_twilio_email):
        messaging_config_twilio_email.secrets = None
        with pytest.raises(MessageDispatchException) as exc:
            TwilioEmailService(messaging_config_twilio_email)

        assert "No Twilio email config details or secrets" in str(exc.value)

    def test_template_found(self, test_template_response_body):
        template_test = TwilioEmailService._get_template_id_if_exists(
            test_template_response_body, EMAIL_TEMPLATE_NAME
        )
        assert template_test

    def test_no_template_found(self, test_template_response_body):
        template_test = TwilioEmailService._get_template_id_if_exists(
            test_template_response_body, f"not_{EMAIL_TEMPLATE_NAME}"
        )
        assert template_test is None

    def test_templated_mail(self, test_message_body):
        mail = TwilioEmailService._compose_mail(
            Email("test@test.com"),
            To("test@test.com"),
            "Test DSR EMail",
            test_message_body,
            "test_template",
        )
        assert "template_id" in mail.get()

    def test_non_templated_mail(self, test_message_body):
        mail = TwilioEmailService._compose_mail(
            Email("test@test.com"),
            To("test@test.com"),
            "Test DSR EMail",
            test_message_body,
            template_id=None,
        )
        assert "template_id" not in mail.get()

    @mock.patch(
        "fides.api.service.messaging.messaging_providers.twilio_email_service.sendgrid.SendGridAPIClient",
    )
    def test_send_email_no_template(
        self, mock_sendgrid_cls, messaging_config_twilio_email
    ):
        mock_client = mock_sendgrid_cls.return_value
        mock_client.client.templates.get.return_value = Mock(body=b'{"result": []}')
        mock_client.client.mail.send.post.return_value = Mock(status_code=202)

        service = TwilioEmailService(messaging_config_twilio_email)
        service.send_email(
            "test@email.com",
            EmailForActionType(subject="Test subject", body="<p>Hello</p>"),
        )
        mock_client.client.mail.send.post.assert_called_once()
        mail_body = mock_client.client.mail.send.post.call_args[1]["request_body"]
        assert mail_body["subject"] == "Test subject"
        assert "template_id" not in mail_body

    @mock.patch(
        "fides.api.service.messaging.messaging_providers.twilio_email_service.sendgrid.SendGridAPIClient",
    )
    def test_send_email_with_template(
        self, mock_sendgrid_cls, messaging_config_twilio_email
    ):
        mock_client = mock_sendgrid_cls.return_value
        mock_client.client.templates.get.return_value = Mock(
            body=b'{"result": [{"name": "fides", "id": "tmpl_123"}]}'
        )
        mock_client.client.mail.send.post.return_value = Mock(status_code=202)

        service = TwilioEmailService(messaging_config_twilio_email)
        service.send_email(
            "test@email.com",
            EmailForActionType(subject="Test subject", body="<p>Hello</p>"),
        )
        mock_client.client.mail.send.post.assert_called_once()
        mail_body = mock_client.client.mail.send.post.call_args[1]["request_body"]
        assert mail_body["template_id"] == "tmpl_123"

    @mock.patch(
        "fides.api.service.messaging.messaging_providers.twilio_email_service.sendgrid.SendGridAPIClient",
    )
    def test_send_email_failure(self, mock_sendgrid_cls, messaging_config_twilio_email):
        mock_client = mock_sendgrid_cls.return_value
        mock_client.client.templates.get.return_value = Mock(body=b'{"result": []}')
        mock_client.client.mail.send.post.return_value = Mock(
            status_code=403, body=b"Forbidden"
        )

        service = TwilioEmailService(messaging_config_twilio_email)
        with pytest.raises(MessageDispatchException, match="Email failed to send"):
            service.send_email(
                "test@email.com",
                EmailForActionType(subject="Test", body="body"),
            )

    @mock.patch(
        "fides.api.service.messaging.messaging_providers.twilio_email_service.sendgrid.SendGridAPIClient",
    )
    def test_send_email_generic_exception(
        self, mock_sendgrid_cls, messaging_config_twilio_email
    ):
        mock_client = mock_sendgrid_cls.return_value
        mock_client.client.templates.get.side_effect = ConnectionError(
            "Connection refused"
        )

        service = TwilioEmailService(messaging_config_twilio_email)
        with pytest.raises(MessageDispatchException, match="Connection refused"):
            service.send_email(
                "test@email.com",
                EmailForActionType(subject="Test", body="body"),
            )
