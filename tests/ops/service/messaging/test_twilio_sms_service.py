import pytest

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
