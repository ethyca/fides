# pylint: disable=protected-access
import json
import os
from datetime import datetime
from io import BytesIO
from typing import List

from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy_utils.types.encrypted.encrypted_type import AesGcmEngine

from fides.api.models.storage import StorageConfig, get_active_default_storage_config
from fides.api.schemas.request_task.external_storage import ExternalStorageMetadata
from fides.api.schemas.storage.storage import StorageDetails, StorageType
from fides.api.service.storage.gcs import get_gcs_client
from fides.api.service.storage.s3 import generic_upload_to_s3
from fides.api.service.storage.util import get_local_filename
from fides.api.util.collection_util import Row
from fides.api.util.storage_util import StorageJSONEncoder
from fides.config import CONFIG


class RequestTaskStorageError(Exception):
    """Raised when external storage operations fail"""


def _encrypt_data(data_bytes: bytes) -> bytes:
    """
    Encrypt data bytes using AesGcmEngine with the same key as database columns

    Args:
        data_bytes: Raw data bytes to encrypt

    Returns:
        Encrypted bytes

    Raises:
        RequestTaskStorageError: If encryption fails
    """
    try:
        engine = AesGcmEngine()
        # Use the same key as database columns
        key = CONFIG.security.app_encryption_key
        engine._update_key(key)
        # Convert bytes to string for encryption, as AesGcmEngine expects string input
        data_str = data_bytes.decode("utf-8")
        encrypted_data = engine.encrypt(data_str)
        # Convert encrypted string back to bytes for storage
        encrypted_bytes = encrypted_data.encode("utf-8")
        logger.debug(
            f"Encrypted {len(data_bytes)} bytes to {len(encrypted_bytes)} bytes"
        )
        return encrypted_bytes
    except Exception as e:
        logger.error(f"Failed to encrypt data: {e}")
        raise RequestTaskStorageError(f"Failed to encrypt data: {str(e)}")


def _decrypt_data(encrypted_bytes: bytes) -> bytes:
    """
    Decrypt data bytes using AesGcmEngine with the same key as database columns

    Args:
        encrypted_bytes: Encrypted data bytes to decrypt

    Returns:
        Decrypted bytes

    Raises:
        RequestTaskStorageError: If decryption fails
    """
    try:
        engine = AesGcmEngine()
        # Use the same key as database columns
        key = CONFIG.security.app_encryption_key
        engine._update_key(key)
        # Convert bytes to string for decryption, as AesGcmEngine expects string input
        encrypted_str = encrypted_bytes.decode("utf-8")
        decrypted_data = engine.decrypt(encrypted_str)
        # Convert decrypted string back to bytes
        decrypted_bytes = decrypted_data.encode("utf-8")
        logger.debug(
            f"Decrypted {len(encrypted_bytes)} bytes to {len(decrypted_bytes)} bytes"
        )
        return decrypted_bytes
    except Exception as e:
        logger.error(f"Failed to decrypt data: {e}")
        raise RequestTaskStorageError(f"Failed to decrypt data: {str(e)}")


def store_large_data(
    db: Session,
    privacy_request_id: str,
    collection_name: str,
    data: List[Row],
    data_type: str,  # "access_data" or "data_for_erasures"
) -> ExternalStorageMetadata:
    """
    Store large data to external storage and return metadata

    Args:
        db: Database session
        privacy_request_id: ID of the privacy request
        collection_name: Name of the collection
        data: The data to store
        data_type: Type of data being stored

    Returns:
        ExternalStorageMetadata with storage details

    Raises:
        RequestTaskStorageError: If storage fails
    """
    storage_config = get_active_default_storage_config(db)
    if not storage_config:
        raise RequestTaskStorageError(
            "No active default storage configuration available for large data"
        )

    # Generate file key: {data_type}/{privacy_request_id}/{collection_name}/{timestamp}
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
    file_key = f"{data_type}/{privacy_request_id}/{collection_name}/{timestamp}"

    # Serialize data using StorageJSONEncoder to handle ObjectIds
    try:
        serialized_data = json.dumps(
            data, cls=StorageJSONEncoder, separators=(",", ":")
        )
        data_bytes = serialized_data.encode("utf-8")

        # Encrypt the data before storing
        encrypted_bytes = _encrypt_data(data_bytes)
        file_size = len(encrypted_bytes)

        logger.info(f"Encrypted data from {len(data_bytes)} to {file_size} bytes")
    except (TypeError, ValueError) as e:
        raise RequestTaskStorageError(f"Failed to serialize data: {str(e)}")

    try:
        if storage_config.type == StorageType.s3:
            url = _store_to_s3(storage_config, file_key, encrypted_bytes)
        elif storage_config.type == StorageType.gcs:
            url = _store_to_gcs(storage_config, file_key, encrypted_bytes)
        elif storage_config.type == StorageType.local:
            url = _store_to_local(storage_config, file_key, encrypted_bytes)
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
            url=url,
            filesize=file_size,
            storage_key=storage_config.key,
        )

    except Exception as e:
        logger.error(
            f"Failed to store large data for privacy request {privacy_request_id} "
            f"collection {collection_name}: {e}"
        )
        raise RequestTaskStorageError(f"Failed to store large data: {str(e)}")


