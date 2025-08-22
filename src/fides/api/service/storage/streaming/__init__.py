"""Streaming storage module for efficient cloud-to-cloud data transfer."""

from .base_storage_client import BaseStorageClient
from .retry import (
    PermanentError,
    RetryableError,
    RetryConfig,
    TransientError,
    create_retry_config_from_settings,
    is_transient_error,
    retry_cloud_storage_operation,
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
    # Main clients
    "SmartOpenStorageClient",
    "SmartOpenStreamingStorage",
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
    "retry_cloud_storage_operation",
    "create_retry_config_from_settings",
    "is_transient_error",
]
