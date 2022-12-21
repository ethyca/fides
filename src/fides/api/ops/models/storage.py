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

from fides.api.ops.db.base_class import JSONTypeOverride
from fides.api.ops.schemas.storage.storage import (
    SUPPORTED_STORAGE_SECRETS,
    ResponseFormat,
    StorageSecretsS3,
    StorageType,
)
from fides.api.ops.schemas.storage.storage_secrets_docs_only import (
    possible_storage_secrets,
)
from fides.api.ops.util.logger import Pii
from fides.core.config import get_config
from fides.lib.db.base import Base  # type: ignore[attr-defined]

CONFIG = get_config()


def get_schema_for_secrets(
    storage_type: StorageType,
    secrets: possible_storage_secrets,
) -> SUPPORTED_STORAGE_SECRETS:
    """
    Returns the secrets that pertain to `storage_type` represented as a Pydantic schema
    for validation purposes.
    """
    try:
        schema = {
            StorageType.s3: StorageSecretsS3,
        }[storage_type]
    except KeyError:
        raise ValueError(
            f"`storage_type` {storage_type} has no supported `secrets` validation."
        )

    try:
        return schema.parse_obj(secrets)  # type: ignore
    except ValidationError as exc:
        # Pydantic requires validators raise either a ValueError, TypeError, or AssertionError
        # so this exception is cast into a `ValueError`.
        errors = [f"{err['msg']} {str(err['loc'])}" for err in exc.errors()]
        raise ValueError(errors)


class StorageConfig(Base):
    """The DB ORM model for StorageConfig"""

    name = Column(String, unique=True, index=True)
    type = Column(Enum(StorageType), index=True, nullable=False)
    # allows JSON to detect in-place mutations to the structure (when used with sqlalchemy)
    details = Column(MutableDict.as_mutable(JSONB), nullable=False)
    key = Column(String, index=True, unique=True, nullable=False)
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

    format = Column(
        Enum(ResponseFormat), server_default="json", nullable=False, default="json"
    )

    def set_secrets(
        self,
        *,
        db: Session,
        storage_secrets: possible_storage_secrets,
    ) -> None:
        """Creates or updates secrets associated with a config id"""

        storage_type = self.type
        if not storage_type:
            raise ValueError("This object must have a `type` to validate secrets.")

        try:
            get_schema_for_secrets(
                storage_type=storage_type,  # type: ignore
                secrets=storage_secrets,
            )
        except (
            KeyError,
            ValidationError,
        ) as exc:
            logger.error("Error: {}", Pii(str(exc)))
            # We don't want to handle these explicitly here, only in the API view
            raise

        self.secrets = storage_secrets
        self.save(db=db)
