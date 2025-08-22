from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING, Any, Optional, Union

from fideslang.validation import AnyHttpUrlString
from loguru import logger

from fides.api.common_exceptions import StorageUploadError
from fides.api.schemas.storage.storage import StorageSecrets, StorageSecretsS3
from fides.api.service.storage.s3 import generic_upload_to_s3
from fides.api.service.storage.streaming.retry import retry_cloud_storage_operation
from fides.api.service.storage.streaming.schemas import StorageUploadConfig
from fides.api.service.storage.streaming.smart_open_client import SmartOpenStorageClient
from fides.api.service.storage.streaming.smart_open_streaming_storage import (
    SmartOpenStreamingStorage,
)

if TYPE_CHECKING:
    from fides.api.models.privacy_request import PrivacyRequest


@retry_cloud_storage_operation(
    provider="s3_streaming",
    operation_name="upload_to_s3_streaming",
    max_retries=2,
    base_delay=2.0,
    max_delay=30.0,
)
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
    """Uploads arbitrary data to S3 using smart-open streaming for memory efficiency.

    This function now uses smart-open for efficient cloud storage operations while maintaining
    our DSR-specific business logic for package splitting and attachment processing.
    """
    logger.info("Starting smart-open streaming S3 Upload of {}", file_key)

    if privacy_request is None:
        raise ValueError("Privacy request must be provided")

    formatted_secrets = format_secrets(storage_secrets)

    if document is not None:
        _, response = generic_upload_to_s3(
            formatted_secrets, bucket_name, file_key, auth_method, document
        )
        return response

    try:
        storage_client = SmartOpenStorageClient("s3", formatted_secrets)

        # Create upload config for the streaming interface
        upload_config = StorageUploadConfig(
            bucket_name=bucket_name,
            file_key=file_key,
            resp_format=resp_format,
            max_workers=max_workers,
        )

        # Use the smart-open streaming implementation
        streaming_storage = SmartOpenStreamingStorage(storage_client)
        result = streaming_storage.upload_to_storage_streaming(
            data,
            upload_config,
            privacy_request,
            document,
        )

        logger.info(
            "Successfully uploaded streaming archive to S3 using smart-open: {}",
            file_key,
        )
        return result

    except Exception as e:
        logger.error("Unexpected error during smart-open streaming upload: {}", e)
        raise StorageUploadError(
            f"Unexpected error during smart-open streaming upload: {e}"
        )


def format_secrets(
    storage_secrets: Union[StorageSecretsS3, dict[StorageSecrets, Any]]
) -> dict[StorageSecrets, Any]:
    """
    Converts StorageSecretsS3 to dict[StorageSecrets, Any] with enum keys.
    """
    secrets_for_streaming: dict[StorageSecrets, Any] = {}
    if isinstance(storage_secrets, StorageSecretsS3):
        for key, value in storage_secrets.model_dump().items():
            if value is not None:
                for enum_key in StorageSecrets:
                    if enum_key.value == key:
                        secrets_for_streaming[enum_key] = value
                        break
        return secrets_for_streaming
    return {k: v for k, v in storage_secrets.items() if isinstance(k, StorageSecrets)}
