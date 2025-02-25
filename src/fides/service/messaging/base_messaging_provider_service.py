from abc import ABC, abstractmethod
from typing import Optional

from loguru import logger

from fides.api.common_exceptions import MessageDispatchException
from fides.api.models.messaging import MessagingConfig
from fides.api.schemas.messaging.messaging import EmailForActionType

EMAIL_TEMPLATE_NAME = "fides"


class BaseMessageProviderService(ABC):
    provider_name: str
    # Some message providers will only have secrets
    validate_details: Optional[bool] = True

    def __init__(self, messaging_config: MessagingConfig):
        self.messaging_config = messaging_config

        self.validate_config()

    def validate_config(self) -> None:
        """
        Validates that the messaging config has the required details and secrets.
        """
        condition = (
            not self.messaging_config.details or not self.messaging_config.secrets
            if self.validate_details
            else not self.messaging_config.secrets
        )

        if condition:
            error_message = f"No {self.provider_name} config {'details or secrets' if self.validate_details else 'secrets'} supplied."
            logger.error(f"Message failed to send. {error_message}")
            raise MessageDispatchException(error_message)

    @abstractmethod
    def send_message(self, message: EmailForActionType, to: str) -> None:
        pass
