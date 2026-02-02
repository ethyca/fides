"""
S3 Storage Provider implementation.

This module provides an S3 implementation of the StorageProvider interface.
It uses the Adapter pattern to wrap existing S3 functions, ensuring behavioral
compatibility while providing a unified interface.
"""

from io import BytesIO
from typing import IO, Any, Dict, Iterator, Optional

from botocore.exceptions import ClientError, ParamValidationError
from loguru import logger

from fides.api.service.storage.providers.base import (
    ObjectInfo,
    StorageProvider,
    UploadResult,
)
from fides.api.service.storage.s3 import (
    create_presigned_url_for_s3,
    generic_delete_from_s3,
    generic_retrieve_from_s3,
    generic_upload_to_s3,
    get_file_size,
    maybe_get_s3_client,
)


class S3StorageProvider(StorageProvider):
    """S3 implementation of the StorageProvider interface.

    This provider uses the Adapter pattern to wrap existing S3 functions,
    ensuring backward compatibility while providing a unified interface.

    Attributes:
        auth_method: The AWS authentication method (e.g., "secret_keys", "automatic").
        secrets: Dictionary containing AWS credentials and configuration.

    Example:
        ```python
        provider = S3StorageProvider(
            auth_method="secret_keys",
            secrets={
                "aws_access_key_id": "...",
                "aws_secret_access_key": "...",
                "region_name": "us-east-1",
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
        """Initialize the S3 storage provider.

        Args:
            auth_method: The AWS authentication method.
            secrets: Optional dictionary containing AWS credentials.
        """
        self._auth_method = auth_method
        self._secrets = secrets or {}
        logger.debug(
            "Initialized S3StorageProvider with auth_method={}",
            auth_method,
        )

    def upload(
        self,
        bucket: str,
        key: str,
        data: IO[bytes],
        content_type: Optional[str] = None,
    ) -> UploadResult:
        """Upload data to S3.

        Delegates to generic_upload_to_s3 for backward compatibility.

        Args:
            bucket: S3 bucket name.
            key: Object key/path.
            data: File-like object containing the data.
            content_type: Optional MIME type (auto-detected from key if not provided).

        Returns:
            UploadResult with file size and presigned URL.
        """
        logger.debug("S3StorageProvider.upload: bucket={}, key={}", bucket, key)

        file_size, presigned_url = generic_upload_to_s3(
            storage_secrets=self._secrets,
            bucket_name=bucket,
            file_key=key,
            auth_method=self._auth_method,
            document=data,
        )

        return UploadResult(
            file_size=file_size,
            location=presigned_url,
        )

    def download(self, bucket: str, key: str) -> IO[bytes]:
        """Download data from S3.

        Delegates to generic_retrieve_from_s3 with get_content=True.

        Args:
            bucket: S3 bucket name.
            key: Object key/path.

        Returns:
            BytesIO containing the downloaded data.
        """
        logger.debug("S3StorageProvider.download: bucket={}, key={}", bucket, key)

        _, content = generic_retrieve_from_s3(
            storage_secrets=self._secrets,
            bucket_name=bucket,
            file_key=key,
            auth_method=self._auth_method,
            get_content=True,
        )

        # Ensure we return a file-like object
        if isinstance(content, bytes):
            return BytesIO(content)
        return content

    def delete(self, bucket: str, key: str) -> None:
        """Delete a single object from S3.

        Delegates to generic_delete_from_s3.

        Args:
            bucket: S3 bucket name.
            key: Object key/path.
        """
        logger.debug("S3StorageProvider.delete: bucket={}, key={}", bucket, key)

        generic_delete_from_s3(
            storage_secrets=self._secrets,
            bucket_name=bucket,
            file_key=key,
            auth_method=self._auth_method,
        )

    def delete_prefix(self, bucket: str, prefix: str) -> None:
        """Delete all objects with the given prefix.

        Ensures prefix ends with '/' and delegates to generic_delete_from_s3.

        Args:
            bucket: S3 bucket name.
            prefix: The prefix to match (will append '/' if not present).
        """
        logger.debug(
            "S3StorageProvider.delete_prefix: bucket={}, prefix={}", bucket, prefix
        )

        # Ensure prefix ends with / for folder deletion
        if not prefix.endswith("/"):
            prefix = f"{prefix}/"

        generic_delete_from_s3(
            storage_secrets=self._secrets,
            bucket_name=bucket,
            file_key=prefix,
            auth_method=self._auth_method,
        )

    def generate_presigned_url(
        self,
        bucket: str,
        key: str,
        ttl_seconds: Optional[int] = None,
    ) -> str:
        """Generate a presigned URL for S3 object access.

        Args:
            bucket: S3 bucket name.
            key: Object key/path.
            ttl_seconds: Time-to-live in seconds (max 7 days = 604800).

        Returns:
            Presigned URL string.
        """
        logger.debug(
            "S3StorageProvider.generate_presigned_url: bucket={}, key={}, ttl={}",
            bucket,
            key,
            ttl_seconds,
        )

        s3_client = maybe_get_s3_client(self._auth_method, self._secrets)
        return create_presigned_url_for_s3(
            s3_client=s3_client,
            bucket_name=bucket,
            file_key=key,
            ttl_seconds=ttl_seconds,
        )

    def get_file_size(self, bucket: str, key: str) -> int:
        """Get the size of an S3 object in bytes.

        Args:
            bucket: S3 bucket name.
            key: Object key/path.

        Returns:
            File size in bytes.
        """
        logger.debug("S3StorageProvider.get_file_size: bucket={}, key={}", bucket, key)

        s3_client = maybe_get_s3_client(self._auth_method, self._secrets)
        return get_file_size(s3_client, bucket, key)

    def exists(self, bucket: str, key: str) -> bool:
        """Check if an object exists in S3.

        Args:
            bucket: S3 bucket name.
            key: Object key/path.

        Returns:
            True if the object exists, False otherwise.
        """
        logger.debug("S3StorageProvider.exists: bucket={}, key={}", bucket, key)

        try:
            s3_client = maybe_get_s3_client(self._auth_method, self._secrets)
            s3_client.head_object(Bucket=bucket, Key=key)
            return True
        except (ClientError, ParamValidationError):
            return False

    def list_objects(self, bucket: str, prefix: str) -> Iterator[ObjectInfo]:
        """List objects in S3 with the given prefix.

        Uses pagination to handle large result sets efficiently.

        Args:
            bucket: S3 bucket name.
            prefix: The prefix to filter objects by.

        Yields:
            ObjectInfo for each matching object.
        """
        logger.debug(
            "S3StorageProvider.list_objects: bucket={}, prefix={}", bucket, prefix
        )

        s3_client = maybe_get_s3_client(self._auth_method, self._secrets)
        paginator = s3_client.get_paginator("list_objects_v2")

        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            if "Contents" in page:
                for obj in page["Contents"]:
                    yield ObjectInfo(
                        key=obj["Key"],
                        size=obj["Size"],
                        last_modified=obj.get("LastModified"),
                        etag=obj.get("ETag"),
                    )

    def stream_upload(self, bucket: str, key: str) -> Any:
        """Get a writable stream for S3 upload.

        Uses smart-open for efficient streaming uploads.

        Args:
            bucket: S3 bucket name.
            key: Object key/path.

        Returns:
            A writable file-like object.
        """
        try:
            from fides.api.service.storage.streaming.smart_open_client import (
                SmartOpenStorageClient,
            )

            client = SmartOpenStorageClient(
                storage_type="s3",
                auth_method=self._auth_method,
                storage_secrets=self._secrets,
            )
            return client.stream_upload(bucket, key)
        except ImportError as exc:
            raise NotImplementedError(
                "Streaming uploads require the smart-open library"
            ) from exc

    def stream_download(self, bucket: str, key: str) -> Any:
        """Get a readable stream for S3 download.

        Uses smart-open for efficient streaming downloads.

        Args:
            bucket: S3 bucket name.
            key: Object key/path.

        Returns:
            A readable file-like object.
        """
        try:
            from fides.api.service.storage.streaming.smart_open_client import (
                SmartOpenStorageClient,
            )

            client = SmartOpenStorageClient(
                storage_type="s3",
                auth_method=self._auth_method,
                storage_secrets=self._secrets,
            )
            return client.stream_read(bucket, key)
        except ImportError as exc:
            raise NotImplementedError(
                "Streaming downloads require the smart-open library"
            ) from exc
