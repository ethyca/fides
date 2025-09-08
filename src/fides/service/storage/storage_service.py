from typing import Any, Dict, IO, Optional, Union
from io import BytesIO

from fideslang.validation import AnyHttpUrlString
from .providers.base import StorageProvider, StorageResponse
from .providers.factory import (
    create_storage_provider_from_config,
    create_storage_provider_by_key,
    create_default_storage_provider,
)
from fides.api.schemas.storage.storage import StorageType


class StorageService:
    """
    Unified storage service that provides a consistent interface for all storage operations.
    Delegates to pluggable StorageProvider implementations based on configuration.
    """

    def __init__(self, provider: StorageProvider):
        self.provider = provider

    def store_file(
        self,
        file_content: Union[IO[bytes], bytes, BytesIO],
        file_key: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> StorageResponse:
        """Store a file in the configured storage backend."""
        return self.provider.store_file(file_content, file_key, content_type, metadata)

    def retrieve_file(
        self, file_key: str, get_content: bool = False
    ) -> StorageResponse:
        """Retrieve a file or its metadata from storage."""
        return self.provider.retrieve_file(file_key, get_content)

    def delete_file(self, file_key: str) -> StorageResponse:
        """Delete a file from storage."""
        return self.provider.delete_file(file_key)

    def generate_presigned_url(
        self, file_key: str, ttl_seconds: Optional[int] = None
    ) -> AnyHttpUrlString:
        """Generate a presigned URL for secure access to the file."""
        return self.provider.generate_presigned_url(file_key, ttl_seconds)

    def stream_upload(self, file_key: str) -> IO[bytes]:
        """Get a writable stream for memory-efficient uploads."""
        return self.provider.stream_upload(file_key)

    def stream_download(self, file_key: str) -> IO[bytes]:
        """Get a readable stream for memory-efficient downloads."""
        return self.provider.stream_download(file_key)

    def file_exists(self, file_key: str) -> bool:
        """Check if a file exists in storage."""
        return self.provider.file_exists(file_key)

    def validate_connection(self) -> bool:
        """Validate the storage provider connection."""
        return self.provider.validate_configuration()

    @classmethod
    def from_config(cls, storage_config) -> "StorageService":
        """
        Create a StorageService from a Fides StorageConfig model instance.

        Args:
            storage_config: Fides StorageConfig model instance

        Returns:
            StorageService configured with the appropriate provider

        Example:
            storage_config = StorageConfig.get_by(db=db, field="key", value="my-s3-config")
            storage_service = StorageService.from_config(storage_config)
            response = storage_service.store_file(file_content, "path/to/file.txt")
        """
        provider = create_storage_provider_from_config(storage_config)
        return cls(provider)

    @classmethod
    def from_config_key(cls, db_session, storage_key: str) -> "StorageService":
        """
        Create a StorageService by looking up a StorageConfig by its key.

        Args:
            db_session: SQLAlchemy database session
            storage_key: The key of the StorageConfig to look up

        Returns:
            StorageService configured with the appropriate provider

        Raises:
            ValueError: If no StorageConfig found with the given key

        Example:
            storage_service = StorageService.from_config_key(db, "my-s3-config")
            response = storage_service.store_file(file_content, "path/to/file.txt")
        """
        provider = create_storage_provider_by_key(db_session, storage_key)
        return cls(provider)

    @classmethod
    def from_default_config(
        cls, db_session, storage_type: StorageType
    ) -> "StorageService":
        """
        Create a StorageService using the default StorageConfig for the given type.

        Args:
            db_session: SQLAlchemy database session
            storage_type: The storage type ('s3', 'gcs', 'local')

        Returns:
            StorageService configured with the default provider for the type

        Raises:
            ValueError: If no default StorageConfig found for the given type

        Example:
            # Use default S3 configuration
            storage_service = StorageService.from_default_config(db, "s3")
            response = storage_service.store_file(file_content, "path/to/file.txt")
        """
        provider = create_default_storage_provider(db_session, storage_type)
        return cls(provider)

    @property
    def provider_type(self) -> str:
        """Get the type of the current storage provider."""
        return getattr(self.provider, "storage_type", "unknown")

    @property
    def provider_config(self) -> Dict[str, Any]:
        """Get the configuration of the current storage provider."""
        return getattr(self.provider, "configuration", {})
