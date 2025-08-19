from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING, Any, Callable, Optional, Tuple

from botocore.exceptions import ClientError, ParamValidationError
from fideslang.validation import AnyHttpUrlString
from loguru import logger

from fides.api.common_exceptions import StorageUploadError
from fides.api.schemas.storage.storage import StorageSecrets
from fides.api.service.storage.s3 import generic_upload_to_s3
from fides.api.service.storage.streaming.schemas import ProcessingMetrics
from fides.api.service.storage.streaming.storage_client_factory import (
    get_storage_client,
)
from fides.api.service.storage.streaming.streaming_storage import (
    upload_to_storage_streaming,
)

if TYPE_CHECKING:
    from fides.api.models.privacy_request import PrivacyRequest


def upload_to_s3_streaming(
    storage_secrets: dict[StorageSecrets, Any],
    data: dict,
    bucket_name: str,
    file_key: str,
    resp_format: str,
    privacy_request: Optional[PrivacyRequest],
    document: Optional[BytesIO],
    auth_method: str,
    max_workers: int = 5,
    progress_callback: Optional[Callable[[ProcessingMetrics], None]] = None,
) -> Tuple[Optional[AnyHttpUrlString], ProcessingMetrics]:
    """Uploads arbitrary data to S3 using production-ready memory-efficient processing.

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
    logger.info("Starting production streaming S3 Upload of {}", file_key)

    if privacy_request is None and document is not None:
        _, response = generic_upload_to_s3(
            storage_secrets, bucket_name, file_key, auth_method, document
        )
        # Return empty metrics for backward compatibility
        empty_metrics = ProcessingMetrics()
        return response, empty_metrics

    if privacy_request is None:
        raise ValueError("Privacy request must be provided")

    try:
        # Create S3 storage client using the new abstraction
        storage_client = get_storage_client("s3", auth_method, storage_secrets)

    except (ClientError, ParamValidationError) as e:
        logger.error(f"Error getting s3 client: {str(e)}")
        raise StorageUploadError(f"Error getting s3 client: {str(e)}")

    try:
        # Use the new cloud-agnostic streaming implementation
        result = upload_to_storage_streaming(
            storage_client,
            data,
            bucket_name,
            file_key,
            resp_format,
            privacy_request,
            document,
            max_workers,
            progress_callback,
        )

        logger.info("Successfully uploaded streaming archive to S3: {}", file_key)
        return result

    except ClientError as e:
        logger.error("Encountered error while uploading s3 object: {}", e)
        raise StorageUploadError(f"Error uploading to S3: {e}")
    except Exception as e:
        logger.error("Unexpected error during streaming upload: {}", e)
        raise StorageUploadError(f"Unexpected error during streaming upload: {e}")


def upload_to_s3_streaming_advanced(
    storage_secrets: dict[StorageSecrets, Any],
    data: dict,
    bucket_name: str,
    file_key: str,
    resp_format: str,
    privacy_request: Optional[PrivacyRequest],
    document: Optional[BytesIO],
    auth_method: str,
    max_workers: int = 5,
    progress_callback: Optional[Callable[[ProcessingMetrics], None]] = None,
) -> Tuple[Optional[AnyHttpUrlString], ProcessingMetrics]:
    """Wrapper function that delegates to the main streaming implementation.

    This function maintains backward compatibility by calling upload_to_s3_streaming.
    The actual streaming logic is implemented in the new cloud-agnostic module.

    Args:
        storage_secrets: S3 storage secrets
        data: The data to upload
        bucket_name: Name of the S3 bucket
        file_key: Key of the file in the bucket
        resp_format: Response format (json, csv, html)
        privacy_request: Privacy request object
        document: Optional document (for backward compatibility)
        auth_method: Authentication method for S3
        max_workers: Number of parallel workers for attachment processing
        progress_callback: Optional callback for progress updates

    Returns:
        Tuple of (presigned_url, metrics) where metrics contains processing information

    Raises:
        StorageUploadError: If upload fails
        ValueError: If privacy request is not provided
    """
    logger.info("Starting advanced streaming S3 Upload of {}", file_key)

    if privacy_request is None and document is not None:
        _, response = generic_upload_to_s3(
            storage_secrets, bucket_name, file_key, auth_method, document
        )
        # Return empty metrics for backward compatibility
        empty_metrics = ProcessingMetrics()
        return response, empty_metrics

    if privacy_request is None:
        raise ValueError("Privacy request must be provided")

    try:
        # Use the main streaming function for all formats
        return upload_to_s3_streaming(
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
