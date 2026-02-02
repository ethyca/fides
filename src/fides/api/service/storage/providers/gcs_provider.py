"""
GCS (Google Cloud Storage) Provider implementation.

This module provides a GCS implementation of the StorageProvider interface.
It uses the Adapter pattern to wrap existing GCS functions, ensuring behavioral
compatibility while providing a unified interface.
"""

from datetime import timedelta
from io import BytesIO
from typing import IO, Any, Dict, Iterator, Optional

from loguru import logger

from fides.api.service.storage.providers.base import (
    ObjectInfo,
    StorageProvider,
    UploadResult,
)
from fides.api.service.storage.gcs import get_gcs_client

# Maximum TTL for signed URLs (7 days in seconds)
MAX_TTL_SECONDS = 604800


class GCSStorageProvider(StorageProvider):
    """GCS implementation of the StorageProvider interface.

    This provider uses the Adapter pattern to wrap existing GCS functions,
    ensuring backward compatibility while providing a unified interface.

    Attributes:
        auth_method: The GCS authentication method (e.g., "adc", "service_account_keys").
        secrets: Dictionary containing GCS credentials and configuration.

    Example:
        ```python
        provider = GCSStorageProvider(
            auth_method="service_account_keys",
            secrets={
                "type": "service_account",
                "project_id": "...",
                "private_key": "...",
                # ... other service account fields
            }
        )

        result = provider.upload("my-bucket", "file.pdf", file_data)
        ```
    """

    def __init__(
        self,
        auth_method: str,
        secrets: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the GCS storage provider.

        Args:
            auth_method: The GCS authentication method.
            secrets: Optional dictionary containing GCS credentials.
        """
        self._auth_method = auth_method
        self._secrets = secrets
        self._client = None  # Lazy initialization
        logger.debug(
            "Initialized GCSStorageProvider with auth_method={}",
            auth_method,
        )

    def _get_client(self) -> Any:
        """Get or create the GCS client.

        Returns:
            Google Cloud Storage client.
        """
        if self._client is None:
            self._client = get_gcs_client(self._auth_method, self._secrets)
        return self._client

    def _get_blob(self, bucket: str, key: str) -> Any:
        """Get a blob reference for the given bucket and key.

        Args:
            bucket: GCS bucket name.
            key: Object key/path.

        Returns:
            GCS Blob object.
        """
        client = self._get_client()
        bucket_obj = client.bucket(bucket)
        return bucket_obj.blob(key)

    def upload(
        self,
        bucket: str,
        key: str,
        data: IO[bytes],
        content_type: Optional[str] = None,
    ) -> UploadResult:
        """Upload data to GCS.

        Args:
            bucket: GCS bucket name.
            key: Object key/path.
            data: File-like object containing the data.
            content_type: Optional MIME type.

        Returns:
            UploadResult with file size.
        """
        logger.debug("GCSStorageProvider.upload: bucket={}, key={}", bucket, key)

        # Validate that data is a file-like object
        if not hasattr(data, "read"):
            raise TypeError(f"Expected a file-like object, got {type(data)}")

        blob = self._get_blob(bucket, key)

        # Reset file pointer to beginning
        try:
            data.seek(0)
        except (OSError, IOError) as e:
            raise ValueError(f"Failed to reset file pointer: {e}") from e

        # Read content to get size
        content = data.read()
        file_size = len(content)

        # Upload using upload_from_string for bytes
        blob.upload_from_string(
            content,
            content_type=content_type or "application/octet-stream",
        )

        logger.info(f"Uploaded {key} to GCS bucket {bucket}")

        return UploadResult(
            file_size=file_size,
            etag=blob.etag,
        )

    def download(self, bucket: str, key: str) -> IO[bytes]:
        """Download data from GCS.

        Args:
            bucket: GCS bucket name.
            key: Object key/path.

        Returns:
            BytesIO containing the downloaded data.
        """
        logger.debug("GCSStorageProvider.download: bucket={}, key={}", bucket, key)

        blob = self._get_blob(bucket, key)

        file_obj = BytesIO()
        blob.download_to_file(file_obj)
        file_obj.seek(0)

        return file_obj

    def delete(self, bucket: str, key: str) -> None:
        """Delete a single object from GCS.

        Args:
            bucket: GCS bucket name.
            key: Object key/path.
        """
        logger.debug("GCSStorageProvider.delete: bucket={}, key={}", bucket, key)

        blob = self._get_blob(bucket, key)

        try:
            blob.delete()
        except (AttributeError, RuntimeError) as e:
            # Log but don't raise for non-existent objects
            logger.warning(f"Error deleting GCS object {key}: {e}")

    def delete_prefix(self, bucket: str, prefix: str) -> None:
        """Delete all objects with the given prefix.

        Args:
            bucket: GCS bucket name.
            prefix: The prefix to match.
        """
        logger.debug(
            "GCSStorageProvider.delete_prefix: bucket={}, prefix={}", bucket, prefix
        )

        client = self._get_client()
        bucket_obj = client.bucket(bucket)

        # Ensure prefix ends with / for folder deletion
        if not prefix.endswith("/"):
            prefix = f"{prefix}/"

        # List and delete all blobs with the prefix
        blobs = bucket_obj.list_blobs(prefix=prefix)
        for blob in blobs:
            try:
                blob.delete()
            except (AttributeError, RuntimeError) as e:
                logger.warning(f"Error deleting GCS object {blob.name}: {e}")

    def generate_presigned_url(
        self,
        bucket: str,
        key: str,
        ttl_seconds: Optional[int] = None,
    ) -> str:
        """Generate a signed URL for GCS object access.

        Args:
            bucket: GCS bucket name.
            key: Object key/path.
            ttl_seconds: Time-to-live in seconds (max 7 days = 604800).

        Returns:
            Signed URL string.
        """
        logger.debug(
            "GCSStorageProvider.generate_presigned_url: bucket={}, key={}, ttl={}",
            bucket,
            key,
            ttl_seconds,
        )

        # Validate TTL
        if ttl_seconds is not None and ttl_seconds > MAX_TTL_SECONDS:
            raise ValueError("TTL must be less than 7 days")

        # Use default if not specified (7 days)
        expiration = ttl_seconds if ttl_seconds else MAX_TTL_SECONDS

        blob = self._get_blob(bucket, key)

        # Reload blob metadata to ensure we have the latest
        try:
            blob.reload()
        except (AttributeError, RuntimeError):
            pass  # Blob may not exist yet, that's okay for URL generation

        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=expiration),
            method="GET",
        )

        return url

    def get_file_size(self, bucket: str, key: str) -> int:
        """Get the size of a GCS object in bytes.

        Args:
            bucket: GCS bucket name.
            key: Object key/path.

        Returns:
            File size in bytes.
        """
        logger.debug("GCSStorageProvider.get_file_size: bucket={}, key={}", bucket, key)

        blob = self._get_blob(bucket, key)
        blob.reload()  # Fetch metadata

        return blob.size

    def exists(self, bucket: str, key: str) -> bool:
        """Check if an object exists in GCS.

        Args:
            bucket: GCS bucket name.
            key: Object key/path.

        Returns:
            True if the object exists, False otherwise.
        """
        logger.debug("GCSStorageProvider.exists: bucket={}, key={}", bucket, key)

        blob = self._get_blob(bucket, key)
        return blob.exists()

    def list_objects(self, bucket: str, prefix: str) -> Iterator[ObjectInfo]:
        """List objects in GCS with the given prefix.

        Args:
            bucket: GCS bucket name.
            prefix: The prefix to filter objects by.

        Yields:
            ObjectInfo for each matching object.
        """
        logger.debug(
            "GCSStorageProvider.list_objects: bucket={}, prefix={}", bucket, prefix
        )

        client = self._get_client()
        bucket_obj = client.bucket(bucket)

        blobs = bucket_obj.list_blobs(prefix=prefix)
        for blob in blobs:
            yield ObjectInfo(
                key=blob.name,
                size=blob.size or 0,
                last_modified=blob.updated,
                etag=blob.etag,
            )
