import json

import pytest
import requests_mock

from fides.api.common_exceptions import MessageDispatchException
from fides.api.schemas.messaging.messaging import EmailForActionType
from fides.api.service.messaging.messaging_providers.mailchimp_transactional_service import (
    MailchimpTransactionalService,
)


@pytest.mark.unit
class TestMailchimpTransactionalProvider:
    def test_send_email_success(self, messaging_config_mailchimp_transactional):
        service = MailchimpTransactionalService(
            messaging_config_mailchimp_transactional
        )
        with requests_mock.Mocker() as m:
            m.post(
                "https://mandrillapp.com/api/1.0/messages/send",
                json=[{"status": "sent", "email": "test@email.com"}],
                status_code=200,
            )
            service.send_email(
                "test@email.com",
                EmailForActionType(subject="Test subject", body="<p>Hello</p>"),
            )
            assert m.called
            sent_data = json.loads(m.last_request.text)
            assert sent_data["message"]["to"] == [
                {"email": "test@email.com", "type": "to"}
            ]
            assert sent_data["message"]["subject"] == "Test subject"
            assert sent_data["message"]["html"] == "<p>Hello</p>"

    def test_send_email_http_failure(self, messaging_config_mailchimp_transactional):
        service = MailchimpTransactionalService(
            messaging_config_mailchimp_transactional
        )
        with requests_mock.Mocker() as m:
            m.post(
                "https://mandrillapp.com/api/1.0/messages/send",
                json={"status": "error", "message": "Invalid API key"},
                status_code=500,
            )
            with pytest.raises(MessageDispatchException, match="status code 500"):
                service.send_email(
                    "test@email.com",
                    EmailForActionType(subject="Test", body="body"),
                )

    def test_send_email_rejected(self, messaging_config_mailchimp_transactional):
        service = MailchimpTransactionalService(
            messaging_config_mailchimp_transactional
        )
        with requests_mock.Mocker() as m:
            m.post(
                "https://mandrillapp.com/api/1.0/messages/send",
                json=[{"status": "rejected", "reject_reason": "hard-bounce"}],
                status_code=200,
            )
            with pytest.raises(MessageDispatchException, match="hard-bounce"):
                service.send_email(
                    "test@email.com",
                    EmailForActionType(subject="Test", body="body"),
                )

    def test_send_email_empty_response(self, messaging_config_mailchimp_transactional):
        service = MailchimpTransactionalService(
            messaging_config_mailchimp_transactional
        )
        with requests_mock.Mocker() as m:
            m.post(
                "https://mandrillapp.com/api/1.0/messages/send",
                json=[],
                status_code=200,
            )
            with pytest.raises(
                MessageDispatchException, match="Unexpected empty response"
            ):
                service.send_email(
                    "test@email.com",
                    EmailForActionType(subject="Test", body="body"),
                )

    def test_dispatch_no_secrets(self, messaging_config_mailchimp_transactional):
        messaging_config_mailchimp_transactional.secrets = None
        with pytest.raises(MessageDispatchException, match="details or secrets"):
            MailchimpTransactionalService(messaging_config_mailchimp_transactional)
