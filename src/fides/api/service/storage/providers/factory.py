"""
Storage Provider Factory.

This module provides a factory for creating storage provider instances based on
storage configuration. It uses the Factory pattern to abstract provider creation.
"""

from typing import Any, Dict, Optional

from loguru import logger

from fides.api.models.storage import StorageConfig
from fides.api.schemas.storage.storage import StorageDetails, StorageType
from fides.api.service.storage.providers.base import StorageProvider
from fides.api.service.storage.providers.gcs_provider import GCSStorageProvider
from fides.api.service.storage.providers.local_provider import LocalStorageProvider
from fides.api.service.storage.providers.s3_provider import S3StorageProvider


class StorageProviderFactory:
    """Factory for creating storage provider instances.

    This factory creates the appropriate StorageProvider implementation based on
    the storage type configuration. It provides a clean separation between
    storage configuration and provider instantiation.

    Example:
        ```python
        # Create from StorageConfig model
        provider = StorageProviderFactory.create(storage_config)

        # Create from raw configuration
        provider = StorageProviderFactory.create_from_type(
            storage_type=StorageType.s3,
            details={"auth_method": "secret_keys", "bucket": "my-bucket"},
            secrets={"aws_access_key_id": "...", "aws_secret_access_key": "..."},
        )

        # Use the provider
        result = provider.upload(bucket, key, data)
        ```
    """

    @staticmethod
    def create(config: StorageConfig) -> StorageProvider:
        """Create a storage provider from a StorageConfig model.

        This is the primary method for creating providers in production code,
        as it extracts configuration from the database model.

        Args:
            config: StorageConfig model instance.

        Returns:
            Appropriate StorageProvider implementation.

        Raises:
            ValueError: If the storage type is not supported.
        """
        logger.debug(
            "Creating storage provider from config: type={}, key={}",
            config.type,
            config.key,
        )

        return StorageProviderFactory.create_from_type(
            storage_type=config.type,
            details=config.details or {},
            secrets=config.secrets,
        )

    @staticmethod
    def create_from_type(
        storage_type: StorageType,
        details: Dict[str, Any],
        secrets: Optional[Dict[str, Any]] = None,
    ) -> StorageProvider:
        """Create a storage provider from raw configuration.

        This method is useful for testing or when StorageConfig is not available.

        Args:
            storage_type: The type of storage (s3, gcs, local).
            details: Dictionary containing storage details (bucket, auth_method, etc.).
            secrets: Optional dictionary containing storage secrets/credentials.

        Returns:
            Appropriate StorageProvider implementation.

        Raises:
            ValueError: If the storage type is not supported.
        """
        logger.debug("Creating storage provider for type: {}", storage_type)

        # Normalize storage type if it's a string
        if isinstance(storage_type, str):
            try:
                storage_type = StorageType(storage_type)
            except ValueError as exc:
                raise ValueError(f"Unsupported storage type: {storage_type}") from exc

        if storage_type == StorageType.s3:
            auth_method = details.get(StorageDetails.AUTH_METHOD.value)
            if not auth_method:
                raise ValueError("auth_method is required for S3 storage")

            return S3StorageProvider(
                auth_method=auth_method,
                secrets=secrets,
            )

        if storage_type == StorageType.gcs:
            auth_method = details.get(StorageDetails.AUTH_METHOD.value)
            if not auth_method:
                raise ValueError("auth_method is required for GCS storage")

            return GCSStorageProvider(
                auth_method=auth_method,
                secrets=secrets,
            )

        if storage_type == StorageType.local:
            return LocalStorageProvider()

        raise ValueError(f"Unsupported storage type: {storage_type}")

    @staticmethod
    def get_bucket_from_config(config: StorageConfig) -> str:
        """Extract the bucket name from a StorageConfig.

        This is a helper method to consistently extract the bucket name
        from storage configuration.

        Args:
            config: StorageConfig model instance.

        Returns:
            Bucket name string. Empty string for local storage.
        """
        if config.type == StorageType.local:
            return ""

        return config.details.get(StorageDetails.BUCKET.value, "")
