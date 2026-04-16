from abc import ABC, abstractmethod

from loguru import logger

from fides.api.common_exceptions import MessageDispatchException
from fides.api.models.messaging import MessagingConfig
from fides.api.schemas.messaging.messaging import EmailForActionType


class BaseMessageProviderService(ABC):
    """Base class for all messaging provider services.

    Subclasses must set ``provider_name`` — it is used in validation error
    messages to identify which provider failed.
    """

    provider_name: str

    def __init__(self, messaging_config: MessagingConfig):
        self.messaging_config = messaging_config
        self.validate_config()

    def validate_config(self) -> None:
        """Validates that the messaging config has required details and secrets.

        Raises MessageDispatchException if details or secrets are missing.
        Override in subclasses that need different validation (e.g., SMS
        providers that don't require details).
        """
        if not self.messaging_config.details or not self.messaging_config.secrets:
            error_message = (
                f"No {self.provider_name} config details or secrets supplied."
            )
            logger.error(f"Message failed to send. {error_message}")
            raise MessageDispatchException(error_message)


class BaseEmailProviderService(BaseMessageProviderService):
    """Base class for email provider services."""

    @abstractmethod
    def send_email(self, to: str, message: EmailForActionType) -> None: ...


class BaseSMSProviderService(BaseMessageProviderService):
    """Base class for SMS provider services."""

    @abstractmethod
    def send_sms(self, to: str, body: str) -> None: ...
