import os
from datetime import datetime
from io import BytesIO
from typing import List, Optional

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.models.storage import StorageConfig, get_active_default_storage_config
from fides.api.schemas.request_task.external_storage import ExternalStorageMetadata
from fides.api.schemas.storage.storage import StorageDetails, StorageType
from fides.api.service.storage.gcs import get_gcs_client
from fides.api.service.storage.s3 import (
    generic_delete_from_s3,
    generic_retrieve_from_s3,
    generic_upload_to_s3,
)
from fides.api.service.storage.util import get_local_filename
from fides.api.util.collection_util import Row
from fides.api.util.encryption.request_task_aes_gcm_util import (
    RequestTaskEncryptionError,
    decrypt_data,
    encrypt_data,
)


class RequestTaskStorageError(Exception):
    """Raised when external storage operations fail"""


class RequestTaskStorageUtil:
    """Utility class to handle external storage operations for RequestTask data

    Provides encrypted storage/retrieval of RequestTask data using existing storage functions.
    """

    @staticmethod
    def store_large_data(
        db: Session,
        privacy_request_id: str,
        collection_name: str,
        data: List[Row],
        data_type: str,  # "access_data" or "data_for_erasures"
        storage_key: Optional[str] = None,
    ) -> ExternalStorageMetadata:
        """
        Store large data to external storage with encryption and return metadata

        Args:
            db: Database session
            privacy_request_id: ID of the privacy request
            collection_name: Name of the collection
            data: The data to store
            data_type: Type of data being stored
            storage_key: Optional specific storage config key to use

        Returns:
            ExternalStorageMetadata with storage details

        Raises:
            RequestTaskStorageError: If storage fails
        """
        # Get storage config
        if storage_key:
            storage_config = (
                db.query(StorageConfig).filter(StorageConfig.key == storage_key).first()
            )
            if not storage_config:
                raise RequestTaskStorageError(
                    f"Storage configuration with key '{storage_key}' not found"
                )
        else:
            storage_config = get_active_default_storage_config(db)
            if not storage_config:
                raise RequestTaskStorageError(
                    "No active default storage configuration available for large data"
                )

        # Generate file key
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        file_key = f"{data_type}/{privacy_request_id}/{collection_name}/{timestamp}"

        # Serialize and encrypt data
        try:
            # Encrypt the data with JSON serialization built-in
            encrypted_bytes = encrypt_data(data)
            file_size = len(encrypted_bytes)

            logger.info(f"Encrypted and serialized data to {file_size} bytes")
        except (TypeError, ValueError) as e:
            raise RequestTaskStorageError(f"Failed to serialize data: {str(e)}")
        except RequestTaskEncryptionError as e:
            raise RequestTaskStorageError(f"Failed to encrypt data: {str(e)}")

        # Store to external storage
        try:
            if storage_config.type == StorageType.s3:
                RequestTaskStorageUtil._store_to_s3(
                    storage_config, file_key, encrypted_bytes
                )
            elif storage_config.type == StorageType.gcs:
                RequestTaskStorageUtil._store_to_gcs(
                    storage_config, file_key, encrypted_bytes
                )
            elif storage_config.type == StorageType.local:
                RequestTaskStorageUtil._store_to_local(file_key, encrypted_bytes)
            else:
                raise RequestTaskStorageError(
                    f"Unsupported storage type: {storage_config.type}"
                )

            logger.info(
                f"Stored encrypted large {data_type} for privacy request {privacy_request_id} "
                f"collection {collection_name} to {storage_config.type} storage ({file_size} bytes)"
            )

            return ExternalStorageMetadata(
                storage_type=StorageType(storage_config.type.value),
                file_key=file_key,
                filesize=file_size,
                storage_key=storage_config.key,
            )

        except Exception as e:
            logger.error(
                f"Failed to store large data for privacy request {privacy_request_id} "
                f"collection {collection_name}: {e}"
            )
            raise RequestTaskStorageError(f"Failed to store large data: {str(e)}")

    @staticmethod
    def retrieve_large_data(
        db: Session, metadata: ExternalStorageMetadata
    ) -> List[Row]:
        """
        Retrieve and decrypt large data from external storage

        Args:
            db: Database session
            metadata: External storage metadata

        Returns:
            The retrieved and decrypted data

        Raises:
            RequestTaskStorageError: If retrieval fails
        """
        try:
            # Get storage config
            if metadata.storage_key:
                storage_config = (
                    db.query(StorageConfig)
                    .filter(StorageConfig.key == metadata.storage_key)
                    .first()
                )
                if not storage_config:
                    raise RequestTaskStorageError(
                        f"Storage configuration with key '{metadata.storage_key}' not found"
                    )
            else:
                storage_config = get_active_default_storage_config(db)
                if not storage_config:
                    raise RequestTaskStorageError("No storage configuration found")

            # Retrieve encrypted data
            storage_type_value = (
                metadata.storage_type.value
                if isinstance(metadata.storage_type, StorageType)
                else metadata.storage_type
            )

            if storage_type_value == StorageType.s3.value:
                encrypted_bytes = RequestTaskStorageUtil._retrieve_from_s3(
                    storage_config, metadata
                )
            elif storage_type_value == StorageType.gcs.value:
                encrypted_bytes = RequestTaskStorageUtil._retrieve_from_gcs(
                    storage_config, metadata
                )
            elif storage_type_value == StorageType.local.value:
                encrypted_bytes = RequestTaskStorageUtil._retrieve_from_local(metadata)
            else:
                raise RequestTaskStorageError(
                    f"Unsupported storage type: {storage_type_value}"
                )

            # Decrypt and deserialize data
            logger.info("Decrypting retrieved data")
            return decrypt_data(encrypted_bytes)

        except RequestTaskEncryptionError as e:
            raise RequestTaskStorageError(f"Failed to decrypt data: {str(e)}")
        except Exception as e:
            raise RequestTaskStorageError(
                f"Failed to retrieve data from {metadata.storage_type} "
                f"storage (key: {metadata.file_key}): {str(e)}"
            ) from e

    @staticmethod
    def delete_large_data(db: Session, metadata: ExternalStorageMetadata) -> None:
        """
        Delete large data from external storage

        Args:
            db: Database session
            metadata: External storage metadata

        Raises:
            RequestTaskStorageError: If deletion fails (but doesn't stop execution)
        """
        try:
            # Get storage config
            if metadata.storage_key:
                storage_config = (
                    db.query(StorageConfig)
                    .filter(StorageConfig.key == metadata.storage_key)
                    .first()
                )
                if not storage_config:
                    logger.warning(
                        f"Storage configuration with key '{metadata.storage_key}' not found for cleanup"
                    )
                    return
            else:
                storage_config = get_active_default_storage_config(db)
                if not storage_config:
                    logger.warning("No storage configuration found for cleanup")
                    return

            # Delete from external storage
            storage_type_value = (
                metadata.storage_type.value
                if isinstance(metadata.storage_type, StorageType)
                else metadata.storage_type
            )

            if storage_type_value == StorageType.s3.value:
                RequestTaskStorageUtil._delete_from_s3(storage_config, metadata)
            elif storage_type_value == StorageType.gcs.value:
                RequestTaskStorageUtil._delete_from_gcs(storage_config, metadata)
            elif storage_type_value == StorageType.local.value:
                RequestTaskStorageUtil._delete_from_local(metadata)
            else:
                logger.warning(
                    f"Unsupported storage type for cleanup: {storage_type_value}"
                )
                return

            logger.info(
                f"Deleted external storage file: {metadata.file_key} "
                f"from {storage_type_value} storage"
            )

        except Exception as e:
            logger.warning(
                f"Failed to delete external storage file {metadata.file_key}: {str(e)}"
            )

    # Private helper methods using existing storage functions

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
        """Retrieve data from S3 using existing generic_retrieve_from_s3"""
        bucket_name = config.details[StorageDetails.BUCKET.value]
        auth_method = config.details[StorageDetails.AUTH_METHOD.value]

        _, data_bytes = generic_retrieve_from_s3(
            storage_secrets=config.secrets,
            bucket_name=bucket_name,
            file_key=metadata.file_key,
            auth_method=auth_method,
            get_content=True,
        )
        return data_bytes  # type: ignore

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
