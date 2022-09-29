import logging
from typing import Optional

from fideslib.db.base import Base
from pydantic import ValidationError
from sqlalchemy import Column, Enum, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Session
from sqlalchemy_utils.types.encrypted.encrypted_type import (
    AesGcmEngine,
    StringEncryptedType,
)

from fides.api.ops.common_exceptions import EmailDispatchException
from fides.api.ops.db.base_class import JSONTypeOverride
from fides.api.ops.schemas.email.email import (
    SUPPORTED_EMAIL_SERVICE_SECRETS,
    EmailServiceSecretsMailgun,
    EmailServiceType,
)
from fides.api.ops.schemas.email.email_secrets_docs_only import possible_email_secrets
from fides.api.ops.util.logger import Pii
from fides.ctl.core.config import get_config

CONFIG = get_config()
logger = logging.getLogger(__name__)


def get_schema_for_secrets(
    service_type: EmailServiceType,
    secrets: possible_email_secrets,
) -> SUPPORTED_EMAIL_SERVICE_SECRETS:
    """
    Returns the secrets that pertain to `service_type` represented as a Pydantic schema
    for validation purposes.
    """
    try:
        schema = {
            EmailServiceType.MAILGUN: EmailServiceSecretsMailgun,
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


class EmailConfig(Base):
    """The DB ORM model for EmailConfig"""

    key = Column(String, index=True, unique=True, nullable=False)
    name = Column(String, unique=True, index=True)
    service_type = Column(Enum(EmailServiceType), index=True, nullable=False)
    details = Column(MutableDict.as_mutable(JSONB), nullable=False)
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
    def get_configuration(cls, db: Session) -> Base:
        """
        Fetches the first configured EmailConfig record. As of v1.7.3 Fidesops does not support
        multiple configured email connectors. Once fetched this function validates that
        the EmailConfig is configured with secrets.
        """
        instance: Optional[Base] = cls.query(db=db).first()
        if not instance:
            raise EmailDispatchException("No email config found.")
        if not instance.secrets:
            logger.warning(
                "Email secrets not found for config with key: %s", instance.key
            )
            raise EmailDispatchException(
                f"Email secrets not found for config with key: {instance.key}"
            )
        return instance

    def set_secrets(
        self,
        *,
        db: Session,
        email_secrets: possible_email_secrets,
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
                secrets=email_secrets,
            )
        except (
            KeyError,
            ValidationError,
        ) as exc:
            logger.error("Error: %s", Pii(str(exc)))
            # We don't want to handle these explicitly here, only in the API view
            raise

        self.secrets = email_secrets
        self.save(db=db)
