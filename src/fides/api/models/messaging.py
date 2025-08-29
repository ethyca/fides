from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional, Type, Union

from loguru import logger
from pydantic import ValidationError
from sqlalchemy import Boolean, Column, DateTime, Enum, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Session
from sqlalchemy_utils.types.encrypted.encrypted_type import (
    AesGcmEngine,
    StringEncryptedType,
)

from fides.api.common_exceptions import MessageDispatchException
from fides.api.db.base_class import Base, JSONTypeOverride
from fides.api.schemas.messaging.messaging import (
    EMAIL_MESSAGING_SERVICES,
    SMS_MESSAGING_SERVICES,
    MessagingConnectionTestStatus,
    MessagingMethod,
    MessagingServiceType,
)
from fides.api.schemas.messaging.shared_schemas import (
    SUPPORTED_MESSAGING_SERVICE_SECRETS,
    MessagingServiceSecretsAWS_SES,
    MessagingServiceSecretsMailchimpTransactional,
    MessagingServiceSecretsMailgun,
    MessagingServiceSecretsTwilioEmail,
    MessagingServiceSecretsTwilioSMS,
    PossibleMessagingSecrets,
)
from fides.api.util.logger import Pii
from fides.config import CONFIG
from fides.config.config_proxy import ConfigProxy


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
    secrets: PossibleMessagingSecrets,
) -> SUPPORTED_MESSAGING_SERVICE_SECRETS:
    """
    Returns the secrets that pertain to `service_type` represented as a Pydantic schema
    for validation purposes.
    """
    messaging_secret_schema_type = Union[
        Type[MessagingServiceSecretsMailgun],
        Type[MessagingServiceSecretsTwilioSMS],
        Type[MessagingServiceSecretsTwilioEmail],
        Type[MessagingServiceSecretsMailchimpTransactional],
        Type[MessagingServiceSecretsAWS_SES],
    ]
    try:
        schema_mapping: Dict[MessagingServiceType, messaging_secret_schema_type] = {
            MessagingServiceType.mailgun: MessagingServiceSecretsMailgun,
            MessagingServiceType.twilio_text: MessagingServiceSecretsTwilioSMS,
            MessagingServiceType.twilio_email: MessagingServiceSecretsTwilioEmail,
            MessagingServiceType.mailchimp_transactional: MessagingServiceSecretsMailchimpTransactional,
            MessagingServiceType.aws_ses: MessagingServiceSecretsAWS_SES,
        }
        schema: messaging_secret_schema_type = schema_mapping[service_type]
    except KeyError:
        raise ValueError(
            f"`service_type` {service_type} has no supported `secrets` validation."
        )

    return schema.model_validate(secrets)


class MessagingConfig(Base):
    """The DB ORM model for MessagingConfig"""

    key = Column(String, index=True, unique=True, nullable=False)
    name = Column(String, unique=True, index=True)
    service_type = Column(
        Enum(MessagingServiceType), index=True, unique=True, nullable=False
    )
    details = Column(MutableDict.as_mutable(JSONB), nullable=True)
    last_test_timestamp = Column(DateTime(timezone=True))
    last_test_succeeded = Column(Boolean)
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
    def get_configuration(cls, db: Session, service_type: str) -> MessagingConfig:
        """
        Fetches the configured MessagingConfig record by service type. Once fetched this function validates that
        the MessagingConfig is configured with secrets.
        """
        instance: Optional[MessagingConfig] = cls.get_by(
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

    @classmethod
    def get_by_type(
        cls,
        db: Session,
        service_type: MessagingServiceType,
    ) -> Optional[MessagingConfig]:
        """
        Retrieve the messaging config of the given type
        """
        return db.query(cls).filter_by(service_type=service_type.value).first()

    def set_secrets(
        self,
        *,
        db: Session,
        messaging_secrets: PossibleMessagingSecrets,
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

    @classmethod
    def get_active_default(cls, db: Session) -> Optional[MessagingConfig]:
        """
        Utility method to return the active default messaging configuration.

        This is determined by looking at the `notifications.notification_service_type`
        config property. We determine that config property's value by using
        the ConfigProxy, which resolves the value based on API-set or traditional
        config-set mechanisms.
        """
        active_default_messaging_type = ConfigProxy(
            db
        ).notifications.notification_service_type
        if not active_default_messaging_type:
            return None
        try:
            service_type = MessagingServiceType[active_default_messaging_type]
            return cls.get_by_type(db, service_type)
        except KeyError:
            raise ValueError(
                f"Unknown notification_service_type {active_default_messaging_type} configured"
            )

    def update_test_status(
        self, test_status: MessagingConnectionTestStatus, db: Session
    ) -> None:
        """
        Updates last_test_timestamp and last_test_succeeded after an attempt to send a test message.
        """
        self.last_test_timestamp = datetime.now()
        self.last_test_succeeded = (
            test_status == MessagingConnectionTestStatus.succeeded
        )
        self.save(db)


def default_messaging_config_name(service_type: str) -> str:
    """
    Utility function for consistency in generating default message config names.

    Returns a name to be used in a default messaging config for the given type.
    """
    return MessagingServiceType(service_type).human_readable


def default_messaging_config_key(service_type: str) -> str:
    """
    Utility function for consistency in generating default message config keys.

    Returns a key to be used in a default messaging config for the given type.
    """
    # Historically, when a key was not supplied, the service type string itself
    # was used as the key (e.g. "mailgun").  Reverting to that behaviour keeps
    # backward-compatibility with existing tests and API consumers that may rely
    # on this convention.
    return service_type.lower()
