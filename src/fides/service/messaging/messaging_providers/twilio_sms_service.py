from typing import Literal

from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from loguru import logger

from fides.api.models.messaging import MessagingConfig
from fides.api.schemas.messaging.messaging import (
    MessagingServiceSecretsTwilioSMS,
    EmailForActionType,
)

from fides.api.util.logger import Pii
from fides.api.common_exceptions import MessageDispatchException

from fides.service.messaging.messaging_providers.base_messaging_provider_service import (
    BaseSMSProviderService,
)


class TwilioSMSException(Exception):
    pass


class TwilioSMSService(BaseSMSProviderService):
    provider_name: Literal["Twilio SMS"] = "Twilio SMS"
    validate_details = False  # Twilio SMS Config does not have details

    def __init__(self, messaging_config: MessagingConfig):
        super().__init__(messaging_config)

        self.messaging_config_secrets = MessagingServiceSecretsTwilioSMS.model_validate(
            messaging_config.secrets
        )

    def send_message(
        self,
        to: str,
        message: str,
    ) -> None:
        """
        Sends a message using Twilio SMS.
        """

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
                raise MessageDispatchException(
                    "Message failed to send. Either sender phone number or messaging service sid must be provided."
                )
        except TwilioRestException as e:
            logger.error("Twilio SMS failed to send: {}", Pii(str(e)))
            raise MessageDispatchException(
                f"Twilio SMS failed to send due to: {Pii(e)}"
            )
