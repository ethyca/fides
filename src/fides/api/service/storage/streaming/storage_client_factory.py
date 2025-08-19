from __future__ import annotations

from typing import Any, Dict, Optional

from loguru import logger

from fides.api.service.storage.streaming.cloud_storage_client import CloudStorageClient
from fides.api.service.storage.streaming.s3_storage_client import create_s3_storage_client
from fides.api.service.storage.streaming.gcs_storage_client import create_gcs_storage_client


class CloudStorageClientFactory:
    """Factory for creating cloud storage clients based on storage type and configuration"""

    @staticmethod
    def create_storage_client(
        storage_type: str,
        auth_method: str,
        storage_secrets: Optional[Dict[str, Any]] = None
    ) -> CloudStorageClient:
        """Create a storage client based on the storage type"""

        if storage_type.lower() == "s3":
            if storage_secrets is None:
                raise ValueError("Storage secrets are required for S3")
            return create_s3_storage_client(auth_method, storage_secrets)

        elif storage_type.lower() in ["gcs", "gcp", "google"]:
            # GCS streaming not yet implemented - basic client only
            # The CloudStorageClient interface is ready for future streaming support
            return create_gcs_storage_client(auth_method, storage_secrets)

        else:
            raise ValueError(f"Unsupported storage type: {storage_type}")

    @staticmethod
    def create_storage_client_from_config(
        storage_config: Dict[str, Any]
    ) -> CloudStorageClient:
        """Create a storage client from a configuration dictionary"""

        storage_type = storage_config.get("type", "s3")
        auth_method = storage_config.get("auth_method", "automatic")
        storage_secrets = storage_config.get("secrets")

        logger.info("Creating storage client for type: {}", storage_type)

        return CloudStorageClientFactory.create_storage_client(
            storage_type=storage_type,
            auth_method=auth_method,
            storage_secrets=storage_secrets
        )


# Convenience function for backward compatibility
def get_storage_client(
    storage_type: str,
    auth_method: str,
    storage_secrets: Optional[Dict[str, Any]] = None
) -> CloudStorageClient:
    """Convenience function to create a storage client"""
    return CloudStorageClientFactory.create_storage_client(
        storage_type, auth_method, storage_secrets
    )
