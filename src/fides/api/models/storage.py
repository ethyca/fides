from __future__ import annotations

from typing import Optional

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

from fides.api.db.base_class import Base, JSONTypeOverride
from fides.api.schemas.storage.storage import ResponseFormat, StorageType
from fides.api.schemas.storage.storage_secrets_docs_only import possible_storage_secrets
from fides.api.util.logger import Pii
from fides.api.util.storage_util import get_schema_for_secrets
from fides.config import CONFIG
from fides.config.config_proxy import ConfigProxy


class StorageConfig(Base):
    """The DB ORM model for StorageConfig"""

    name = Column(String, unique=True, index=True)
    type = Column(Enum(StorageType), index=True, nullable=False)
    # allows JSON to detect in-place mutations to the structure (when used with sqlalchemy)
    details = Column(MutableDict.as_mutable(JSONB), nullable=False)
    key = Column(String, index=True, unique=True, nullable=False)
    is_default = Column(Boolean, index=True, default=False, nullable=False)
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


def default_storage_config_name(storage_type: str) -> str:
    """
    Utility function for consistency in generating default storage config names.

    Returns a name to be used in a default storage config for the given type.
    """
    return f"Default Storage Config [{storage_type}]"


def get_default_storage_config_by_type(
    db: Session, storage_type: StorageType
) -> Optional[StorageConfig]:
    """
    Retrieve the default storage config for the given type by querying for the
    `StorageConfig` record with the given type and with `is_default` set to `True`.

    There should only ever be one `StorageConfig` record that
    matches this criteria at any point.

    If `local` storage type is requested and a default doesn't yet exist, we create a default.
    `local` storage configurations, at this point, don't have any configurable settings,
    so we can safely create a default here, at the time it's requested.
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

    if not default_storage and storage_type == StorageType.local:
        return _create_local_default_storage(db)
    return default_storage


def _create_local_default_storage(db: Session) -> StorageConfig:
    """
    Creates a default `local` storage configuration record in the database.

    `local` storage configurations, at this point, don't have any configurable settings,
    so we can safely create a standard default here, without any user input.
    """
    return StorageConfig.create(
        db,
        data={
            "name": default_storage_config_name(StorageType.local.value),
            "type": StorageType.local,
            "is_default": True,
            "format": ResponseFormat.html,
            "details": {"naming": "request_id"},
        },
    )


def get_active_default_storage_config(db: Session) -> Optional[StorageConfig]:
    """
    Utility function to return the active default storage configuration.

    As of now, we look at the application property `storage.active_default_storage_type`
    that's been set through the application settings API to determine the active default
    storage type. We use that to then look up the default configuration for that given
    storage type.

    If no `storage.active_default_storage_type` property has been set through the settings API,
    then we fall back the default `local` storage configuration.

    TODO: Eventually, we'll want the `storage.active_default_storage_type` to be settable
    via _either_ API or env var/toml, i.e. to be properly reconciled with the global
    pydantic config module. For now, though, we just rely on this being set through API.
    """
    active_default_storage_type = (
        ConfigProxy(db).storage.active_default_storage_type or StorageType.local
    )
    return get_default_storage_config_by_type(db, active_default_storage_type)
