"""Factory for creating provider-specific storage clients."""

from __future__ import annotations

from typing import Any

from fides.api.service.storage.streaming.base_storage_client import BaseStorageClient
from fides.api.service.storage.streaming.s3.s3_storage_client import S3StorageClient


class StorageClientFactory:
    """Factory for creating provider-specific storage clients.

    This factory creates the appropriate storage client implementation based on
    the storage type, providing a clean separation between the main client and
    provider-specific logic.
    """

    @staticmethod
    def create_client(storage_type: str, storage_secrets: Any) -> BaseStorageClient:
        """Create a provider-specific storage client.

        Args:
            storage_type: Type of storage ('s3', 'gcs', 'azure')
            storage_secrets: Storage credentials and configuration.
                           Will be passed to the specific storage client implementation.

        Returns:
            Provider-specific storage client implementation

        Raises:
            ValueError: If the storage type is not supported
        """
        normalized_type = StorageClientFactory._normalize_storage_type(storage_type)

        if normalized_type == "s3":
            return S3StorageClient(storage_secrets)
        if normalized_type == "gcs":
            raise NotImplementedError("GCS storage is not yet supported")
        raise ValueError(f"Unsupported storage type: {storage_type}")

    @staticmethod
    def _normalize_storage_type(storage_type: str) -> str:
        """Normalize storage type to standard values.

        Args:
            storage_type: Raw storage type string

        Returns:
            Normalized storage type string
        """
        storage_type = storage_type.lower()

        # Normalize storage type
        if storage_type in {"gcs", "gcp", "google"}:
            return "gcs"
        if storage_type == "s3":
            return "s3"

        return storage_type
