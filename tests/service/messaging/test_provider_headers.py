"""Per-provider threading header mapping tests.

Tests that each email provider correctly maps EmailForActionType threading
fields to provider-specific API payloads, and omits them when None.
"""

import json
from email import policy
from email.parser import BytesParser
from unittest import mock
from unittest.mock import MagicMock, Mock, patch

import pytest

from fides.api.common_exceptions import MessageDispatchException
from fides.api.schemas.messaging.messaging import EmailForActionType
from fides.api.service.messaging.messaging_providers.aws_ses_service import (
    AwsSesService,
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


def _make_messaging_config(service_type, details=None, secrets=None):
    """Create a minimal mock MessagingConfig for provider tests."""
    config = MagicMock()
    config.service_type = service_type
    config.details = details or {}
    config.secrets = secrets or {}
    return config


def _email_with_headers(**overrides):
    """Create an EmailForActionType with all threading fields set."""
    defaults = {
        "subject": "Test Subject",
        "body": "<p>Test body</p>",
        "reply_to": "reply+token123@replies.example.com",
        "message_id": "<msg-001@example.com>",
        "in_reply_to": "<msg-000@example.com>",
        "references": "<msg-000@example.com>",
        "body_text": "Test body plaintext",
    }
    defaults.update(overrides)
    return EmailForActionType(**defaults)


def _email_without_headers():
    """Create an EmailForActionType with no threading fields."""
    return EmailForActionType(subject="Test Subject", body="<p>Test body</p>")


class TestMailgunHeaders:
    @pytest.fixture()
    def mailgun_service(self):
        config = _make_messaging_config(
            "mailgun",
            details={
                "domain": "example.com",
                "is_eu_domain": False,
                "api_version": "v3",
            },
            secrets={"mailgun_api_key": "test-key"},
        )
        return MailgunService(config)

    @patch("fides.api.service.messaging.messaging_providers.mailgun_service.requests")
    def test_headers_included_when_set(self, mock_requests, mailgun_service):
        mock_requests.get.return_value = Mock(status_code=404)
        mock_requests.post.return_value = Mock(ok=True)

        mailgun_service.send_email("to@test.com", _email_with_headers())

        call_kwargs = mock_requests.post.call_args
        data = call_kwargs.kwargs.get("data") or call_kwargs[1].get("data")

        assert data["h:Reply-To"] == "reply+token123@replies.example.com"
        assert data["h:Message-ID"] == "<msg-001@example.com>"
        assert data["h:In-Reply-To"] == "<msg-000@example.com>"
        assert data["h:References"] == "<msg-000@example.com>"
        assert data["text"] == "Test body plaintext"

    @patch("fides.api.service.messaging.messaging_providers.mailgun_service.requests")
    def test_headers_omitted_when_none(self, mock_requests, mailgun_service):
        mock_requests.get.return_value = Mock(status_code=404)
        mock_requests.post.return_value = Mock(ok=True)

        mailgun_service.send_email("to@test.com", _email_without_headers())

        call_kwargs = mock_requests.post.call_args
        data = call_kwargs.kwargs.get("data") or call_kwargs[1].get("data")

        assert "h:Reply-To" not in data
        assert "h:Message-ID" not in data
        assert "h:In-Reply-To" not in data
        assert "h:References" not in data
        assert "text" not in data


class TestTwilioEmailHeaders:
    @pytest.fixture()
    def twilio_email_service(self):
        config = _make_messaging_config(
            "twilio_email",
            details={"twilio_email_from": "from@test.com"},
            secrets={"twilio_api_key": "test-key"},
        )
        return TwilioEmailService(config)

    @patch(
        "fides.api.service.messaging.messaging_providers.twilio_email_service.sendgrid"
    )
    def test_headers_included_when_set(self, mock_sendgrid, twilio_email_service):
        mock_sg = MagicMock()
        mock_sendgrid.SendGridAPIClient.return_value = mock_sg
        mock_sg.client.templates.get.return_value = Mock(
            body=json.dumps({"result": []}).encode()
        )
        mock_sg.client.mail.send.post.return_value = Mock(status_code=200)

        twilio_email_service.send_email("to@test.com", _email_with_headers())

        call_kwargs = mock_sg.client.mail.send.post.call_args
        request_body = call_kwargs.kwargs.get("request_body") or call_kwargs[1].get(
            "request_body"
        )

        # SendGrid Mail.get() returns a dict with headers and content
        assert request_body is not None
        # Check reply_to is set
        assert "reply_to" in request_body
        assert request_body["reply_to"]["email"] == "reply+token123@replies.example.com"
        # Check headers
        headers = request_body.get("headers", {})
        assert headers.get("Message-ID") == "<msg-001@example.com>"
        assert headers.get("In-Reply-To") == "<msg-000@example.com>"
        assert headers.get("References") == "<msg-000@example.com>"
        # Check plaintext content
        content_types = [c["type"] for c in request_body.get("content", [])]
        assert "text/plain" in content_types

    @patch(
        "fides.api.service.messaging.messaging_providers.twilio_email_service.sendgrid"
    )
    def test_headers_omitted_when_none(self, mock_sendgrid, twilio_email_service):
        mock_sg = MagicMock()
        mock_sendgrid.SendGridAPIClient.return_value = mock_sg
        mock_sg.client.templates.get.return_value = Mock(
            body=json.dumps({"result": []}).encode()
        )
        mock_sg.client.mail.send.post.return_value = Mock(status_code=200)

        twilio_email_service.send_email("to@test.com", _email_without_headers())

        call_kwargs = mock_sg.client.mail.send.post.call_args
        request_body = call_kwargs.kwargs.get("request_body") or call_kwargs[1].get(
            "request_body"
        )

        assert "reply_to" not in request_body
        assert "headers" not in request_body or request_body["headers"] == {}
        content_types = [c["type"] for c in request_body.get("content", [])]
        assert "text/plain" not in content_types


class TestMailchimpTransactionalHeaders:
    @pytest.fixture()
    def mailchimp_service(self):
        config = _make_messaging_config(
            "mailchimp_transactional",
            details={"email_from": "from@test.com"},
            secrets={"mailchimp_transactional_api_key": "test-key"},
        )
        return MailchimpTransactionalService(config)

    @patch(
        "fides.api.service.messaging.messaging_providers.mailchimp_transactional_service.requests"
    )
    def test_headers_included_when_set(self, mock_requests, mailchimp_service):
        mock_requests.post.return_value = Mock(
            ok=True, json=lambda: [{"status": "sent"}]
        )

        mailchimp_service.send_email("to@test.com", _email_with_headers())

        call_kwargs = mock_requests.post.call_args
        payload = json.loads(
            call_kwargs.kwargs.get("data") or call_kwargs[1].get("data")
        )
        msg = payload["message"]

        assert msg["reply_to"] == "reply+token123@replies.example.com"
        assert "Reply-To" not in msg.get("headers", {})
        assert msg["headers"]["Message-ID"] == "<msg-001@example.com>"
        assert msg["headers"]["In-Reply-To"] == "<msg-000@example.com>"
        assert msg["headers"]["References"] == "<msg-000@example.com>"
        assert msg["text"] == "Test body plaintext"

    @patch(
        "fides.api.service.messaging.messaging_providers.mailchimp_transactional_service.requests"
    )
    def test_headers_omitted_when_none(self, mock_requests, mailchimp_service):
        mock_requests.post.return_value = Mock(
            ok=True, json=lambda: [{"status": "sent"}]
        )

        mailchimp_service.send_email("to@test.com", _email_without_headers())

        call_kwargs = mock_requests.post.call_args
        payload = json.loads(
            call_kwargs.kwargs.get("data") or call_kwargs[1].get("data")
        )
        msg = payload["message"]

        assert "headers" not in msg or msg["headers"] == {}
        assert "text" not in msg


class TestAwsSesHeaders:
    """Tests for SES send_raw_email MIME construction with threading headers."""

    @pytest.fixture()
    def ses_service(self):
        config = _make_messaging_config(
            "aws_ses",
            details={
                "aws_region": "us-east-1",
                "email_from": "test@example.com",
                "domain": "example.com",
            },
            secrets={
                "aws_access_key_id": "fake",
                "aws_secret_access_key": "fake",
                "auth_method": "secret_keys",
            },
        )
        service = AwsSesService(config)
        service._ses_client = MagicMock()
        return service

    def test_headers_included_in_raw_mime(self, ses_service):
        ses_service.send_email("to@test.com", _email_with_headers())

        call_args = ses_service._ses_client.send_raw_email.call_args
        raw_data = (
            call_args.kwargs.get("RawMessage", {}).get("Data")
            or call_args[1]["RawMessage"]["Data"]
        )

        # Parse the MIME message
        msg = BytesParser(policy=policy.default).parsebytes(
            raw_data if isinstance(raw_data, bytes) else raw_data.encode()
        )

        assert msg["Reply-To"] == "reply+token123@replies.example.com"
        assert msg["Message-ID"] == "<msg-001@example.com>"
        assert msg["In-Reply-To"] == "<msg-000@example.com>"
        assert msg["References"] == "<msg-000@example.com>"

        # Should be multipart/alternative with text/plain and text/html
        assert msg.get_content_type() == "multipart/alternative"
        parts = list(msg.iter_parts())
        content_types = [p.get_content_type() for p in parts]
        assert "text/plain" in content_types
        assert "text/html" in content_types

    def test_headers_omitted_when_none(self, ses_service):
        ses_service.send_email("to@test.com", _email_without_headers())

        call_args = ses_service._ses_client.send_raw_email.call_args
        raw_data = (
            call_args.kwargs.get("RawMessage", {}).get("Data")
            or call_args[1]["RawMessage"]["Data"]
        )

        msg = BytesParser(policy=policy.default).parsebytes(
            raw_data if isinstance(raw_data, bytes) else raw_data.encode()
        )

        assert msg["Reply-To"] is None
        assert msg["Message-ID"] is None or msg["Message-ID"] == ""
        assert msg["In-Reply-To"] is None
        assert msg["References"] is None
        # No body_text, so should be text/html only (not multipart)
        assert msg.get_content_type() == "text/html"

    def test_non_ascii_subject_encoding(self, ses_service):
        """Non-ASCII subjects must be RFC 2047 encoded in raw MIME."""
        email = _email_with_headers(subject="Ré: données personnelles")
        ses_service.send_email("to@test.com", email)

        call_args = ses_service._ses_client.send_raw_email.call_args
        raw_data = (
            call_args.kwargs.get("RawMessage", {}).get("Data")
            or call_args[1]["RawMessage"]["Data"]
        )

        msg = BytesParser(policy=policy.default).parsebytes(
            raw_data if isinstance(raw_data, bytes) else raw_data.encode()
        )
        # Decoded subject should match
        assert msg["Subject"] == "Ré: données personnelles"

    def test_non_ascii_body_encoding(self, ses_service):
        """Non-ASCII body content must use appropriate transfer encoding."""
        email = _email_with_headers(
            body="<p>Données personnelles: café résumé</p>",
            body_text="Données personnelles: café résumé",
        )
        ses_service.send_email("to@test.com", email)

        call_args = ses_service._ses_client.send_raw_email.call_args
        raw_data = (
            call_args.kwargs.get("RawMessage", {}).get("Data")
            or call_args[1]["RawMessage"]["Data"]
        )

        msg = BytesParser(policy=policy.default).parsebytes(
            raw_data if isinstance(raw_data, bytes) else raw_data.encode()
        )

        # Both parts should decode correctly
        for part in msg.iter_parts():
            content = part.get_content()
            assert "café" in content
            assert "résumé" in content
