from typing import Any, Dict

from botocore.exceptions import ClientError

from fides.api.ops.schemas.storage.storage import (
    SUPPORTED_STORAGE_SECRETS,
    S3AuthMethod,
    StorageSecrets,
    StorageType,
)
from fides.api.ops.util.storage_authenticator import get_s3_session


def secrets_are_valid(
    secrets: SUPPORTED_STORAGE_SECRETS,
    storage_type: StorageType,
) -> bool:
    """Authenticates upload destination with appropriate upload method"""
    uploader: Any = _get_authenticator_from_config(storage_type)
    return uploader(secrets)


def _s3_authenticator(secrets: Dict[StorageSecrets, Any]) -> bool:
    """Authenticates secrets for s3, returns true if secrets are valid"""
    try:
        get_s3_session(S3AuthMethod.SECRET_KEYS.value, secrets.dict())  # type: ignore
        return True
    except ClientError:
        return False


def _get_authenticator_from_config(storage_type: StorageType) -> Any:
    """Determines which uploader method to use based on storage type"""
    return {
        StorageType.s3.value: _s3_authenticator,
    }[storage_type.value]
