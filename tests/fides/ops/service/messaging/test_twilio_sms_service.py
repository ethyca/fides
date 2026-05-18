from unittest import mock

import pytest
from twilio.base.exceptions import TwilioRestException

from fides.api.common_exceptions import MessageDispatchException
from fides.api.schemas.messaging.messaging import MessagingServiceSecrets
from fides.api.service.messaging.messaging_providers.twilio_sms_service import (
    TwilioSmsService,
)


@pytest.mark.unit
class TestTwilioSmsProvider:
    def test_dispatch_no_secrets(self, messaging_config_twilio_sms):
        messaging_config_twilio_sms.secrets = None
        with pytest.raises(MessageDispatchException) as exc:
            TwilioSmsService(messaging_config_twilio_sms)

        assert "No Twilio SMS config secrets supplied" in str(exc.value)

    def test_dispatch_no_sender(self, messaging_config_twilio_sms):
        messaging_config_twilio_sms.secrets[
            MessagingServiceSecrets.TWILIO_MESSAGING_SERVICE_SID.value
        ] = None
        messaging_config_twilio_sms.secrets[
            MessagingServiceSecrets.TWILIO_SENDER_PHONE_NUMBER.value
        ] = None
        service = TwilioSmsService(messaging_config_twilio_sms)
        with pytest.raises(MessageDispatchException) as exc:
            service.send_sms("+9198675309", "test")

        assert "must be provided" in str(exc.value)

    @mock.patch(
        "fides.api.service.messaging.messaging_providers.twilio_sms_service.Client",
        autospec=True,
    )
    def test_send_sms_success(
        self, mock_twilio_client_cls, messaging_config_twilio_sms
    ):
        service = TwilioSmsService(messaging_config_twilio_sms)
        service.send_sms("+19198675309", "Test message")
        mock_client = mock_twilio_client_cls.return_value
        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["to"] == "+19198675309"
        assert call_kwargs["body"] == "Test message"

    @mock.patch(
        "fides.api.service.messaging.messaging_providers.twilio_sms_service.Client",
        autospec=True,
    )
    def test_send_sms_twilio_rest_exception(
        self, mock_twilio_client_cls, messaging_config_twilio_sms
    ):
        mock_client = mock_twilio_client_cls.return_value
        mock_client.messages.create.side_effect = TwilioRestException(
            status=400, uri="/Messages", msg="Invalid phone number"
        )
        service = TwilioSmsService(messaging_config_twilio_sms)
        with pytest.raises(MessageDispatchException, match="Twilio SMS failed to send"):
            service.send_sms("+19198675309", "Test message")
