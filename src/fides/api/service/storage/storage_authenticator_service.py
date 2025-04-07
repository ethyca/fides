from typing import Any, Dict, Union

from botocore.exceptions import ClientError
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from loguru import logger

from fides.api.schemas.storage.storage import (
    SUPPORTED_STORAGE_SECRETS,
    AWSAuthMethod,
    StorageSecrets,
    StorageType,
)
from fides.api.util.aws_util import get_aws_session


def secrets_are_valid(
    secrets: SUPPORTED_STORAGE_SECRETS,
    storage_type: Union[StorageType, str],
) -> bool:
    """Authenticates upload destination with appropriate upload method"""
    if not isinstance(storage_type, StorageType):
        # try to coerce into an enum
        try:
            storage_type = StorageType[storage_type]
        except KeyError:
            raise ValueError(
                "storage_type argument must be a valid StorageType enum member."
            )
    uploader: Any = _get_authenticator_from_config(storage_type)
    return uploader(secrets)


def _s3_authenticator(secrets: Dict[StorageSecrets, Any]) -> bool:
    """Authenticates secrets for s3, returns true if secrets are valid"""
    try:
        get_aws_session(AWSAuthMethod.SECRET_KEYS.value, secrets.model_dump(mode="json"))  # type: ignore
        return True
    except ClientError:
        return False


def _gcs_authenticator(secrets: Dict) -> bool:
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
