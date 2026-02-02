"""
Service for handling external storage of large encrypted data.

This service provides a generic interface for storing large data that would
otherwise exceed database column size limits or impact performance.
"""

from io import BytesIO
from typing import Any, Optional

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.models.storage import StorageConfig, get_active_default_storage_config
from fides.api.schemas.external_storage import ExternalStorageMetadata
from fides.api.schemas.storage.storage import StorageType
from fides.api.service.storage.providers import StorageProviderFactory
from fides.api.util.encryption.aes_gcm_encryption_util import decrypt_data, encrypt_data


class ExternalDataStorageError(Exception):
    """Raised when external data storage operations fail."""


class ExternalDataStorageService:
    """
    Service for storing large encrypted data externally.

    Handles:
    - Automatic encryption/decryption
    - Multiple storage backends (S3, local, GCS, etc.) via StorageProviderFactory
    - Consistent file organization
    - Cleanup operations
    """

    @staticmethod
    def _get_storage_config(db: Session, storage_key: Optional[str]) -> "StorageConfig":
        """Resolve and return the StorageConfig to use.

        Preference order:

        1. If *storage_key* is provided, fetch that specific configuration.
        2. Otherwise, fall back to the *active* default storage configuration.

        Raises ExternalDataStorageError when no suitable configuration is found.
        """

        if storage_key:
            storage_config = (
                db.query(StorageConfig).filter(StorageConfig.key == storage_key).first()
            )
            if not storage_config:
                msg = f"Storage configuration with key '{storage_key}' not found"
                logger.error(msg)
                raise ExternalDataStorageError(msg)
            return storage_config

        # No explicit key – use the active default
        storage_config = get_active_default_storage_config(db)
        if not storage_config:
            msg = "No active default storage configuration available for large data"
            logger.error(msg)
            raise ExternalDataStorageError(msg)

        return storage_config

    @staticmethod
    def store_data(
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
        try:
            storage_config = ExternalDataStorageService._get_storage_config(
                db, storage_key
            )

            # Serialize and encrypt the data
            encrypted_data = encrypt_data(data)
            file_size = len(encrypted_data)

            # Create provider using factory and store data
            provider = StorageProviderFactory.create(storage_config)
            bucket = StorageProviderFactory.get_bucket_from_config(storage_config)

            provider.upload(bucket, storage_path, BytesIO(encrypted_data))

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

        except ExternalDataStorageError:
            raise
        except Exception as e:
            logger.error(f"Failed to store data externally: {str(e)}")
            raise ExternalDataStorageError(f"Failed to store data: {str(e)}") from e

    @staticmethod
    def retrieve_data(
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
        try:
            storage_config = ExternalDataStorageService._get_storage_config(
                db, metadata.storage_key
            )

            # Create provider using factory and download data
            provider = StorageProviderFactory.create(storage_config)
            bucket = StorageProviderFactory.get_bucket_from_config(storage_config)

            file_obj = provider.download(bucket, metadata.file_key)
            encrypted_data = file_obj.read()

            # Handle case where download returns None or empty
            if not encrypted_data:
                raise ExternalDataStorageError(
                    f"No data found at path: {metadata.file_key}"
                )

            # Decrypt and deserialize
            data = decrypt_data(encrypted_data)

            storage_type_value = (
                metadata.storage_type.value
                if isinstance(metadata.storage_type, StorageType)
                else metadata.storage_type
            )
            logger.info(
                f"Retrieved {metadata.filesize:,} bytes from {storage_type_value} storage "
                f"at path: {metadata.file_key}"
            )

            return data

        except ExternalDataStorageError:
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve data from external storage: {str(e)}")
            raise ExternalDataStorageError(f"Failed to retrieve data: {str(e)}") from e

    @staticmethod
    def delete_data(
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
        try:
            storage_config = ExternalDataStorageService._get_storage_config(
                db, metadata.storage_key
            )

            # Create provider using factory and delete data
            provider = StorageProviderFactory.create(storage_config)
            bucket = StorageProviderFactory.get_bucket_from_config(storage_config)

            provider.delete(bucket, metadata.file_key)

            storage_type_value = (
                metadata.storage_type.value
                if isinstance(metadata.storage_type, StorageType)
                else metadata.storage_type
            )
            logger.info(
                f"Deleted external storage file from {storage_type_value} storage "
                f"at path: {metadata.file_key}"
            )

        except Exception as e:
            # Log but don't raise - cleanup should be best effort
            logger.warning(
                f"Failed to delete external storage file at {metadata.file_key}: {str(e)}"
            )
