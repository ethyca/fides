"""
ExternalDataStorageService handles external storage of large encrypted data.
Clean implementation using the unified StorageService with automatic encryption.
"""

from io import BytesIO
from typing import Any, Optional

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.models.storage import StorageConfig, get_active_default_storage_config
from fides.api.schemas.external_storage import ExternalStorageMetadata
from fides.api.schemas.storage.storage import StorageType
from fides.api.util.encryption.aes_gcm_encryption_util import decrypt_data, encrypt_data


class ExternalDataStorageError(Exception):
    """Raised when external data storage operations fail."""


class ExternalDataStorageService:
    """
    Service for storing large encrypted data externally using unified StorageService.

    Handles:
    - Automatic encryption/decryption
    - Multiple storage backends through unified interface
    - Consistent file organization
    - Cleanup operations
    """

    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.db = db

    @classmethod
    def store_data(
        cls,
        db: Session,
        storage_path: str,
        data: Any,
        storage_key: Optional[str] = None,
    ) -> ExternalStorageMetadata:
        """
        Store data in external storage with encryption.

        Args:
            db: Database session
            storage_path: Path where data should be stored (e.g., "model/id/field/timestamp")
            data: The data to store (will be serialized and encrypted)
            storage_key: Optional specific storage config key to use

        Returns:
            ExternalStorageMetadata with storage details

        Raises:
            ExternalDataStorageError: If storage operation fails
        """
        service = cls(db)
        return service._store_data_internal(storage_path, data, storage_key)

    @classmethod
    def retrieve_data(
        cls,
        db: Session,
        metadata: ExternalStorageMetadata,
    ) -> Any:
        """
        Retrieve and decrypt data from external storage.

        Args:
            db: Database session
            metadata: Storage metadata containing location and details

        Returns:
            Decrypted and deserialized data

        Raises:
            ExternalDataStorageError: If retrieval operation fails
        """
        service = cls(db)
        return service._retrieve_data_internal(metadata)

    @classmethod
    def delete_data(
        cls,
        db: Session,
        metadata: ExternalStorageMetadata,
    ) -> None:
        """
        Delete data from external storage.

        Args:
            db: Database session
            metadata: Storage metadata containing location

        Note:
            This operation is best-effort and will log warnings on failure
            rather than raising exceptions, to support cleanup scenarios.
        """
        service = cls(db)
        service._delete_data_internal(metadata)

    def _store_data_internal(
        self, storage_path: str, data: Any, storage_key: Optional[str] = None
    ) -> ExternalStorageMetadata:
        """Internal implementation for storing data."""
        try:
            # Get storage configuration
            storage_config = self._get_storage_config(storage_key)

            # Serialize and encrypt the data
            encrypted_data = encrypt_data(data)
            file_size = len(encrypted_data)

            # Create unified storage service (lazy import to avoid circular import)
            from fides.service.storage.storage_service import StorageService
            storage_service = StorageService.from_config(storage_config)

            # Store encrypted data
            response = storage_service.store_file(
                file_content=BytesIO(encrypted_data),
                file_key=storage_path,
                content_type="application/octet-stream",
                metadata={
                    "data_type": "external_encrypted_data",
                    "original_size": str(file_size),
                    "encrypted": "true",
                    "created_by": "ExternalDataStorageService",
                },
            )

            if not response.success:
                raise ExternalDataStorageError(
                    f"Failed to store data: {response.error_message}"
                )

            # Create and return metadata
            metadata = ExternalStorageMetadata(
                storage_type=StorageType(storage_config.type.value),
                file_key=storage_path,
                filesize=file_size,
                storage_key=storage_config.key,
            )

            logger.info(
                f"Stored {file_size:,} bytes to {storage_config.type} storage "
                f"at path: {storage_path}"
            )

            return metadata

        except Exception as e:
            logger.error(f"Failed to store data externally: {str(e)}")
            raise ExternalDataStorageError(f"Failed to store data: {str(e)}") from e

    def _retrieve_data_internal(self, metadata: ExternalStorageMetadata) -> Any:
        """Internal implementation for retrieving data."""
        try:
            # Get storage configuration
            storage_config = self._get_storage_config(metadata.storage_key)

            # Create unified storage service (lazy import to avoid circular import)
            from fides.service.storage.storage_service import StorageService
            storage_service = StorageService.from_config(storage_config)

            # Retrieve encrypted data
            response = storage_service.retrieve_file(
                metadata.file_key, get_content=True
            )

            if not response.success:
                raise ExternalDataStorageError(
                    f"Failed to retrieve data from storage: {response.error_message}"
                )

            # Get content using streaming for memory efficiency
            with storage_service.stream_download(metadata.file_key) as content_stream:
                encrypted_data = content_stream.read()

            # Handle case where download returns None
            if encrypted_data is None:
                raise ExternalDataStorageError(
                    f"No data found at path: {metadata.file_key}"
                )

            # Decrypt and deserialize
            data = decrypt_data(encrypted_data)

            logger.info(
                f"Retrieved {metadata.filesize:,} bytes from {metadata.storage_type} storage "
                f"at path: {metadata.file_key}"
            )

            return data

        except ExternalDataStorageError:
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve data from external storage: {str(e)}")
            raise ExternalDataStorageError(f"Failed to retrieve data: {str(e)}") from e

    def _delete_data_internal(self, metadata: ExternalStorageMetadata) -> None:
        """Internal implementation for deleting data."""
        try:
            # Get storage configuration
            storage_config = self._get_storage_config(metadata.storage_key)

            # Create unified storage service (lazy import to avoid circular import)
            from fides.service.storage.storage_service import StorageService
            storage_service = StorageService.from_config(storage_config)

            # Delete from storage
            response = storage_service.delete_file(metadata.file_key)

            if not response.success:
                logger.warning(
                    f"Failed to delete external storage file: {response.error_message}"
                )
            else:
                logger.info(
                    f"Deleted external storage file from {metadata.storage_type} storage "
                    f"at path: {metadata.file_key}"
                )

        except Exception as e:
            # Log but don't raise - cleanup should be best effort
            logger.warning(
                f"Failed to delete external storage file at {metadata.file_key}: {str(e)}"
            )

    def _get_storage_config(self, storage_key: Optional[str]) -> StorageConfig:
        """Resolve and return the StorageConfig to use."""
        if storage_key:
            storage_config = StorageConfig.get_by(
                db=self.db, field="key", value=storage_key
            )
            if not storage_config:
                msg = f"Storage configuration with key '{storage_key}' not found"
                logger.error(msg)
                raise ExternalDataStorageError(msg)
            return storage_config

        # No explicit key – use the active default
        storage_config = get_active_default_storage_config(self.db)
        if not storage_config:
            msg = "No active default storage configuration available for large data"
            logger.error(msg)
            raise ExternalDataStorageError(msg)

        return storage_config


# Backward compatibility - maintains exact same API as before
def store_data_externally(
    db: Session,
    storage_path: str,
    data: Any,
    storage_key: Optional[str] = None,
) -> ExternalStorageMetadata:
    """Store data externally with backward compatibility."""
    return ExternalDataStorageService.store_data(db, storage_path, data, storage_key)


def retrieve_external_data(
    db: Session,
    metadata: ExternalStorageMetadata,
) -> Any:
    """Retrieve external data with backward compatibility."""
    return ExternalDataStorageService.retrieve_data(db, metadata)


def delete_external_data(
    db: Session,
    metadata: ExternalStorageMetadata,
) -> None:
    """Delete external data with backward compatibility."""
    ExternalDataStorageService.delete_data(db, metadata)
