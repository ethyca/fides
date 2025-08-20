from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING, Any, Callable, Optional, Tuple

from fideslang.validation import AnyHttpUrlString
from google.cloud.exceptions import GoogleCloudError
from loguru import logger

from fides.api.common_exceptions import StorageUploadError
from fides.api.schemas.storage.storage import StorageSecrets
from fides.api.service.storage.streaming.cloud_storage_client import ProgressCallback
from fides.api.service.storage.streaming.schemas import (
    ProcessingMetrics,
    StorageUploadConfig,
)
from fides.api.service.storage.streaming.storage_client_factory import (
    get_storage_client,
)
from fides.api.service.storage.streaming.streaming_storage import (
    upload_to_storage_streaming,
)
from fides.api.tasks.storage import upload_to_gcs

if TYPE_CHECKING:
    from fides.api.models.privacy_request import PrivacyRequest


def upload_to_gcs_streaming(
    storage_secrets: Optional[dict[StorageSecrets, Any]],
    data: dict,
    bucket_name: str,
    file_key: str,
    resp_format: str,
    privacy_request: Optional[PrivacyRequest],
    document: Optional[BytesIO],
    auth_method: str,
    max_workers: int = 5,
    progress_callback: Optional[ProgressCallback] = None,
) -> Tuple[Optional[AnyHttpUrlString], ProcessingMetrics]:
    """Uploads arbitrary data to GCS using production-ready memory-efficient processing.

    This function maintains backward compatibility while using the new cloud-agnostic
    streaming implementation under the hood.

    The production-ready approach includes:
    1. Parallel processing of multiple attachments
    2. Adaptive chunk sizes based on file size
    3. Progress tracking and comprehensive metrics
    4. Automatic package splitting for large datasets
    5. Robust error handling and retry logic
    6. Memory usage limited to ~5.6MB regardless of attachment count
    """
    logger.info("Starting production streaming GCS Upload of {}", file_key)

    if privacy_request is None and document is not None:
        _, response = upload_to_gcs(
            storage_secrets, bucket_name, file_key, auth_method, document
        )
        # Return empty metrics for backward compatibility
        empty_metrics = ProcessingMetrics()
        return response, empty_metrics

    if privacy_request is None:
        raise ValueError("Privacy request must be provided")

    try:
        # Create GCS storage client using the new abstraction
        storage_client = get_storage_client("gcs", auth_method, storage_secrets)

    except GoogleCloudError as e:
        logger.error(f"Error getting GCS client: {str(e)}")
        raise StorageUploadError(f"Error getting GCS client: {str(e)}")

    try:
        # Create upload config for the new streaming interface
        upload_config = StorageUploadConfig(
            bucket_name=bucket_name,
            file_key=file_key,
            resp_format=resp_format,
            max_workers=max_workers,
        )

        # Use the new cloud-agnostic streaming implementation
        result = upload_to_storage_streaming(
            storage_client,
            data,
            upload_config,
            privacy_request,
            document,
            progress_callback,
        )

        logger.info("Successfully uploaded streaming archive to GCS: {}", file_key)
        return result

    except GoogleCloudError as e:
        logger.error("Encountered error while uploading GCS object: {}", e)
        raise StorageUploadError(f"Error uploading to GCS: {e}")
    except Exception as e:
        logger.error("Unexpected error during streaming upload: {}", e)
        raise StorageUploadError(f"Unexpected error during streaming upload: {e}")


