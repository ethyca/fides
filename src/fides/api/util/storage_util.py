from datetime import datetime
from typing import Any, Dict, Union

from bson import ObjectId
from pydantic import ValidationError

from fides.api.schemas.storage.storage import (
    SUPPORTED_STORAGE_SECRETS,
    StorageSecretsS3,
    StorageType,
)
from fides.api.schemas.storage.storage_secrets_docs_only import possible_storage_secrets


def get_schema_for_secrets(
    storage_type: Union[StorageType, str],
    secrets: possible_storage_secrets,
) -> SUPPORTED_STORAGE_SECRETS:
    """
    Returns the secrets that pertain to `storage_type` represented as a Pydantic schema
    for validation purposes.
    """
    if not isinstance(storage_type, StorageType):
        # try to coerce into an enum
        try:
            storage_type = StorageType[storage_type]
        except KeyError:
            raise ValueError(
                "storage_type argument must be a valid StorageType enum member."
            )
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


def storage_json_encoder(field: Any) -> Union[str, Dict[str, str]]:
    """Specify str format for datetime objects"""
    if isinstance(field, datetime):
        return field.strftime("%Y-%m-%dT%H:%M:%S")
    if isinstance(field, ObjectId):
        return {"$oid": str(field)}
    return field
