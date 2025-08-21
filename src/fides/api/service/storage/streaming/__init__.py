"""Streaming storage module for efficient cloud-to-cloud data transfer."""

from .azure.azure_storage_client import AzureStorageClient
from .base_storage_client import BaseStorageClient
from .gcs.gcs_storage_client import GCSStorageClient
from .gcs.streaming_gcs import upload_to_gcs_streaming
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
from .s3.s3_storage_client import S3StorageClient
from .schemas import AttachmentInfo, StorageUploadConfig, StreamingBufferConfig
from .smart_open_client import SmartOpenStorageClient
from .smart_open_streaming_storage import SmartOpenStreamingStorage
from .storage_client_factory import StorageClientFactory

__all__ = [
    # Base classes and interfaces
    "BaseStorageClient",
    "StorageClientFactory",
    # Provider-specific clients
    "S3StorageClient",
    "GCSStorageClient",
    "AzureStorageClient",
    # Main clients
    "SmartOpenStorageClient",
    "SmartOpenStreamingStorage",
    # Legacy streaming functions
    "upload_to_gcs_streaming",
    # Schemas
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
