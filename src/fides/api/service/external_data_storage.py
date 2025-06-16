"""
Service for handling external storage of large encrypted data.

This service provides a generic interface for storing large data that would
otherwise exceed database column size limits or impact performance.
"""

import os
from io import BytesIO
from typing import Any, Optional

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.models.storage import StorageConfig, get_active_default_storage_config
from fides.api.schemas.external_storage import ExternalStorageMetadata
from fides.api.schemas.storage.storage import StorageDetails, StorageType
from fides.api.service.storage.gcs import get_gcs_client
from fides.api.service.storage.s3 import generic_delete_from_s3, generic_upload_to_s3
from fides.api.service.storage.util import get_local_filename
from fides.api.util.aws_util import get_s3_client
from fides.api.util.encryption.aes_gcm_encryption_util import decrypt_data, encrypt_data


class ExternalDataStorageError(Exception):
    """Raised when external data storage operations fail."""


class ExternalDataStorageService:
    """
    Service for storing large encrypted data externally.

    Handles:
    - Automatic encryption/decryption
    - Multiple storage backends (S3, local, GCS, etc.)
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

            # Store to external storage based on type
            if storage_config.type == StorageType.s3:
                ExternalDataStorageService._store_to_s3(
                    storage_config, storage_path, encrypted_data
                )
            elif storage_config.type == StorageType.gcs:
                ExternalDataStorageService._store_to_gcs(
                    storage_config, storage_path, encrypted_data
                )
            elif storage_config.type == StorageType.local:
                ExternalDataStorageService._store_to_local(storage_path, encrypted_data)
            else:
                raise ExternalDataStorageError(
                    f"Unsupported storage type: {storage_config.type}"
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

            # Retrieve encrypted data based on storage type
            storage_type_value = (
                metadata.storage_type.value
                if isinstance(metadata.storage_type, StorageType)
                else metadata.storage_type
            )

            if storage_type_value == StorageType.s3.value:
                encrypted_data = ExternalDataStorageService._retrieve_from_s3(
                    storage_config, metadata
                )
            elif storage_type_value == StorageType.gcs.value:
                encrypted_data = ExternalDataStorageService._retrieve_from_gcs(
                    storage_config, metadata
                )
            elif storage_type_value == StorageType.local.value:
                encrypted_data = ExternalDataStorageService._retrieve_from_local(
                    metadata
                )
            else:
                raise ExternalDataStorageError(
                    f"Unsupported storage type: {storage_type_value}"
                )

            # Handle case where download returns None
            if encrypted_data is None:
                raise ExternalDataStorageError(
                    f"No data found at path: {metadata.file_key}"
                )

            # Decrypt and deserialize
            data = decrypt_data(encrypted_data)

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

            # Delete from external storage based on type
            storage_type_value = (
                metadata.storage_type.value
                if isinstance(metadata.storage_type, StorageType)
                else metadata.storage_type
            )

            if storage_type_value == StorageType.s3.value:
                ExternalDataStorageService._delete_from_s3(storage_config, metadata)
            elif storage_type_value == StorageType.gcs.value:
                ExternalDataStorageService._delete_from_gcs(storage_config, metadata)
            elif storage_type_value == StorageType.local.value:
                ExternalDataStorageService._delete_from_local(metadata)
            else:
                logger.warning(
                    f"Unsupported storage type for cleanup: {storage_type_value}"
                )
                return

            logger.info(
                f"Deleted external storage file from {storage_type_value} storage "
                f"at path: {metadata.file_key}"
            )

        except Exception as e:
            # Log but don't raise - cleanup should be best effort
            logger.warning(
                f"Failed to delete external storage file at {metadata.file_key}: {str(e)}"
            )

    # Private helper methods for each storage type

    @staticmethod
    def _store_to_s3(config: StorageConfig, file_key: str, data: bytes) -> None:
        """Store data to S3 using existing generic_upload_to_s3"""
        bucket_name = config.details[StorageDetails.BUCKET.value]
        auth_method = config.details[StorageDetails.AUTH_METHOD.value]

        document = BytesIO(data)
        generic_upload_to_s3(
            storage_secrets=config.secrets,
            bucket_name=bucket_name,
            file_key=file_key,
            auth_method=auth_method,
            document=document,
        )

    @staticmethod
    def _store_to_gcs(config: StorageConfig, file_key: str, data: bytes) -> None:
        """Store data to GCS using existing get_gcs_client"""
        bucket_name = config.details[StorageDetails.BUCKET.value]
        auth_method = config.details[StorageDetails.AUTH_METHOD.value]

        storage_client = get_gcs_client(auth_method, config.secrets)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_key)

        blob.upload_from_string(data, content_type="application/octet-stream")

    @staticmethod
    def _store_to_local(file_key: str, data: bytes) -> None:
        """Store data to local filesystem using existing get_local_filename"""
        file_path = get_local_filename(file_key)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(data)

    @staticmethod
    def _retrieve_from_s3(
        config: StorageConfig, metadata: ExternalStorageMetadata
    ) -> bytes:
        """Retrieve data from S3 directly, bypassing file size limits"""

        bucket_name = config.details[StorageDetails.BUCKET.value]
        auth_method = config.details[StorageDetails.AUTH_METHOD.value]

        # Get S3 client directly and download content regardless of file size
        s3_client = get_s3_client(auth_method, config.secrets)

        try:
            # Download content directly to BytesIO buffer
            file_obj = BytesIO()
            s3_client.download_fileobj(
                Bucket=bucket_name, Key=metadata.file_key, Fileobj=file_obj
            )
            file_obj.seek(0)  # Reset file pointer to beginning
            return file_obj.read()
        except Exception as e:
            logger.error(f"Error retrieving file from S3: {e}")
            raise e

    @staticmethod
    def _retrieve_from_gcs(
        config: StorageConfig, metadata: ExternalStorageMetadata
    ) -> bytes:
        """Retrieve data from GCS using existing get_gcs_client"""
        bucket_name = config.details[StorageDetails.BUCKET.value]
        auth_method = config.details[StorageDetails.AUTH_METHOD.value]

        storage_client = get_gcs_client(auth_method, config.secrets)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(metadata.file_key)
        return blob.download_as_bytes()

    @staticmethod
    def _retrieve_from_local(metadata: ExternalStorageMetadata) -> bytes:
        """Retrieve data from local filesystem"""
        file_path = get_local_filename(metadata.file_key)
        with open(file_path, "rb") as f:
            return f.read()

    @staticmethod
    def _delete_from_s3(
        config: StorageConfig, metadata: ExternalStorageMetadata
    ) -> None:
        """Delete data from S3 using existing generic_delete_from_s3"""
        bucket_name = config.details[StorageDetails.BUCKET.value]
        auth_method = config.details[StorageDetails.AUTH_METHOD.value]

        generic_delete_from_s3(
            storage_secrets=config.secrets,
            bucket_name=bucket_name,
            file_key=metadata.file_key,
            auth_method=auth_method,
        )

    @staticmethod
    def _delete_from_gcs(
        config: StorageConfig, metadata: ExternalStorageMetadata
    ) -> None:
        """Delete data from GCS using existing get_gcs_client"""
        bucket_name = config.details[StorageDetails.BUCKET.value]
        auth_method = config.details[StorageDetails.AUTH_METHOD.value]

        storage_client = get_gcs_client(auth_method, config.secrets)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(metadata.file_key)
        blob.delete()

    @staticmethod
    def _delete_from_local(metadata: ExternalStorageMetadata) -> None:
        """Delete data from local filesystem"""
        file_path = get_local_filename(metadata.file_key)
        if os.path.exists(file_path):
            os.remove(file_path)
