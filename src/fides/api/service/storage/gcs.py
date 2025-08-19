from io import BytesIO
from typing import IO, Any, Dict, Optional, Tuple

from fideslang.validation import AnyHttpUrlString
from google.cloud.storage import Blob, Client  # type: ignore
from google.oauth2 import service_account
from loguru import logger

from fides.api.common_exceptions import StorageUploadError
from fides.api.schemas.storage.storage import GCSAuthMethod


def get_gcs_client(
    auth_method: str,
    storage_secrets: Optional[dict],
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


def get_gcs_blob(
    auth_method: str, storage_secrets: Optional[dict], bucket_name: str, file_key: str
) -> Blob:
    try:
        storage_client = get_gcs_client(auth_method, storage_secrets)
        bucket = storage_client.bucket(bucket_name)
        return bucket.blob(file_key)
    except Exception as e:
        logger.error(f"Error getting GCS blob: {str(e)}")
        raise e


def generic_upload_to_gcs(
    storage_secrets: Dict[str, Any],
    bucket_name: str,
    file_key: str,
    auth_method: str,
    document: IO[bytes],
) -> Tuple[int, AnyHttpUrlString]:
    """
    Uploads file-like objects to GCS.
    Handles both small and large uploads.

    :param storage_secrets: GCS storage secrets
    :param bucket_name: Name of the GCS bucket
    :param file_key: Key of the file in the bucket
    :param auth_method: Authentication method for GCS
    :param document: File contents to upload
    """
    logger.info("Starting GCS Upload of {}", file_key)

    # Validate that the document is a file-like object
    if not hasattr(document, "read") or not hasattr(document, "seek"):
        raise TypeError(
            f"The 'document' parameter must be a file-like object supporting 'read' and 'seek'. "
            f"Received: {type(document)}, {document}"
        )

    # Ensure the file pointer is at the beginning
    try:
        document.seek(0)
    except Exception as e:
        raise ValueError(f"Failed to reset file pointer for document: {e}")

    try:
        blob = get_gcs_blob(auth_method, storage_secrets, bucket_name, file_key)

        # Upload the file content
        blob.upload_from_file(document)

        # Get file size
        blob.reload()
        file_size = blob.size

        # Generate a signed URL for the uploaded file
        signed_url = blob.generate_signed_url(
            version="v4", expiration=3600, method="GET"  # 1 hour default
        )

        logger.info("Successfully uploaded file {} to bucket {}", file_key, bucket_name)
        return file_size, signed_url

    except Exception as e:
        logger.error(f"Failed to upload file {file_key} to bucket {bucket_name}: {e}")
        raise StorageUploadError(
            f"Failed to upload file {file_key} to bucket {bucket_name}: {e}"
        )
