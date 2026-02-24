"""
Storage providers module.

This module provides a unified interface for all storage backends (S3, GCS, Local)
following the Strategy and Factory design patterns.

Usage:
    from fides.api.service.storage.providers import StorageProviderFactory

    # Create provider from StorageConfig
    provider = StorageProviderFactory.create(storage_config)

    # Use the provider
    result = provider.upload(bucket, key, data)
    content = provider.download(bucket, key)
    provider.delete(bucket, key)
"""

from fides.api.service.storage.providers.base import (
    ObjectInfo,
    StorageProvider,
    UploadResult,
)
from fides.api.service.storage.providers.factory import StorageProviderFactory
from fides.api.service.storage.providers.gcs_provider import GCSStorageProvider
from fides.api.service.storage.providers.local_provider import LocalStorageProvider
from fides.api.service.storage.providers.s3_provider import S3StorageProvider

__all__ = [
    # Base interface
    "StorageProvider",
    "UploadResult",
    "ObjectInfo",
    # Factory
    "StorageProviderFactory",
    # Provider implementations
    "S3StorageProvider",
    "GCSStorageProvider",
    "LocalStorageProvider",
]
