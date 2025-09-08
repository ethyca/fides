from abc import ABC, abstractmethod
from dataclasses import dataclass
from io import BytesIO
from typing import IO, Any, Dict, Optional, Union

from fideslang.validation import AnyHttpUrlString


@dataclass
class StorageMetadata:
    """Metadata for storage operations"""

    content_type: Optional[str] = None
    file_size: Optional[int] = None
    last_modified: Optional[str] = None
    custom_metadata: Optional[Dict[str, str]] = None


@dataclass
class StorageResponse:
    """Response from storage operations"""

    success: bool
    file_size: Optional[int] = None
    presigned_url: Optional[AnyHttpUrlString] = None
    error_message: Optional[str] = None
    metadata: Optional[StorageMetadata] = None


class StorageProvider(ABC):
    """
    Abstract base class for storage provider implementations.
    Each provider (S3, GCS, Local, etc.) implements this interface.
    """

    def __init__(self, configuration: Dict[str, Any]):
        """Initialize the provider with configuration including credentials and settings."""
        self.configuration = configuration

    @abstractmethod
    def store_file(
        self,
        file_content: Union[IO[bytes], bytes, BytesIO],
        file_key: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> StorageResponse:
        """Store a file in storage."""

    @abstractmethod
    def retrieve_file(
        self, file_key: str, get_content: bool = False
    ) -> StorageResponse:
        """Retrieve a file from storage."""

    @abstractmethod
    def delete_file(self, file_key: str) -> StorageResponse:
        """Delete a file from storage."""

    @abstractmethod
    def generate_presigned_url(
        self, file_key: str, ttl_seconds: Optional[int] = None
    ) -> AnyHttpUrlString:
        """Generate a presigned URL for the object."""

    @abstractmethod
    def stream_upload(self, file_key: str) -> IO[bytes]:
        """Get a writable stream for uploading data."""

    @abstractmethod
    def stream_download(self, file_key: str) -> IO[bytes]:
        """Get a readable stream for downloading data."""

    @abstractmethod
    def file_exists(self, file_key: str) -> bool:
        """Check if a file exists in storage."""

    @abstractmethod
    def validate_configuration(self) -> bool:
        """Validate the provider configuration and credentials."""
