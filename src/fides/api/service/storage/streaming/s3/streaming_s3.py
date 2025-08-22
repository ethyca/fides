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
    logger.info("Storage secrets type: {}", type(storage_secrets))
    logger.debug("Storage secrets content: {}", storage_secrets)

    if privacy_request is None:
        raise ValueError("Privacy request must be provided")

    if isinstance(storage_secrets, StorageSecretsS3):
        logger.info("Processing StorageSecretsS3 object")
        secrets_dict = update_storage_secrets_s3(storage_secrets)
    else:
        logger.info("Processing dict[StorageSecrets, Any] object")
        # Convert dict[StorageSecrets, Any] to dict[str, Any] for SmartOpenStorageClient
        secrets_dict = update_storage_secrets_s3(storage_secrets)

    if document is not None:
        # Convert to dict[StorageSecrets, Any] for generic_upload_to_s3 compatibility
        generic_secrets = convert_to_storage_secrets_format(storage_secrets)
        _, response = generic_upload_to_s3(
            generic_secrets, bucket_name, file_key, auth_method, document
        )
        return response

    try:
        # Create smart-open S3 storage client directly
        storage_client = SmartOpenStorageClient("s3", secrets_dict)

    except Exception as e:
        logger.error(f"Error creating smart-open S3 client: {str(e)}")
        raise StorageUploadError(f"Error creating smart-open S3 client: {str(e)}")

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


def update_storage_secrets_s3(
    storage_secrets: Union[StorageSecretsS3, dict[StorageSecrets, Any]]
) -> dict[str, Any]:
    """
    Updates the storage secrets to the expected format for SmartOpenStorageClient.
    Returns dict[str, Any] for compatibility with smart-open.
    """
    logger.info("Processing storage secrets of type: {}", type(storage_secrets))
    logger.debug("Storage secrets content: {}", storage_secrets)

    if not isinstance(storage_secrets, dict):
        # Check if it's a StorageSecretsS3-like object (including docs versions)
        if hasattr(storage_secrets, "model_dump"):
            try:
                # Preserve all values including None for test compatibility
                secrets_dict = storage_secrets.model_dump()
                logger.info(
                    "Converted StorageSecretsS3 object to dict: {}", secrets_dict
                )
                return secrets_dict
            except AttributeError:
                logger.error("StorageSecretsS3 object missing model_dump method")
                raise ValueError(
                    "Storage secrets must be of type StorageSecretsS3, or dict[StorageSecrets, Any]"
                )
        else:
            logger.error("Storage secrets is not a dict and has no model_dump method")
            raise ValueError(
                "Storage secrets must be of type StorageSecretsS3, or dict[StorageSecrets, Any]"
            )

    # Handle the case where secrets come from database as dict[str, Any]
    # Check if keys are string values of StorageSecrets enum
    if all(isinstance(k, str) for k in storage_secrets.keys()):
        # Keys are already strings, check if they match StorageSecrets enum values
        storage_secret_values = {secret.value for secret in StorageSecrets}
        if all(k in storage_secret_values for k in storage_secrets.keys()):
            logger.info(
                "Storage secrets already in correct string format for SmartOpenStorageClient"
            )
            return storage_secrets
        else:
            logger.warning(
                "Some storage secret keys don't match StorageSecrets enum values: {}",
                [k for k in storage_secrets.keys() if k not in storage_secret_values],
            )
            # Still return as-is since this might be a valid case

    # Handle the case where keys are StorageSecrets enum objects
    try:
        if all(isinstance(k, StorageSecrets) for k in storage_secrets.keys()):
            # Convert StorageSecrets enum keys to string keys for SmartOpenStorageClient
            converted_secrets = {}
            for k, v in storage_secrets.items():
                converted_secrets[k.value] = v
            logger.info("Converted StorageSecrets enum keys to string keys")
            return converted_secrets
    except AttributeError:
        logger.error("Error checking if keys are StorageSecrets enum objects")
        raise ValueError(
            "Storage secrets must be of type StorageSecretsS3, or dict[StorageSecrets, Any]"
        )

    # If we get here, the keys are neither StorageSecrets enum objects nor valid string values
    logger.error(
        "Storage secrets keys are neither StorageSecrets enum objects nor valid string values"
    )
    logger.error("Keys found: {}", list(storage_secrets.keys()))
    logger.error("Expected keys: {}", [secret.value for secret in StorageSecrets])
    raise ValueError(
        "Storage secrets must be of type StorageSecretsS3, or dict[StorageSecrets, Any]"
    )


def convert_to_storage_secrets_format(
    storage_secrets: Union[StorageSecretsS3, dict[StorageSecrets, Any]]
) -> dict[StorageSecrets, Any]:
    """
    Converts storage secrets to the format expected by generic_upload_to_s3.
    Returns dict[StorageSecrets, Any] for compatibility with existing S3 functions.
    """
    if isinstance(storage_secrets, StorageSecretsS3):
        # Convert StorageSecretsS3 to dict[StorageSecrets, Any]
        secrets_dict = storage_secrets.model_dump()
        converted_secrets = {}
        for k, v in secrets_dict.items():
            if v is not None:
                # Map string keys back to StorageSecrets enum keys
                for enum_key in StorageSecrets:
                    if enum_key.value == k:
                        converted_secrets[enum_key] = v
                        break
        return converted_secrets

    # Already in the correct format
    return storage_secrets
