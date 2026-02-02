"""
Base abstract class for storage providers.

This module defines the unified interface that all storage provider implementations
must follow. It uses the Strategy pattern to allow interchangeable storage backends.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import IO, Any, Iterator, Optional


@dataclass
class UploadResult:
    """Result of an upload operation.

    Attributes:
        file_size: Size of the uploaded file in bytes.
        etag: Optional entity tag (hash) of the uploaded content.
        location: Optional URL or path where the file was stored.
    """

    file_size: int
    etag: Optional[str] = None
    location: Optional[str] = None


@dataclass
class ObjectInfo:
    """Information about a stored object.

    Attributes:
        key: The object key/path within the bucket.
        size: Size of the object in bytes.
        last_modified: Optional timestamp when the object was last modified.
        etag: Optional entity tag (hash) of the content.
    """

    key: str
    size: int
    last_modified: Optional[datetime] = None
    etag: Optional[str] = None


class StorageProvider(ABC):
    """Unified abstract interface for all storage providers.

    This abstract base class defines the contract that all storage provider
    implementations (S3, GCS, Local) must follow. It provides a consistent
    interface for storage operations regardless of the underlying backend.

    Implementations should:
    - Handle authentication internally based on provided configuration
    - Raise appropriate exceptions for error cases
    - Support both streaming and in-memory operations where applicable

    Example:
        ```python
        provider = S3StorageProvider(auth_method="secret_keys", secrets=secrets)

        # Upload a file
        result = provider.upload("my-bucket", "path/to/file.pdf", file_data)

        # Download a file
        content = provider.download("my-bucket", "path/to/file.pdf")

        # Generate a presigned URL
        url = provider.generate_presigned_url("my-bucket", "path/to/file.pdf")

        # Delete a file
        provider.delete("my-bucket", "path/to/file.pdf")
        ```
    """

    @abstractmethod
    def upload(
        self,
        bucket: str,
        key: str,
        data: IO[bytes],
        content_type: Optional[str] = None,
    ) -> UploadResult:
        """Upload data to storage.

        Args:
            bucket: The storage bucket/container name.
            key: The object key/path within the bucket.
            data: A file-like object containing the data to upload.
            content_type: Optional MIME type of the content.

        Returns:
            UploadResult containing file size and optional metadata.

        Raises:
            StorageUploadError: If the upload fails.
            TypeError: If data is not a file-like object.
        """

    @abstractmethod
    def download(self, bucket: str, key: str) -> IO[bytes]:
        """Download data from storage.

        Args:
            bucket: The storage bucket/container name.
            key: The object key/path within the bucket.

        Returns:
            A file-like object containing the downloaded data.

        Raises:
            StorageUploadError: If the download fails.
            FileNotFoundError: If the object does not exist.
        """

    @abstractmethod
    def delete(self, bucket: str, key: str) -> None:
        """Delete an object from storage.

        Args:
            bucket: The storage bucket/container name.
            key: The object key/path within the bucket.

        Raises:
            StorageUploadError: If the deletion fails.

        Note:
            Deleting a non-existent object should not raise an error.
        """

    @abstractmethod
    def delete_prefix(self, bucket: str, prefix: str) -> None:
        """Delete all objects with the given prefix.

        Args:
            bucket: The storage bucket/container name.
            prefix: The prefix to match (e.g., "folder/" deletes all in folder).

        Raises:
            StorageUploadError: If the deletion fails.

        Note:
            This is useful for cleaning up attachment folders or grouped files.
        """

    @abstractmethod
    def generate_presigned_url(
        self,
        bucket: str,
        key: str,
        ttl_seconds: Optional[int] = None,
    ) -> str:
        """Generate a presigned/signed URL for accessing the object.

        Args:
            bucket: The storage bucket/container name.
            key: The object key/path within the bucket.
            ttl_seconds: Time-to-live in seconds. Defaults to configured value.
                         Maximum is typically 7 days (604800 seconds).

        Returns:
            A presigned URL string for accessing the object.
            For local storage, returns the local file path.

        Raises:
            ValueError: If ttl_seconds exceeds the maximum allowed.
            StorageUploadError: If URL generation fails.
        """

    @abstractmethod
    def get_file_size(self, bucket: str, key: str) -> int:
        """Get the size of an object in bytes.

        Args:
            bucket: The storage bucket/container name.
            key: The object key/path within the bucket.

        Returns:
            The size of the object in bytes.

        Raises:
            FileNotFoundError: If the object does not exist.
            StorageUploadError: If the operation fails.
        """

    @abstractmethod
    def exists(self, bucket: str, key: str) -> bool:
        """Check if an object exists in storage.

        Args:
            bucket: The storage bucket/container name.
            key: The object key/path within the bucket.

        Returns:
            True if the object exists, False otherwise.
        """

    @abstractmethod
    def list_objects(self, bucket: str, prefix: str) -> Iterator[ObjectInfo]:
        """List objects with the given prefix.

        Args:
            bucket: The storage bucket/container name.
            prefix: The prefix to filter objects by.

        Yields:
            ObjectInfo for each matching object.

        Note:
            This method yields results lazily for memory efficiency.
        """

    def stream_upload(self, bucket: str, key: str) -> Any:
        """Get a writable stream for uploading data.

        This method is optional and may not be implemented by all providers.
        It enables memory-efficient streaming uploads for large files.

        Args:
            bucket: The storage bucket/container name.
            key: The object key/path within the bucket.

        Returns:
            A writable file-like object.

        Raises:
            NotImplementedError: If streaming is not supported.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support streaming uploads"
        )

    def stream_download(self, bucket: str, key: str) -> Any:
        """Get a readable stream for downloading data.

        This method is optional and may not be implemented by all providers.
        It enables memory-efficient streaming downloads for large files.

        Args:
            bucket: The storage bucket/container name.
            key: The object key/path within the bucket.

        Returns:
            A readable file-like object.

        Raises:
            NotImplementedError: If streaming is not supported.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support streaming downloads"
        )
