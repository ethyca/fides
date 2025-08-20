"""Streaming storage module for efficient cloud-to-cloud data transfer."""

from .cloud_storage_client import CloudStorageClient
from .retry import (
    PermanentError,
    RetryableError,
    RetryConfig,
    TransientError,
    create_retry_config_from_settings,
    is_s3_transient_error,
    is_transient_error,
    retry_cloud_storage_operation,
    retry_s3_operation,
    retry_with_backoff,
)
from .schemas import AttachmentInfo, StorageUploadConfig, StreamingBufferConfig
from .storage_client_factory import CloudStorageClientFactory, get_storage_client
from .streaming_storage import (
    split_data_into_packages,
    stream_attachments_to_storage_zip,
    stream_attachments_to_storage_zip_memory_efficient,
    upload_to_storage_streaming,
)

__all__ = [
    "stream_attachments_to_storage_zip",
    "stream_attachments_to_storage_zip_memory_efficient",
    "upload_to_storage_streaming",
    "split_data_into_packages",
    "CloudStorageClient",
    "CloudStorageClientFactory",
    "get_storage_client",
    "StorageUploadConfig",
    "StreamingBufferConfig",
    "AttachmentInfo",
    # Retry utilities
    "RetryConfig",
    "RetryableError",
    "TransientError",
    "PermanentError",
    "retry_with_backoff",
    "retry_s3_operation",
    "retry_cloud_storage_operation",
    "create_retry_config_from_settings",
    "is_transient_error",
    "is_s3_transient_error",
]
