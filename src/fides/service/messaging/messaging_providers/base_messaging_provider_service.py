from abc import ABC, abstractmethod
from typing import Optional

from loguru import logger

from fides.api.common_exceptions import MessageDispatchException
from fides.api.models.messaging import MessagingConfig
from fides.api.schemas.messaging.messaging import EmailForActionType

EMAIL_TEMPLATE_NAME = "fides"


class BaseMessageProviderService(ABC):
    """
    Base class for Messaging provider services.
    Services shouldn't inherit directly from this class, but from one of its
    more specific subclasses (BaseEmailProviderService, BaseSMSProviderService)
    """

    provider_name: str
    # Some message providers will only have secrets
    validate_details: Optional[bool] = True

    def __init__(self, messaging_config: MessagingConfig):
        self.messaging_config = messaging_config

        assert (
            self.provider_name
        ), "Provider name must be set in child classes of BaseMessageProviderService."

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


class BaseEmailProviderService(BaseMessageProviderService):
    @abstractmethod
    def send_email(
        self,
        to: str,
        message: EmailForActionType,
    ) -> None:
        pass


class BaseSMSProviderService(BaseMessageProviderService):
    @abstractmethod
    def send_message(
        self,
        to: str,
        message: str,
    ) -> None:
        pass
