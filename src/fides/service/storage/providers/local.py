import os
from io import BytesIO
from typing import IO, Any, Dict, Optional, Union

import smart_open
from fideslang.validation import AnyHttpUrlString
from loguru import logger

from fides.api.service.storage.util import (
    LOCAL_FIDES_UPLOAD_DIRECTORY,
    get_local_filename,
)

from .base import StorageMetadata, StorageProvider, StorageResponse


class LocalStorageProvider(StorageProvider):
    """
    Local filesystem storage provider implementation using smart_open for consistency.
    Provides secure local file storage with path validation to prevent directory traversal.
    """

    def __init__(self, configuration: Dict[str, Any]):
        super().__init__(configuration)
        self.base_directory = configuration.get(
            "base_directory", LOCAL_FIDES_UPLOAD_DIRECTORY
        )

        # Handle case where base_directory might be None or empty
        if not self.base_directory:
            self.base_directory = LOCAL_FIDES_UPLOAD_DIRECTORY

        # Ensure base directory exists
        os.makedirs(self.base_directory, exist_ok=True)

    def _build_local_uri(self, file_key: str) -> str:
        """Build file URI for smart_open with security validation"""
        # Use existing security validation from get_local_filename
        file_path = get_local_filename(file_key)
        return f"file://{os.path.abspath(file_path)}"

    def _get_local_path(self, file_key: str) -> str:
        """Get validated local file path"""
        return get_local_filename(file_key)

    def store_file(
        self,
        file_content: Union[IO[bytes], bytes, BytesIO],
        file_key: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> StorageResponse:
        """Store a file locally using smart_open for consistency"""
        try:
            uri = self._build_local_uri(file_key)

            with smart_open.open(uri, "wb") as local_file:
                if hasattr(file_content, "read"):
                    # File-like object
                    while chunk := file_content.read(8192):  # 8KB chunks
                        local_file.write(chunk)
                elif isinstance(file_content, (bytes, bytearray)):
                    local_file.write(file_content)
                else:
                    raise ValueError(
                        f"Unsupported file_content type: {type(file_content)}"
                    )

            # Get file size for response
            try:
                file_size = self._get_file_size(file_key)
            except Exception as e:
                logger.warning(f"Could not determine file size for {file_key}: {e}")
                file_size = None

            return StorageResponse(
                success=True,
                file_size=file_size,
                metadata=StorageMetadata(
                    content_type=content_type, custom_metadata=metadata
                ),
            )

        except Exception as e:
            logger.error(f"Failed to store file locally: {e}")
            return StorageResponse(success=False, error_message=str(e))

    def retrieve_file(
        self, file_key: str, get_content: bool = False
    ) -> StorageResponse:
        """Retrieve a file from local storage"""
        try:
            local_path = self._get_local_path(file_key)

            if not os.path.exists(local_path):
                return StorageResponse(
                    success=False, error_message=f"File not found: {file_key}"
                )

            if get_content:
                uri = self._build_local_uri(file_key)

                with smart_open.open(uri, "rb") as local_file:
                    content = local_file.read()

                return StorageResponse(
                    success=True,
                    file_size=len(content),
                    metadata=StorageMetadata(file_size=len(content)),
                )
            else:
                # Just check if file exists and get metadata
                file_size = self._get_file_size(file_key)
                return StorageResponse(
                    success=True,
                    file_size=file_size,
                    metadata=StorageMetadata(file_size=file_size),
                )

        except Exception as e:
            logger.error(f"Failed to retrieve file locally: {e}")
            return StorageResponse(success=False, error_message=str(e))

    def delete_file(self, file_key: str) -> StorageResponse:
        """Delete a file from local storage"""
        try:
            local_path = self._get_local_path(file_key)

            if os.path.exists(local_path):
                os.remove(local_path)

                # Clean up empty parent directories
                parent_dir = os.path.dirname(local_path)
                try:
                    # Only remove if directory is empty and not the base directory
                    if (
                        parent_dir != self.base_directory
                        and os.path.exists(parent_dir)
                        and not os.listdir(parent_dir)
                    ):
                        os.rmdir(parent_dir)
                except OSError:
                    # Directory not empty or other error, ignore
                    pass

            return StorageResponse(success=True)

        except Exception as e:
            logger.error(f"Failed to delete file locally: {e}")
            return StorageResponse(success=False, error_message=str(e))

    def generate_presigned_url(
        self, file_key: str, ttl_seconds: Optional[int] = None
    ) -> AnyHttpUrlString:
        """Generate a local file path (not actually presigned for local storage)"""
        # For local storage, return the local path directly for test compatibility
        # This is mainly for compatibility with the interface
        local_path = self._get_local_path(file_key)
        return local_path

    def stream_upload(self, file_key: str) -> IO[bytes]:
        """Get a writable stream for uploading to local storage"""
        uri = self._build_local_uri(file_key)
        return smart_open.open(uri, "wb")

    def stream_download(self, file_key: str) -> IO[bytes]:
        """Get a readable stream for downloading from local storage"""
        uri = self._build_local_uri(file_key)
        return smart_open.open(uri, "rb")

    def file_exists(self, file_key: str) -> bool:
        """Check if a file exists in local storage"""
        try:
            local_path = self._get_local_path(file_key)
            return os.path.exists(local_path) and os.path.isfile(local_path)
        except Exception:
            return False

    def validate_configuration(self) -> bool:
        """Validate the local storage configuration"""
        try:
            # Check if base directory is accessible and writable
            test_file = os.path.join(self.base_directory, ".storage_test")

            # Try to write a test file
            with open(test_file, "w") as f:
                f.write("test")

            # Try to read it back
            with open(test_file, "r") as f:
                content = f.read()

            # Clean up test file
            os.remove(test_file)

            return content == "test"

        except Exception as e:
            logger.error(f"Local storage configuration validation failed: {e}")
            return False

    def _get_file_size(self, file_key: str) -> Optional[int]:
        """Get the size of a local file"""
        try:
            local_path = self._get_local_path(file_key)
            if os.path.exists(local_path):
                return os.path.getsize(local_path)
            return None
        except Exception:
            return None
