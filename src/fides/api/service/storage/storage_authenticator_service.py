from typing import Any, Dict

from botocore.exceptions import ClientError

from fides.api.models.storage import StorageConfig
from fides.api.schemas.storage.storage import (
    SUPPORTED_STORAGE_SECRETS,
    StorageSecrets,
    StorageType,
)
from fides.api.util.aws_util import get_aws_session


def secrets_are_valid(
    secrets: SUPPORTED_STORAGE_SECRETS,
    storage_config: StorageConfig,
) -> bool:
    """Authenticates upload destination with appropriate upload method"""
    uploader: Any = _get_authenticator_from_config(storage_config.type)
    return uploader(storage_config, secrets)


def _s3_authenticator(
    config: StorageConfig, secrets: Dict[StorageSecrets, Any]
) -> bool:
    """Authenticates secrets for s3, returns true if secrets are valid"""
    try:
        get_aws_session(config.details["auth_method"], secrets.model_dump(mode="json"))  # type: ignore
        return True
    except ClientError:
        return False


def _get_authenticator_from_config(storage_type: StorageType) -> Any:
    """Determines which uploader method to use based on storage type"""
    return {
        StorageType.s3.value: _s3_authenticator,
    }[storage_type.value]
