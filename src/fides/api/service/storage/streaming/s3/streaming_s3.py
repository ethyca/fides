from __future__ import annotations

from io import BytesIO
from typing import Any, Optional, Union

from fideslang.validation import AnyHttpUrlString
from loguru import logger

from fides.api.common_exceptions import StorageUploadError
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.storage.storage import StorageSecrets, StorageSecretsS3
from fides.api.service.storage.s3 import generic_upload_to_s3
from fides.api.service.storage.streaming.retry import retry_cloud_storage_operation
from fides.api.service.storage.streaming.schemas import StorageUploadConfig
from fides.api.service.storage.streaming.smart_open_client import SmartOpenStorageClient
from fides.api.service.storage.streaming.smart_open_streaming_storage import (
    SmartOpenStreamingStorage,
)


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
    privacy_request: PrivacyRequest,
    document: Optional[BytesIO],
    auth_method: str,
    max_workers: int = 5,
) -> Optional[AnyHttpUrlString]:
    """Uploads arbitrary data to S3 using smart-open streaming for memory efficiency.

    This function now uses smart-open for efficient cloud storage operations while maintaining
    our DSR-specific business logic for package splitting and attachment processing.
    """
    formatted_secrets = format_secrets(storage_secrets)

    if document is not None:
        _, response = generic_upload_to_s3(
            formatted_secrets,  # type: ignore[arg-type]
            bucket_name,
            file_key,
            auth_method,
            document,
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

        logger.debug(
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
) -> dict[str, Any]:
    """
    Returns the correct format for the S3StorageClient.

    This function handles multiple credential formats and processes them through several stages:
    1. Input processing: Accepts either StorageSecretsS3 models (from API) or raw dicts (from database)
    2. Key normalization: Converts all keys to string format for consistency
    3. Default setting: Sets default region if missing
    4. Validation: Ensures all required AWS credentials are present
    5. Return: Returns string-keyed dict ready for S3StorageClient

    Input formats:
    - StorageSecretsS3: Used by storage API endpoints (e.g., put_config_secrets)
    - dict[StorageSecrets, Any]: Used by storage models (e.g., StorageConfig.secrets)
    - dict[str, Any]: Used by database queries (e.g., StorageConfig.get_by)

    Output format:
    - dict[str, Any]: Required by S3StorageClient.generate_presigned_url() and other AWS operations

    Returns:
        dict[str, Any]: Credentials with string keys like 'aws_access_key_id'

    Raises:
        ValueError: If required AWS credentials are missing
    """
    logger.debug("format_secrets called with type: {}", type(storage_secrets).__name__)

    # Stage 1: Process input and create final format directly
    # We'll build the final string-keyed dictionary from the start
    final_secrets: dict[str, Any] = {}

    if isinstance(storage_secrets, StorageSecretsS3):
        # Convert StorageSecretsS3 model directly to string keys
        # This handles input from storage API endpoints (e.g., put_config_secrets)
        for key, value in storage_secrets.model_dump().items():
            if value is not None:
                final_secrets[key] = value
    else:
        # Process dict input, converting enum keys to strings if needed
        # This handles input from StorageConfig.secrets (database storage)
        for key, value in (storage_secrets or {}).items():
            if isinstance(key, str):
                final_secrets[key] = value
            elif isinstance(key, StorageSecrets):
                # Convert enum key to string key
                final_secrets[key.value] = value  # type: ignore[assignment]

    # Stage 2: Set default region if missing
    # AWS S3 operations require a region, so we provide a sensible default
    # This is needed for S3StorageClient.generate_presigned_url() and other AWS calls
    if "region_name" not in final_secrets or not final_secrets["region_name"]:
        logger.debug("Setting default region to 'us-east-1'")
        final_secrets["region_name"] = "us-east-1"

    # Stage 3: Validate required credentials
    # Ensure all necessary AWS credentials are present before proceeding
    # These are required by S3StorageClient and AWS SDK operations
    required_secrets = ["aws_access_key_id", "aws_secret_access_key", "region_name"]

    missing_secrets = [
        secret
        for secret in required_secrets
        if secret not in final_secrets or not final_secrets[secret]
    ]

    if missing_secrets:
        raise ValueError(
            f"Missing required AWS credentials: {missing_secrets}. "
            "Storage configuration must include valid AWS access key, secret key, and region."
        )

    logger.debug(
        "format_secrets completed successfully with {} keys", len(final_secrets)
    )
    return final_secrets
