from abc import ABC, abstractmethod

from fides.api.models.messaging import MessagingConfig

from fides.api.schemas.messaging.messaging import EmailForActionType

EMAIL_TEMPLATE_NAME = "fides"


class BaseMessageProviderService(ABC):

    def __init__(self, messaging_config: MessagingConfig):
        self.messaging_config = messaging_config

    @abstractmethod
    def send_message(self, message: EmailForActionType, to: str) -> None:
        pass
