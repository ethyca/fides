"""
Storage service module.

This module provides storage backends for file operations including S3, GCS,
and local filesystem storage.

Recommended usage (new code):
    Use the StorageProvider interface via the factory:

        from fides.api.service.storage.providers import StorageProviderFactory

        provider = StorageProviderFactory.create(storage_config)
        provider.upload(bucket, key, data)
        provider.download(bucket, key)
        provider.delete(bucket, key)

Legacy usage (deprecated):
    Direct function calls are deprecated but still supported:

        from fides.api.service.storage.s3 import generic_upload_to_s3
        from fides.api.service.storage.gcs import get_gcs_client
"""

# Re-export the providers module for convenience
from fides.api.service.storage.providers import (
    GCSStorageProvider,
    LocalStorageProvider,
    ObjectInfo,
    S3StorageProvider,
    StorageProvider,
    StorageProviderFactory,
    UploadResult,
)

__all__ = [
    # Provider interface
    "StorageProvider",
    "StorageProviderFactory",
    "UploadResult",
    "ObjectInfo",
    # Provider implementations
    "S3StorageProvider",
    "GCSStorageProvider",
    "LocalStorageProvider",
]
