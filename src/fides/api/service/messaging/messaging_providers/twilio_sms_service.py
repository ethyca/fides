from loguru import logger
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from fides.api.common_exceptions import MessageDispatchException
from fides.api.models.messaging import MessagingConfig
from fides.api.schemas.messaging.messaging import MessagingServiceSecrets
from fides.api.service.messaging.messaging_providers.base import (
    BaseSMSProviderService,
)


class TwilioSmsService(BaseSMSProviderService):
    """Dispatches SMS using Twilio."""

    provider_name = "Twilio SMS"

    def __init__(self, messaging_config: MessagingConfig):
        super().__init__(messaging_config)
        self.account_sid = messaging_config.secrets[
            MessagingServiceSecrets.TWILIO_ACCOUNT_SID.value
        ]
        self.auth_token = messaging_config.secrets[
            MessagingServiceSecrets.TWILIO_AUTH_TOKEN.value
        ]
        self.messaging_service_sid = messaging_config.secrets.get(
            MessagingServiceSecrets.TWILIO_MESSAGING_SERVICE_SID.value
        )
        self.sender_phone_number = messaging_config.secrets.get(
            MessagingServiceSecrets.TWILIO_SENDER_PHONE_NUMBER.value
        )

    def validate_config(self) -> None:
        """Twilio SMS only requires secrets (no details)."""
        if not self.messaging_config.secrets:
            error_message = f"No {self.provider_name} config secrets supplied."
            logger.error(f"Message failed to send. {error_message}")
            raise MessageDispatchException(error_message)

    def send_sms(self, to: str, body: str) -> None:
        client = Client(self.account_sid, self.auth_token)
        try:
            if self.messaging_service_sid:
                client.messages.create(
                    to=to,
                    messaging_service_sid=self.messaging_service_sid,
                    body=body,
                )
            elif self.sender_phone_number:
                client.messages.create(to=to, from_=self.sender_phone_number, body=body)
            else:
                logger.error(
                    "Message failed to send. Either sender phone number or messaging service sid must be provided."
                )
                raise MessageDispatchException(
                    "Message failed to send. Either sender phone number or messaging service sid must be provided."
                )
        except TwilioRestException as exc:
            logger.error("Twilio SMS failed to send: {}", str(exc))
            raise MessageDispatchException(
                f"Twilio SMS failed to send due to: {str(exc)}"
            )
