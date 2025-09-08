from typing import Any, Dict

from .base import StorageProvider
from .s3 import S3StorageProvider
from .gcs import GCSStorageProvider
from .local import LocalStorageProvider
from fides.api.schemas.storage.storage import StorageType
from fides.api.models.storage import StorageConfig


class StorageProviderFactory:
    """
    Factory class for creating storage provider instances based on configuration.
    """

    _providers = {
        StorageType.s3.value: S3StorageProvider,
        StorageType.gcs.value: GCSStorageProvider,
        StorageType.local.value: LocalStorageProvider,
    }

    @classmethod
    def create_provider(
        cls, storage_type: str, configuration: Dict[str, Any]
    ) -> StorageProvider:
        """
        Create a storage provider instance based on the storage type.

        Args:
            storage_type: The type of storage provider ('s3', 'gcs', 'local')
            configuration: Configuration dictionary containing credentials and settings

        Returns:
            StorageProvider instance

        Raises:
            ValueError: If storage type is not supported
        """
        if storage_type not in cls._providers:
            available_types = list(cls._providers.keys())
            raise ValueError(
                f"Unsupported storage type: {storage_type}. "
                f"Available types: {available_types}"
            )

        provider_class = cls._providers[storage_type]
        return provider_class(configuration)

    @classmethod
    def get_supported_types(cls) -> list[str]:
        """Get list of supported storage types"""
        return list(cls._providers.keys())


def create_storage_provider_from_config(storage_config) -> StorageProvider:
    """
    Convenience function to create a storage provider from a Fides StorageConfig model.

    Args:
        storage_config: Fides StorageConfig model instance

    Returns:
        StorageProvider instance configured from the storage config
    """

    # Extract configuration from StorageConfig model
    configuration = {
        # Core fields that all providers might use
        "storage_config_key": storage_config.key,
        "storage_config_name": storage_config.name,
        "format": storage_config.format.value,
        # Provider-specific fields
        "bucket_name": storage_config.details.get("bucket"),
        "auth_method": storage_config.details.get("auth_method"),
        "region_name": storage_config.details.get("region_name"),
        "base_directory": storage_config.details.get("base_directory"),
        # Encrypted secrets
        "secrets": storage_config.secrets or {},
    }

    # Add all details to configuration for provider flexibility
    if storage_config.details:
        for key, value in storage_config.details.items():
            if key not in configuration:  # Don't override already extracted values
                configuration[key] = value

    return StorageProviderFactory.create_provider(
        storage_config.type.value, configuration
    )


def create_storage_provider_by_key(db_session, storage_key: str) -> StorageProvider:
    """
    Create a storage provider by looking up a StorageConfig by its key.

    Args:
        db_session: SQLAlchemy database session
        storage_key: The key of the StorageConfig to look up

    Returns:
        StorageProvider instance configured from the found storage config

    Raises:
        ValueError: If no StorageConfig found with the given key
    """

    storage_config = StorageConfig.get_by(db=db_session, field="key", value=storage_key)
    if not storage_config:
        raise ValueError(f"No StorageConfig found with key: {storage_key}")

    return create_storage_provider_from_config(storage_config)


def create_default_storage_provider(
    db_session, storage_type: StorageType
) -> StorageProvider:
    """
    Create a storage provider using the default StorageConfig for the given type.

    Args:
        db_session: SQLAlchemy database session
        storage_type: The storage type ('s3', 'gcs', 'local')

    Returns:
        StorageProvider instance configured from the default storage config

    Raises:
        ValueError: If no default StorageConfig found for the given type
    """

    storage_config = (
        StorageConfig.query(db_session)
        .filter(StorageConfig.type == storage_type, StorageConfig.is_default is True)
        .first()
    )

    if not storage_config:
        raise ValueError(f"No default StorageConfig found for type: {storage_type}")

    return create_storage_provider_from_config(storage_config)