def retrieve_large_data(metadata: ExternalStorageMetadata) -> List[Row]:
    """
    Retrieve large data from external storage using metadata

    Args:
        metadata: Storage metadata containing retrieval information

    Returns:
        The deserialized data

    Raises:
        RequestTaskStorageError: If retrieval fails
    """
    try:
        # Handle both enum and string values for storage_type
        storage_type_value = (
            metadata.storage_type.value
            if isinstance(metadata.storage_type, StorageType)
            else metadata.storage_type
        )

        if storage_type_value == StorageType.s3.value:
            encrypted_bytes = _retrieve_from_s3(metadata)
        elif storage_type_value == StorageType.gcs.value:
            encrypted_bytes = _retrieve_from_gcs(metadata)
        elif storage_type_value == StorageType.local.value:
            encrypted_bytes = _retrieve_from_local(metadata)
        else:
            raise RequestTaskStorageError(
                f"Unsupported storage type: {metadata.storage_type}"
            )

        # Decrypt the retrieved data
        logger.info("Decrypting retrieved data")
        data_bytes = _decrypt_data(encrypted_bytes)

        data_str = data_bytes.decode("utf-8")
        return json.loads(data_str)

    except Exception as e:
        logger.error(f"Failed to retrieve large data from {metadata.storage_type}: {e}")
        raise RequestTaskStorageError(f"Failed to retrieve large data: {str(e)}")


def delete_large_data(metadata: ExternalStorageMetadata) -> None:
    """
    Delete large data from external storage

    Args:
        metadata: Storage metadata for the data to delete

    Raises:
        RequestTaskStorageError: If deletion fails (but doesn't stop execution)
    """
    try:
        # Handle both enum and string values for storage_type
        storage_type_value = (
            metadata.storage_type.value
            if isinstance(metadata.storage_type, StorageType)
            else metadata.storage_type
        )

        if storage_type_value == StorageType.s3.value:
            _delete_from_s3(metadata)
        elif storage_type_value == StorageType.gcs.value:
            _delete_from_gcs(metadata)
        elif storage_type_value == StorageType.local.value:
            _delete_from_local(metadata)
        else:
            logger.warning(
                f"Cannot delete from unsupported storage type: {metadata.storage_type}"
            )
            return  # Exit early for unsupported types

        logger.info(f"Deleted large data from {metadata.storage_type} storage")

    except Exception as e:
        logger.error(f"Failed to delete large data from {metadata.storage_type}: {e}")
        # Don't raise here - deletion is best-effort during cleanup


# Private helper functions for each storage type


def _store_to_s3(config: StorageConfig, file_key: str, data: bytes) -> str:
    """Store data to S3 and return access URL"""
    bucket_name = config.details[StorageDetails.BUCKET.value]
    auth_method = config.details[StorageDetails.AUTH_METHOD.value]

    document = BytesIO(data)
    _, presigned_url = generic_upload_to_s3(
        storage_secrets=config.secrets,
        bucket_name=bucket_name,
        file_key=file_key,
        auth_method=auth_method,
        document=document,
    )
    return str(presigned_url)


def _store_to_gcs(config: StorageConfig, file_key: str, data: bytes) -> str:
    """Store data to GCS and return access URL"""
    bucket_name = config.details[StorageDetails.BUCKET.value]
    auth_method = config.details[StorageDetails.AUTH_METHOD.value]

    storage_client = get_gcs_client(auth_method, config.secrets)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_key)

    blob.upload_from_string(data, content_type="application/json")

    # Return the GCS URL
    return f"gs://{bucket_name}/{file_key}"


def _store_to_local(config: StorageConfig, file_key: str, data: bytes) -> str:
    """Store data to local filesystem and return file path"""
    file_path = get_local_filename(file_key)

    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, "wb") as f:
        f.write(data)

    return file_path


def _retrieve_from_s3(metadata: ExternalStorageMetadata) -> bytes:
    """Retrieve data from S3"""
    # Parse bucket and key from the file_key or URL
    # For now, assume we can reconstruct the storage config from metadata
    # In practice, might need to store more metadata or look up config by storage_key
    raise NotImplementedError("S3 retrieval needs storage config lookup")


def _retrieve_from_gcs(metadata: ExternalStorageMetadata) -> bytes:
    """Retrieve data from GCS"""
    raise NotImplementedError("GCS retrieval needs storage config lookup")


def _retrieve_from_local(metadata: ExternalStorageMetadata) -> bytes:
    """Retrieve data from local filesystem"""
    with open(metadata.url, "rb") as f:
        return f.read()


def _delete_from_s3(metadata: ExternalStorageMetadata) -> None:
    """Delete data from S3"""
    raise NotImplementedError("S3 deletion needs storage config lookup")


def _delete_from_gcs(metadata: ExternalStorageMetadata) -> None:
    """Delete data from GCS"""
    raise NotImplementedError("GCS deletion needs storage config lookup")


def _delete_from_local(metadata: ExternalStorageMetadata) -> None:
    """Delete data from local filesystem"""
    try:
        if os.path.exists(metadata.url):
            os.remove(metadata.url)
    except OSError as e:
        logger.warning(f"Failed to delete local file {metadata.url}: {e}")
