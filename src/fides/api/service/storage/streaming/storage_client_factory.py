from __future__ import annotations

from typing import Any, Optional, Union

from loguru import logger

from fides.api.schemas.storage.storage import StorageSecrets, StorageSecretsS3
from fides.api.service.storage.streaming.cloud_storage_client import CloudStorageClient
from fides.api.service.storage.streaming.s3.s3_storage_client import (
    create_s3_storage_client,
)
from fides.api.service.storage.streaming.util import update_storage_secrets


class CloudStorageClientFactory:
    """Factory for creating cloud storage clients based on storage type and configuration"""

    @staticmethod
    def create_storage_client(
        storage_type: str,
        auth_method: str,
        storage_secrets: Optional[
            Union[StorageSecretsS3, dict[StorageSecrets, Any]]
        ] = None,
    ) -> CloudStorageClient:
        """Create a storage client based on the storage type"""

        if storage_type.lower() == "s3":
            if storage_secrets is None:
                raise ValueError("Storage secrets are required for S3")
            secrets_dict = update_storage_secrets(storage_secrets)
            return create_s3_storage_client(auth_method, secrets_dict)

        if storage_type.lower() in ["gcs", "gcp", "google"]:
            raise NotImplementedError("GCS streaming is not yet implemented")

        raise ValueError(f"Unsupported storage type: {storage_type}")

    @staticmethod
    def create_storage_client_from_config(
        storage_config: dict[str, Any]
    ) -> CloudStorageClient:
        """Create a storage client from a configuration dictionary"""

        storage_type = storage_config.get("type", "s3")
        auth_method = storage_config.get("auth_method", "automatic")
        storage_secrets = storage_config.get("secrets")

        logger.info("Creating storage client for type: {}", storage_type)

        return CloudStorageClientFactory.create_storage_client(
            storage_type=storage_type,
            auth_method=auth_method,
            storage_secrets=storage_secrets,
        )


# Convenience function for backward compatibility
def get_storage_client(
    storage_type: str,
    auth_method: str,
    storage_secrets: Optional[
        Union[StorageSecretsS3, dict[StorageSecrets, Any]]
    ] = None,
) -> CloudStorageClient:
    """Convenience function to create a storage client"""
    return CloudStorageClientFactory.create_storage_client(
        storage_type, auth_method, storage_secrets
    )
