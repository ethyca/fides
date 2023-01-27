from __future__ import annotations

from typing import Any, Optional

from loguru import logger
from pydantic import ValidationError
from sqlalchemy import Boolean, Column, Enum, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Session
from sqlalchemy_utils.types.encrypted.encrypted_type import (
    AesGcmEngine,
    StringEncryptedType,
)

from fides.api.ops.db.base_class import JSONTypeOverride
from fides.api.ops.schemas.storage.storage import ResponseFormat, StorageType
from fides.api.ops.schemas.storage.storage_secrets_docs_only import (
    possible_storage_secrets,
)
from fides.api.ops.util.logger import Pii
from fides.api.ops.util.storage_util import get_schema_for_secrets
from fides.core.config import get_config
from fides.lib.db.base import Base

CONFIG = get_config()


class StorageConfig(Base):
    """The DB ORM model for StorageConfig"""

    name = Column(String, unique=True, index=True)
    type = Column(Enum(StorageType), index=True, nullable=False)
    # allows JSON to detect in-place mutations to the structure (when used with sqlalchemy)
    details = Column(MutableDict.as_mutable(JSONB), nullable=False)
    key = Column(String, index=True, unique=True, nullable=False)
    is_default = Column(Boolean, index=True, default=False)
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

    __table_args__ = (
        Index(
            "only_one_default_per_type",
            type,
            is_default,
            unique=True,
            postgresql_where=(is_default),
        ),
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


def default_storage_config_by_type(
    db: Session, storage_type: StorageType
) -> Optional[StorageConfig]:
    """
    Retrieve the default storage config for the given type by querying for the
    `StorageConfig` record with the given type and with `is_default` set to `True`.

    There should only ever be one `StorageConfig` record that
    matches this criteria at any point.
    """
    if not isinstance(storage_type, StorageType):
        # try to coerce into an enum
        try:
            storage_type = StorageType[storage_type]
        except KeyError:
            raise ValueError(
                "storage_type argument must be a valid StorageType enum member."
            )
    default_storage: Optional[StorageConfig] = (
        db.query(StorageConfig).filter_by(is_default=True, type=storage_type).first()
    )
    return default_storage


def active_default_storage_config(db: Session):
    """
    Retrieve the active default storage config.

    At this point, this is just hardcoded to the default s3 config.
    TODO: update to rely on config setting to determine the active default.
    """
    return default_storage_config_by_type(db, StorageType.local)
