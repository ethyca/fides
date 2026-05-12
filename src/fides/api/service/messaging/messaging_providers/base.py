from abc import ABC, abstractmethod
from email import policy as email_policy
from email.message import EmailMessage
from typing import ClassVar

from loguru import logger

from fides.api.common_exceptions import MessageDispatchException
from fides.api.models.messaging import MessagingConfig
from fides.api.schemas.messaging.messaging import (
    EmailForActionType,
    MessagingServiceDetails,
    MessagingServiceSecrets,
)

EMAIL_TEMPLATE_NAME = "fides"


class BaseMessageProviderService(ABC):
    """Base class for all messaging provider services.

    Subclasses must set ``provider_name`` — it is used in validation error
    messages to identify which provider failed.
    """

    provider_name: ClassVar[str]

    def __init__(self, messaging_config: MessagingConfig):
        if not getattr(self, "provider_name", None):
            raise TypeError(f"{type(self).__name__} must define 'provider_name'")
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

    def validate_on_save(self) -> None:
        """Optional hook for config-save-time validation. Default no-op.

        Override in subclasses that need to verify external state (e.g.,
        SES identity verification) when secrets are saved.
        """

    def _get_detail(self, key: MessagingServiceDetails) -> str:
        """Retrieve a required config detail, raising MessageDispatchException if missing."""
        try:
            return self.messaging_config.details[key.value]
        except (KeyError, TypeError) as exc:
            raise MessageDispatchException(
                f"{self.provider_name} config is missing required detail: {key.value}"
            ) from exc

    def _get_secret(self, key: MessagingServiceSecrets) -> str:
        """Retrieve a required config secret, raising MessageDispatchException if missing."""
        try:
            return self.messaging_config.secrets[key.value]
        except (KeyError, TypeError) as exc:
            raise MessageDispatchException(
                f"{self.provider_name} config is missing required secret: {key.value}"
            ) from exc

    def _get_optional_secret(self, key: MessagingServiceSecrets) -> str | None:
        """Retrieve an optional config secret, returning None if missing."""
        if not self.messaging_config.secrets:
            return None
        return self.messaging_config.secrets.get(key.value)


class BaseEmailProviderService(BaseMessageProviderService):
    """Base class for email provider services."""

    HEADER_REPLY_TO = "Reply-To"
    HEADER_MESSAGE_ID = "Message-ID"
    HEADER_IN_REPLY_TO = "In-Reply-To"
    HEADER_REFERENCES = "References"

    @abstractmethod
    def send_email(self, to: str, message: EmailForActionType) -> None: ...

    @staticmethod
    def get_threading_headers(
        message: EmailForActionType, header_prefix: str = ""
    ) -> dict[str, str]:
        """Return non-None threading headers from the message."""
        candidates = {
            BaseEmailProviderService.HEADER_REPLY_TO: message.reply_to,
            BaseEmailProviderService.HEADER_MESSAGE_ID: message.message_id,
            BaseEmailProviderService.HEADER_IN_REPLY_TO: message.in_reply_to,
            BaseEmailProviderService.HEADER_REFERENCES: message.references,
        }
        return {f"{header_prefix}{k}": v for k, v in candidates.items() if v}

    @staticmethod
    def build_mime(
        from_address: str, to: str, message: EmailForActionType
    ) -> EmailMessage:
        """Build a MIME EmailMessage with optional threading headers.

        Reusable by any provider that sends raw MIME (e.g., SES, SMTP).
        """
        msg = EmailMessage(policy=email_policy.SMTP)
        msg["From"] = from_address
        msg["To"] = to
        msg["Subject"] = message.subject

        for header, value in BaseEmailProviderService.get_threading_headers(
            message
        ).items():
            msg[header] = value

        if message.body_text:
            # The RFC 2046 multipart/alternative spec says parts should be
            # ordered from simplest to richest. The email client picks the
            # richest part it can render successfully.
            msg.set_content(message.body_text)
            msg.add_alternative(message.body, subtype="html")
        else:
            msg.set_content(message.body, subtype="html")

        return msg


class BaseSMSProviderService(BaseMessageProviderService):
    """Base class for SMS provider services."""

    @abstractmethod
    def send_sms(self, to: str, body: str) -> None: ...
