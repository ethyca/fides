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
        logger.debug("Creating SmartOpenStorageClient with formatted secrets")
        storage_client = SmartOpenStorageClient("s3", auth_method, formatted_secrets)

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


def _process_storage_secrets_input(
    storage_secrets: Union[StorageSecretsS3, dict[StorageSecrets, Any]]  # type: ignore[misc]
) -> dict[str, Any]:
    """Process input and convert to string-keyed dictionary."""
    final_secrets: dict[str, Any] = {}

    logger.debug(
        f"Processing storage secrets input of type: {type(storage_secrets).__name__}"
    )

    if isinstance(storage_secrets, StorageSecretsS3):
        # Convert StorageSecretsS3 model directly to string keys
        for key, value in storage_secrets.model_dump().items():
            if value is not None:
                final_secrets[key] = value
    else:
        # Process dict input, converting enum keys to strings if needed
        for key, value in (storage_secrets or {}).items():  # type: ignore[assignment]
            if isinstance(key, str):
                final_secrets[key] = value
            elif isinstance(key, StorageSecrets):
                final_secrets[key.value] = value

    return final_secrets


def _validate_aws_credentials(final_secrets: dict[str, Any]) -> None:
    """Validate that required AWS credentials are present."""
    has_access_key = (
        "aws_access_key_id" in final_secrets and final_secrets["aws_access_key_id"]
    )
    has_secret_key = (
        "aws_secret_access_key" in final_secrets
        and final_secrets["aws_secret_access_key"]
    )

    # If we have any AWS credentials, we need both for SECRET_KEYS auth
    if has_access_key or has_secret_key:
        if not has_access_key:
            raise ValueError(
                "Missing required AWS credentials for SECRET_KEYS auth: aws_access_key_id. "
                "Storage configuration must include valid AWS access key and secret key."
            )
        if not has_secret_key:
            raise ValueError(
                "Missing required AWS credentials for SECRET_KEYS auth: aws_secret_access_key. "
                "Storage configuration must include valid AWS access key and secret key."
            )
    else:
        # AUTOMATIC authentication - check if region is provided
        has_region = "region_name" in final_secrets and final_secrets["region_name"]

        if not has_region:
            raise ValueError(
                "Missing required region_name for AUTOMATIC authentication. "
                "Storage configuration must include a valid AWS region."
            )


def format_secrets(
    storage_secrets: Union[StorageSecretsS3, dict[StorageSecrets, Any]]  # type: ignore[misc]
) -> dict[str, Any]:
    """
    Returns the correct format for the S3StorageClient.

    This function handles multiple credential formats and processes them through several stages:
    1. Input processing: Accepts either StorageSecretsS3 models (from API) or raw dicts (from database)
    2. Key normalization: Converts all keys to string format for consistency
    3. Default setting: Sets default region if missing (before validation for better automatic auth support)
    4. Validation: Ensures required AWS credentials are present based on auth method
    5. Return: Returns string-keyed dict ready for S3StorageClient

    Input formats:
    - StorageSecretsS3: Used by storage API endpoints (e.g., put_config_secrets)
    - dict[StorageSecrets, Any]: Used by storage models (e.g., StorageConfig.secrets)
    - dict[str, Any]: Used by database queries (e.g., StorageConfig.get_by)

    Authentication methods:
    - SECRET_KEYS: Requires aws_access_key_id, aws_secret_access_key, and region_name
    - AUTOMATIC: Requires only region_name (relies on AWS SDK credential chain)
    - Role assumption: Can be used with either auth method via assume_role_arn

    Output format:
    - dict[str, Any]: Required by S3StorageClient.generate_presigned_url() and other AWS operations

    Returns:
        dict[str, Any]: Credentials with string keys like 'aws_access_key_id'

    Raises:
        ValueError: If required AWS credentials are missing for the chosen auth method
    """
    final_secrets = _process_storage_secrets_input(storage_secrets)
    _validate_aws_credentials(final_secrets)

    return final_secrets
