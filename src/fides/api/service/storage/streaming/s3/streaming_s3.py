from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING, Any, Optional, Union

from botocore.exceptions import ClientError, ParamValidationError
from fideslang.validation import AnyHttpUrlString
from loguru import logger

from fides.api.common_exceptions import StorageUploadError
from fides.api.schemas.storage.storage import StorageSecrets, StorageSecretsS3
from fides.api.service.storage.s3 import generic_upload_to_s3
from fides.api.service.storage.streaming.schemas import StorageUploadConfig
from fides.api.service.storage.streaming.storage_client_factory import (
    get_storage_client,
)
from fides.api.service.storage.streaming.streaming_storage import StreamingStorage
from fides.api.service.storage.streaming.util import update_storage_secrets

if TYPE_CHECKING:
    from fides.api.models.privacy_request import PrivacyRequest


def upload_to_s3_streaming(
    storage_secrets: Union[StorageSecretsS3, dict[StorageSecrets, Any]],
    data: dict,
    bucket_name: str,
    file_key: str,
    resp_format: str,
    privacy_request: Optional[PrivacyRequest],
    document: Optional[BytesIO],
    auth_method: str,
    max_workers: int = 5,
) -> Optional[AnyHttpUrlString]:
    """Uploads arbitrary data to S3 using production-ready memory-efficient processing.

    This function maintains backward compatibility while using the new cloud-agnostic
    streaming implementation under the hood.

    The production-ready approach includes:
    1. Parallel processing of multiple attachments
    2. Adaptive chunk sizes based on file size
    3. Automatic package splitting for large datasets
    4. Robust error handling and retry logic
    5. Memory usage limited to ~5.6MB regardless of attachment count
    """
    logger.info("Starting production streaming S3 Upload of {}", file_key)

    if privacy_request is None:
        raise ValueError("Privacy request and document must be provided")

    if document is not None:
        if isinstance(storage_secrets, StorageSecretsS3):
            secrets_dict = update_storage_secrets(storage_secrets)
        else:
            secrets_dict = storage_secrets

        _, response = generic_upload_to_s3(
            secrets_dict, bucket_name, file_key, auth_method, document
        )
        return response

    try:
        # Create S3 storage client using the new abstraction
        storage_client = get_storage_client("s3", auth_method, storage_secrets)

    except (ClientError, ParamValidationError) as e:
        logger.error(f"Error getting s3 client: {str(e)}")
        raise StorageUploadError(f"Error getting s3 client: {str(e)}")

    try:
        # Create upload config for the new streaming interface
        upload_config = StorageUploadConfig(
            bucket_name=bucket_name,
            file_key=file_key,
            resp_format=resp_format,
            max_workers=max_workers,
        )

        # Use the new cloud-agnostic streaming implementation
        result = StreamingStorage.upload_to_storage_streaming(
            storage_client,
            data,
            upload_config,
            privacy_request,
            document,
        )

        logger.info("Successfully uploaded streaming archive to S3: {}", file_key)
        return result

    except ClientError as e:
        logger.error("Encountered error while uploading s3 object: {}", e)
        raise StorageUploadError(f"Error uploading to S3: {e}")
    except Exception as e:
        logger.error("Unexpected error during streaming upload: {}", e)
        raise StorageUploadError(f"Unexpected error during streaming upload: {e}")
