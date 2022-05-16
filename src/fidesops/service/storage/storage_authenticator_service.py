import logging
from typing import Any

from botocore.exceptions import ClientError
from requests import RequestException

from fidesops.schemas.storage.storage import (
    SUPPORTED_STORAGE_SECRETS,
    StorageSecretsOnetrust,
    StorageSecretsS3,
    StorageType,
)
from fidesops.util.storage_authenticator import (
    get_onetrust_access_token,
    get_s3_session,
)

logger = logging.getLogger(__name__)


def secrets_are_valid(
    secrets: SUPPORTED_STORAGE_SECRETS,
    storage_type: StorageType,
) -> bool:
    """Authenticates upload destination with appropriate upload method"""
    uploader: Any = _get_authenticator_from_config(storage_type)
    return uploader(secrets)


def _s3_authenticator(secrets: StorageSecretsS3) -> bool:
    """Authenticates secrets for s3, returns true if secrets are valid"""
    try:
        get_s3_session(
            aws_access_key_id=secrets.aws_access_key_id,
            aws_secret_access_key=secrets.aws_secret_access_key,
        )
        return True
    except ClientError:
        return False


def _onetrust_authenticator(secrets: StorageSecretsOnetrust) -> bool:
    """Authenticates secrets for OneTrust, returns true if secrets are valid"""
    try:
        access_token = get_onetrust_access_token(
            client_id=secrets.onetrust_client_id,
            client_secret=secrets.onetrust_client_secret,
            hostname=secrets.onetrust_hostname,
        )
        return bool(access_token)
    except RequestException:
        return False


def _get_authenticator_from_config(storage_type: StorageType) -> Any:
    """Determines which uploader method to use based on storage type"""
    return {
        StorageType.s3.value: _s3_authenticator,
        StorageType.onetrust.value: _onetrust_authenticator,
    }[storage_type.value]
