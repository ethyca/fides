from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

from fideslang.validation import AnyHttpUrlString
from loguru import logger

from fides.api.common_exceptions import StorageUploadError
from fides.api.schemas.storage.storage import StorageSecretsGCS
from fides.api.service.storage.streaming.retry import retry_cloud_storage_operation
from fides.api.service.storage.streaming.schemas import StorageUploadConfig
from fides.api.service.storage.streaming.smart_open_client import SmartOpenStorageClient
from fides.api.service.storage.streaming.smart_open_streaming_storage import (
    SmartOpenStreamingStorage,
)

if TYPE_CHECKING:
    from fides.api.models.privacy_request import PrivacyRequest


@retry_cloud_storage_operation(
    provider="gcs_streaming",
    operation_name="upload_to_gcs_streaming",
    max_retries=2,
    base_delay=2.0,
    max_delay=30.0,
)
def upload_to_gcs_streaming(
    storage_secrets: Union[StorageSecretsGCS, dict[str, Any]],
    data: dict,
    bucket_name: str,
    file_key: str,
    resp_format: str,
    privacy_request: Optional[PrivacyRequest],
    auth_method: str,
    max_workers: int = 5,
) -> Optional[AnyHttpUrlString]:
    """Uploads data to Google Cloud Storage using smart-open streaming for memory efficiency.

    This function uses smart-open for efficient cloud storage operations while maintaining
    our DSR-specific business logic for package splitting and attachment processing.
    """
    logger.info("Starting smart-open streaming GCS Upload of {}", file_key)

    if privacy_request is None:
        raise ValueError("Privacy request must be provided")

    try:
        # Convert to dictionary format for SmartOpenStorageClient
        if hasattr(storage_secrets, "model_dump"):
            # It's a Pydantic model
            storage_secrets_dict = storage_secrets.model_dump()
        else:
            # It's already a dictionary
            storage_secrets_dict = storage_secrets

        storage_client = SmartOpenStorageClient("gcs", storage_secrets_dict)

    except Exception as e:
        logger.error(f"Error creating smart-open GCS client: {str(e)}")
        raise StorageUploadError(f"Error creating smart-open GCS client: {str(e)}")

    try:
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
            document=None,
        )

        logger.info(
            "Successfully uploaded streaming archive to GCS using smart-open: {}",
            file_key,
        )
        return result

    except Exception as e:
        logger.error(
            "Unexpected error during smart-open streaming upload to GCS: {}", e
        )
        raise StorageUploadError(
            f"Unexpected error during smart-open streaming upload to GCS: {e}"
        )
