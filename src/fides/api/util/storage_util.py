from datetime import datetime
from typing import Any, Union

from bson import ObjectId
from pydantic import ValidationError

from fides.api.schemas.storage.storage import (
    SUPPORTED_STORAGE_SECRETS,
    StorageSecretsGCS,
    StorageSecretsS3,
    StorageType,
)
from fides.api.schemas.storage.storage_secrets_docs_only import possible_storage_secrets
from fides.api.util.custom_json_encoder import CustomJSONEncoder


def format_size(size_bytes: float) -> str:
    """
    Format size in bytes to human readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted string with appropriate unit (B, KB, MB, GB, TB, PB)
    """
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_bytes)
    for unit in units:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


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
            StorageType.gcs: StorageSecretsGCS,
        }[storage_type]
    except KeyError:
        raise ValueError(
            f"`storage_type` {storage_type} has no supported `secrets` validation."
        )

    try:
        return schema.model_validate(secrets)  # type: ignore
    except ValidationError as exc:
        # Pydantic requires validators raise either a ValueError, TypeError, or AssertionError
        # so this exception is cast into a `ValueError`.
        errors = [f"{err['msg']} {str(err['loc'])}" for err in exc.errors()]
        raise ValueError(errors)


class StorageJSONEncoder(CustomJSONEncoder):
    """
    A JSON encoder specifically for storage operations that maintains the original
    format for datetime and ObjectId while inheriting other functionality from CustomJSONEncoder.
    """

    def default(self, o: Any) -> Any:
        if isinstance(o, datetime):
            return o.strftime("%Y-%m-%dT%H:%M:%S")
        if isinstance(o, ObjectId):
            return {"$oid": str(o)}
        return super().default(o)
