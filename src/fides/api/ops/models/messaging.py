from typing import Optional

from loguru import logger
from pydantic import ValidationError
from sqlalchemy import Column, Enum, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Session
from sqlalchemy_utils.types.encrypted.encrypted_type import (
    AesGcmEngine,
    StringEncryptedType,
)

from fides.api.ops.common_exceptions import MessageDispatchException
from fides.api.ops.db.base_class import JSONTypeOverride
from fides.api.ops.schemas.messaging.messaging import (
    EMAIL_MESSAGING_SERVICES,
    SMS_MESSAGING_SERVICES,
    SUPPORTED_MESSAGING_SERVICE_SECRETS,
    MessagingMethod,
    MessagingServiceSecretsMailgun,
    MessagingServiceSecretsTwilioEmail,
    MessagingServiceSecretsTwilioSMS,
    MessagingServiceType,
)
from fides.api.ops.schemas.messaging.messaging_secrets_docs_only import (
    possible_messaging_secrets,
)
from fides.api.ops.util.logger import Pii
from fides.core.config import get_config
from fides.lib.db.base import Base  # type: ignore[attr-defined]

CONFIG = get_config()


def get_messaging_method(
    service_type: Optional[str],
) -> Optional[MessagingMethod]:
    """returns messaging method based on configured service type"""
    if service_type in EMAIL_MESSAGING_SERVICES:
        return MessagingMethod.EMAIL
    if service_type in SMS_MESSAGING_SERVICES:
        return MessagingMethod.SMS
    return None


def get_schema_for_secrets(
    service_type: MessagingServiceType,
    secrets: possible_messaging_secrets,
) -> SUPPORTED_MESSAGING_SERVICE_SECRETS:
    """
    Returns the secrets that pertain to `service_type` represented as a Pydantic schema
    for validation purposes.
    """
    try:
        schema = {
            MessagingServiceType.MAILGUN: MessagingServiceSecretsMailgun,
            MessagingServiceType.TWILIO_TEXT: MessagingServiceSecretsTwilioSMS,
            MessagingServiceType.TWILIO_EMAIL: MessagingServiceSecretsTwilioEmail,
        }[service_type]
    except KeyError:
        raise ValueError(
            f"`service_type` {service_type} has no supported `secrets` validation."
        )

    try:
        return schema.parse_obj(secrets)  # type: ignore
    except ValidationError as exc:
        # Pydantic requires validators raise either a ValueError, TypeError, or AssertionError
        # so this exception is cast into a `ValueError`.
        errors = [f"{err['msg']} {str(err['loc'])}" for err in exc.errors()]
        raise ValueError(errors)


class MessagingConfig(Base):
    """The DB ORM model for MessagingConfig"""

    key = Column(String, index=True, unique=True, nullable=False)
    name = Column(String, unique=True, index=True)
    service_type = Column(
        Enum(MessagingServiceType), index=True, unique=True, nullable=False
    )
    details = Column(MutableDict.as_mutable(JSONB), nullable=True)
    secrets = Column(
        MutableDict.as_mutable(
            StringEncryptedType(
                JSONTypeOverride,
                CONFIG.security.app_encryption_key,
                AesGcmEngine,
                "pkcs5",
            )
        ),
        nullable=True,
    )  # Type bytea in the db

    @classmethod
    def get_configuration(cls, db: Session, service_type: str) -> Base:
        """
        Fetches the configured MessagingConfig record by service type. Once fetched this function validates that
        the MessagingConfig is configured with secrets.
        """
        instance: Optional[Base] = cls.get_by(
            db=db, field="service_type", value=service_type
        )
        if not instance:
            raise MessageDispatchException(
                f"No messaging config found for service_type {service_type}."
            )
        if not instance.secrets:
            logger.warning(
                "Messaging secrets not found for config with key: {}", instance.key
            )
            raise MessageDispatchException(
                f"Messaging secrets not found for config with key: {instance.key}"
            )
        return instance

    def set_secrets(
        self,
        *,
        db: Session,
        messaging_secrets: possible_messaging_secrets,
    ) -> None:
        """Creates or updates secrets associated with a config id"""

        service_type = self.service_type
        if not service_type:
            raise ValueError(
                "This object must have a `service_type` to validate secrets."
            )

        try:
            get_schema_for_secrets(
                service_type=service_type,  # type: ignore
                secrets=messaging_secrets,
            )
        except (
            KeyError,
            ValidationError,
        ) as exc:
            logger.error("Error: {}", Pii(str(exc)))
            # We don't want to handle these explicitly here, only in the API view
            raise

        self.secrets = messaging_secrets
        self.save(db=db)
