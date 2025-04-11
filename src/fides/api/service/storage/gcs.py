from typing import Dict, Optional

from google.cloud.storage import Client  # type: ignore
from google.oauth2 import service_account
from loguru import logger

from fides.api.common_exceptions import StorageUploadError
from fides.api.schemas.storage.storage import GCSAuthMethod


def get_gcs_client(
    auth_method: str,
    storage_secrets: Optional[Dict],
) -> Client:
    """
    Abstraction to retrieve a GCS client using secrets.
    """
    if auth_method == GCSAuthMethod.ADC.value:
        storage_client = Client()

    elif auth_method == GCSAuthMethod.SERVICE_ACCOUNT_KEYS.value:
        if not storage_secrets:
            err_msg = "Storage secrets not found for Google Cloud Storage."
            logger.warning(err_msg)
            raise StorageUploadError(err_msg)

        credentials = service_account.Credentials.from_service_account_info(
            dict(storage_secrets)
        )
        storage_client = Client(credentials=credentials)

    else:
        logger.error("Google Cloud Storage auth method not supported: {}", auth_method)
        raise ValueError(
            f"Google Cloud Storage auth method not supported: {auth_method}"
        )

    return storage_client