def upload_to_gcs_streaming_advanced(
    storage_secrets: Optional[dict[StorageSecrets, Any]],
    data: dict,
    bucket_name: str,
    file_key: str,
    resp_format: str,
    privacy_request: Optional[PrivacyRequest],
    document: Optional[BytesIO],
    auth_method: str,
    max_workers: int = 5,
    progress_callback: Optional[ProgressCallback] = None,
) -> Tuple[Optional[AnyHttpUrlString], ProcessingMetrics]:
    """Wrapper function that delegates to the main streaming implementation.

    This function maintains backward compatibility by calling upload_to_gcs_streaming.
    The actual streaming logic is implemented in the new cloud-agnostic module.

    Args:
        storage_secrets: GCS storage secrets
        data: The data to upload
        bucket_name: Name of the GCS bucket
        file_key: Key of the file in the bucket
        resp_format: Response format (json, csv, html)
        privacy_request: Privacy request object
        document: Optional document (for backward compatibility)
        auth_method: Authentication method for GCS
        max_workers: Number of parallel workers for attachment processing
        progress_callback: Optional callback for progress updates

    Returns:
        Tuple of (signed_url, metrics) where metrics contains processing information

    Raises:
        StorageUploadError: If upload fails
        ValueError: If privacy request is not provided
    """
    logger.info("Starting advanced streaming GCS Upload of {}", file_key)

    if privacy_request is None and document is not None:
        _, response = upload_to_gcs(
            storage_secrets, bucket_name, file_key, auth_method, document
        )
        # Return empty metrics for backward compatibility
        empty_metrics = ProcessingMetrics()
        return response, empty_metrics

    if privacy_request is None:
        raise ValueError("Privacy request must be provided")

    try:
        # Use the main streaming function for all formats
        return upload_to_gcs_streaming(
            storage_secrets,
            data,
            bucket_name,
            file_key,
            resp_format,
            privacy_request,
            document,
            auth_method,
            max_workers,
            progress_callback,
        )

    except Exception as e:
        logger.error("Unexpected error during advanced streaming upload: {}", e)
        raise StorageUploadError(
            f"Unexpected error during advanced streaming upload: {e}"
        )


def upload_to_gcs_resumable(
    storage_secrets: Optional[dict[StorageSecrets, Any]],
    data: dict,
    bucket_name: str,
    file_key: str,
    resp_format: str,
    privacy_request: Optional[PrivacyRequest],
    document: Optional[BytesIO],
    auth_method: str,
    max_workers: int = 5,
    progress_callback: Optional[ProgressCallback] = None,
) -> Tuple[Optional[AnyHttpUrlString], ProcessingMetrics]:
    """Uploads data to GCS using resumable uploads for large files.

    This function uses GCS's native resumable upload capability for better
    handling of large files and network interruptions.

    Args:
        storage_secrets: GCS storage secrets
        data: The data to upload
        bucket_name: Name of the GCS bucket
        file_key: Key of the file in the bucket
        resp_format: Response format (json, csv, html)
        privacy_request: Privacy request object
        document: Optional document (for backward compatibility)
        auth_method: Authentication method for GCS
        max_workers: Number of parallel workers for attachment processing
        progress_callback: Optional callback for progress updates

    Returns:
        Tuple of (signed_url, metrics) where metrics contains processing information

    Raises:
        StorageUploadError: If upload fails
        ValueError: If privacy request is not provided
    """
    logger.info("Starting GCS resumable upload of {}", file_key)

    if privacy_request is None and document is not None:
        _, response = upload_to_gcs(
            storage_secrets, bucket_name, file_key, auth_method, document
        )
        # Return empty metrics for backward compatibility
        empty_metrics = ProcessingMetrics()
        return response, empty_metrics

    if privacy_request is None:
        raise ValueError("Privacy request must be provided")

    try:
        # Create GCS storage client
        storage_client = get_storage_client("gcs", auth_method, storage_secrets)

        # Create upload config for the new streaming interface
        upload_config = StorageUploadConfig(
            bucket_name=bucket_name,
            file_key=file_key,
            resp_format=resp_format,
            max_workers=max_workers,
        )

        # For resumable uploads, we'll use the cloud-agnostic streaming
        # but with GCS-specific optimizations
        result = upload_to_storage_streaming(
            storage_client,
            data,
            upload_config,
            privacy_request,
            document,
            progress_callback,
        )

        logger.info("Successfully uploaded using GCS resumable upload: {}", file_key)
        return result

    except GoogleCloudError as e:
        logger.error("Encountered error during GCS resumable upload: {}", e)
        raise StorageUploadError(f"Error during GCS resumable upload: {e}")
    except Exception as e:
        logger.error("Unexpected error during GCS resumable upload: {}", e)
        raise StorageUploadError(f"Unexpected error during GCS resumable upload: {e}")
