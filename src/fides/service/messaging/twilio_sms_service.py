from loguru import logger
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from fides.api.models.messaging import MessagingConfig
from fides.api.schemas.messaging.messaging import (
    MessagingServiceSecretsTwilioSMS,
)
from fides.api.util.logger import Pii


class TwilioSMSException(Exception):
    pass


class TwilioSMSService:
    def __init__(self, messaging_config: MessagingConfig):
        self.messaging_config_secrets = MessagingServiceSecretsTwilioSMS.model_validate(
            messaging_config.secrets
        )

    def send_sms(
        self,
        message: str,
        to: str,
    ) -> None:
        """Dispatches SMS using Twilio"""
        account_sid = self.messaging_config_secrets.twilio_account_sid
        auth_token = self.messaging_config_secrets.twilio_auth_token
        messaging_service_id = (
            self.messaging_config_secrets.twilio_messaging_service_sid
        )
        sender_phone_number = self.messaging_config_secrets.twilio_sender_phone_number

        client = Client(account_sid, auth_token)
        try:
            if messaging_service_id:
                client.messages.create(
                    to=to, messaging_service_sid=messaging_service_id, body=message
                )
            elif sender_phone_number:
                client.messages.create(to=to, from_=sender_phone_number, body=message)
            else:
                logger.error(
                    "Message failed to send. Either sender phone number or messaging service sid must be provided."
                )
                raise TwilioSMSException(
                    "Message failed to send. Either sender phone number or messaging service sid must be provided."
                )
        except TwilioRestException as e:
            logger.error("Twilio SMS failed to send: {}", Pii(str(e)))
            raise TwilioSMSException(f"Twilio SMS failed to send due to: {Pii(e)}")
