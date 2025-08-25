"""Smart-open based storage client for cloud storage operations."""

from __future__ import annotations

from typing import Any, Optional

import smart_open
from fideslang.validation import AnyHttpUrlString
from loguru import logger

from fides.api.service.storage.streaming.retry import retry_cloud_storage_operation
from fides.api.service.storage.streaming.schemas import (
    MIN_PART_SIZE,
    MultipartUploadResponse,
    UploadPartResponse,
)
from fides.api.service.storage.streaming.storage_client_factory import (
    StorageClientFactory,
)


class SmartOpenStorageClient:
    """Smart-open based storage client that supports multiple cloud providers.

    This client uses smart-open for efficient streaming I/O operations while maintaining
    compatibility with our existing storage interface. It delegates provider-specific
    logic to specialized client implementations.
    """

    min_part_size: int = MIN_PART_SIZE

    def __init__(self, storage_type: str, storage_secrets: Any):
        """Initialize the smart-open storage client.

        Args:
            storage_type: Type of storage ('s3', 'gcs', 'azure')
            storage_secrets: Storage credentials and configuration.
                           Will be passed to the specific storage client implementation.
        """
        self.storage_type = StorageClientFactory._normalize_storage_type(storage_type)
        self.storage_secrets = storage_secrets
        self._provider_client = StorageClientFactory.create_client(
            storage_type, storage_secrets
        )

    def _build_uri(self, bucket: str, key: str) -> str:
        """Build the URI for the storage location.

        Args:
            bucket: Storage bucket/container name
            key: Object key/path

        Returns:
            URI string for smart-open
        """
        return self._provider_client.build_uri(bucket, key)

    def _get_transport_params(self) -> dict[str, Any]:
        """Get transport parameters for smart-open based on storage type and secrets.

        Returns:
            Dictionary of transport parameters for smart-open
        """
        return self._provider_client.get_transport_params()

    @retry_cloud_storage_operation(
        provider="smart_open_storage",
        operation_name="put_object",
        max_retries=3,
        base_delay=2.0,
        max_delay=30.0,
    )
    def put_object(
        self,
        bucket: str,
        key: str,
        body: Any,
        content_type: Optional[str] = None,
    ) -> dict[str, Any]:
        """Upload an object to storage using smart-open.

        Args:
            bucket: Storage bucket/container name
            key: Object key/path
            body: Object content (file-like object, bytes, or string)
            content_type: MIME type of the object

        Returns:
            Response dictionary with upload result
        """
        uri = self._build_uri(bucket, key)
        transport_params = self._get_transport_params()

        # Handle content type and metadata
        if content_type:
            transport_params["content_type"] = content_type

        try:
            with smart_open.open(uri, "wb", transport_params=transport_params) as fout:
                if hasattr(body, "read"):
                    # File-like object
                    fout.write(body.read())
                elif isinstance(body, (bytes, bytearray)):
                    # Bytes
                    fout.write(body)
                elif isinstance(body, str):
                    # String
                    fout.write(body.encode("utf-8"))
                else:
                    # Try to convert to string
                    fout.write(str(body).encode("utf-8"))

            logger.debug(f"Successfully uploaded object to {uri}")
            return {"status": "success", "uri": uri}

        except Exception as e:
            logger.error(f"Failed to upload object to {uri}: {e}")
            raise

    @retry_cloud_storage_operation(
        provider="smart_open_storage",
        operation_name="get_object",
        max_retries=3,
        base_delay=2.0,
        max_delay=30.0,
    )
    def get_object(self, bucket: str, key: str) -> bytes:
        """Get the full content of an object using smart-open.

        Args:
            bucket: Storage bucket/container name
            key: Object key/path

        Returns:
            Object content as bytes
        """
        uri = self._build_uri(bucket, key)
        transport_params = self._get_transport_params()

        try:
            with smart_open.open(uri, "rb", transport_params=transport_params) as fin:
                return fin.read()

        except Exception as e:
            logger.error(f"Failed to read object from {uri}: {e}")
            raise

    def generate_presigned_url(
        self, bucket: str, key: str, ttl_seconds: Optional[int] = None
    ) -> AnyHttpUrlString:
        """Generate a presigned URL for the object.

        Args:
            bucket: Storage bucket/container name
            key: Object key/path
            ttl_seconds: Time to live in seconds

        Returns:
            Presigned URL for the object

        Raises:
            Exception: If presigned URL generation fails
        """
        return self._provider_client.generate_presigned_url(bucket, key, ttl_seconds)

    # Multipart upload methods - these are simplified since smart-open handles streaming
    def create_multipart_upload(
        self,
        bucket: str,
        key: str,
        content_type: str,
        metadata: Optional[dict[str, str]] = None,
    ) -> MultipartUploadResponse:
        """Create a multipart upload (simplified for smart-open).

        Since smart-open handles streaming efficiently, we don't need complex multipart logic.
        This method exists for compatibility but delegates to put_object.
        """
        # Return a dummy response for compatibility
        return MultipartUploadResponse(
            upload_id="smart_open_streaming",
            metadata={"storage_type": self.storage_type, "method": "streaming"},
        )

    def upload_part(
        self,
        bucket: str,
        key: str,
        upload_id: str,
        part_number: int,
        body: bytes,
    ) -> UploadPartResponse:
        """Upload a part (simplified for smart-open).

        Since smart-open handles streaming efficiently, we don't need complex multipart logic.
        This method exists for compatibility but delegates to put_object.
        """
        # For smart-open, we just upload the part directly
        part_key = f"{key}.part{part_number}"
        self.put_object(bucket, part_key, body)

        return UploadPartResponse(
            part_number=part_number,
            etag=f"smart_open_part_{part_number}",
            metadata={"storage_type": self.storage_type, "method": "streaming"},
        )

    @retry_cloud_storage_operation(
        provider="smart_open_storage",
        operation_name="stream_upload",
        max_retries=3,
        base_delay=2.0,
        max_delay=30.0,
    )
    def stream_upload(
        self,
        bucket: str,
        key: str,
        content_type: Optional[str] = None,
    ) -> Any:
        """Get a writable stream for uploading data.

        This is the main advantage of smart-open - true streaming uploads.

        Args:
            bucket: Storage bucket/container name
            key: Object key/path
            content_type: MIME type of the object

        Returns:
            Writable file-like object
        """
        uri = self._build_uri(bucket, key)
        transport_params = self._get_transport_params()

        if content_type:
            transport_params["content_type"] = content_type

        return smart_open.open(uri, "wb", transport_params=transport_params)

    @retry_cloud_storage_operation(
        provider="smart_open_storage",
        operation_name="stream_read",
        max_retries=3,
        base_delay=2.0,
        max_delay=30.0,
    )
    def stream_read(
        self,
        bucket: str,
        key: str,
    ) -> Any:
        """Get a readable stream for streaming data from cloud storage.

        Args:
            bucket: Storage bucket/container name
            key: Object key/path

        Returns:
            Readable file-like object for streaming content
        """
        uri = self._build_uri(bucket, key)
        transport_params = self._get_transport_params()

        return smart_open.open(uri, "rb", transport_params=transport_params)
