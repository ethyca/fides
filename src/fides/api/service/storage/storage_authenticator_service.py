from typing import Any

from botocore.exceptions import ClientError
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from loguru import logger

from fides.api.models.storage import StorageConfig
from fides.api.schemas.storage.storage import (
    SUPPORTED_STORAGE_SECRETS,
    AWSAuthMethod,
    StorageSecrets,
    StorageType,
)
from fides.api.util.aws_util import get_aws_session


def secrets_are_valid(
    secrets: SUPPORTED_STORAGE_SECRETS,
    storage_config: StorageConfig,
) -> bool:
    """Authenticates upload destination with appropriate upload method"""
    uploader: Any = _get_authenticator_from_config(storage_config.type)  # type: ignore
    return uploader(storage_config, secrets)


def _s3_authenticator(
    config: StorageConfig, secrets: dict[StorageSecrets, Any]
) -> bool:
    """Authenticates secrets for s3, returns true if secrets are valid"""
    try:
        get_aws_session(config.details["auth_method"] or AWSAuthMethod.SECRET_KEYS.value, secrets.model_dump(mode="json"))  # type: ignore
        return True
    except ClientError:
        return False


def _gcs_authenticator(storage_config: StorageConfig, secrets: dict) -> bool:
    """Autenticates secrets for Google Cloud Storage, returns true if secrets are valid"""
    try:
        credentials = service_account.Credentials.from_service_account_info(
            dict(secrets),
            scopes=["https://www.googleapis.com/auth/devstorage.read_only"],
        )
        # To validate the credentials, it is necessary to make a request to Google Cloud API
        credentials.refresh(Request())
        return True

    except GoogleAuthError as auth_error:
        logger.warning(
            "Google authentication error trying to authenticate GCS secrets: {}",
            auth_error,
        )
        return False

    except Exception as e:
        logger.warning("Unexpected error authenticating GCS secrets: {}", e)
        return False


def _get_authenticator_from_config(storage_type: StorageType) -> Any:
    """Determines which uploader method to use based on storage type"""
    return {
        StorageType.s3.value: _s3_authenticator,
        StorageType.gcs.value: _gcs_authenticator,
    }[storage_type.value]
