from __future__ import annotations

from pydantic import Extra, validator

from fides.api.ops.schemas.storage.storage import StorageType
from fides.lib.schemas.base_class import BaseSchema


class StorageApplicationConfig(BaseSchema):
    active_default_storage_type: StorageType

    class Config:
        use_enum_values = True
        extra = Extra.forbid

    @validator("active_default_storage_type")
    @classmethod
    def validate_storage_type(cls, storage_type: StorageType) -> StorageType:
        """
        For now, only `local` and `s3` storage types are supported
        as an `active_default_storage_type`
        """
        valid_storage_types = (StorageType.local.value, StorageType.s3.value)
        if storage_type not in valid_storage_types:
            raise ValueError(
                f"Only '{valid_storage_types}' are supported as `active_default_storage_type`s"
            )
        return storage_type


class ApplicationConfig(BaseSchema):
    """
    Application config settings update body is an arbitrary dict (JSON object)
    We describe it in a schema to enforce some restrictions on the keys passed.

    TODO: Eventually this should be driven by a more formal validation schema for this
    the application config that is properly hooked up to the global pydantic config module.
    """

    storage: StorageApplicationConfig

    class Config:
        extra = Extra.forbid
