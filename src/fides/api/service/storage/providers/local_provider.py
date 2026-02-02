"""
Local Storage Provider implementation.

This module provides a local filesystem implementation of the StorageProvider interface.
It is primarily intended for development and testing purposes.
"""

import os
import shutil
from datetime import datetime
from io import BytesIO
from typing import IO, Iterator, Optional

from loguru import logger

from fides.api.service.storage.providers.base import (
    ObjectInfo,
    StorageProvider,
    UploadResult,
)
from fides.api.service.storage.util import (
    LOCAL_FIDES_UPLOAD_DIRECTORY,
    get_local_filename,
)


class LocalStorageProvider(StorageProvider):
    """Local filesystem implementation of the StorageProvider interface.

    This provider stores files on the local filesystem and is intended
    primarily for development, testing, and demo purposes. It should
    not be used in production environments.

    The bucket parameter is typically ignored for local storage, as all
    files are stored under the LOCAL_FIDES_UPLOAD_DIRECTORY.

    Example:
        ```python
        provider = LocalStorageProvider()

        result = provider.upload("", "file.pdf", file_data)
        content = provider.download("", "file.pdf")
        ```
    """

    def __init__(self, base_path: Optional[str] = None):
        """Initialize the local storage provider.

        Args:
            base_path: Optional base path override. Defaults to LOCAL_FIDES_UPLOAD_DIRECTORY.
        """
        self._base_path = base_path or LOCAL_FIDES_UPLOAD_DIRECTORY
        logger.debug(
            "Initialized LocalStorageProvider with base_path={}", self._base_path
        )

    def _get_file_path(self, key: str) -> str:
        """Get the full file path for a given key.

        Uses get_local_filename for path traversal protection.

        Args:
            key: Object key/path.

        Returns:
            Full file path.
        """
        return get_local_filename(key)

    def upload(
        self,
        bucket: str,
        key: str,
        data: IO[bytes],
        content_type: Optional[str] = None,
    ) -> UploadResult:
        """Upload data to local filesystem.

        Args:
            bucket: Ignored for local storage.
            key: File key/path.
            data: File-like object containing the data.
            content_type: Ignored for local storage.

        Returns:
            UploadResult with file size.
        """
        logger.debug("LocalStorageProvider.upload: key={}", key)

        file_path = self._get_file_path(key)

        # Validate that data is a file-like object
        if not hasattr(data, "read"):
            raise TypeError(f"Expected a file-like object, got {type(data)}")

        # Reset file pointer to beginning
        try:
            data.seek(0)
        except (OSError, IOError) as e:
            raise ValueError(f"Failed to reset file pointer: {e}") from e

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Write the file in chunks for memory efficiency
        file_size = 0
        with open(file_path, "wb") as f:
            for chunk in iter(lambda: data.read(1024 * 1024), b""):  # 1MB chunks
                if not isinstance(chunk, bytes):
                    raise TypeError(f"Expected bytes, got {type(chunk)}")
                f.write(chunk)
                file_size += len(chunk)

        logger.info(f"Uploaded {key} to local storage at {file_path}")

        return UploadResult(
            file_size=file_size,
            location=file_path,
        )

    def download(self, bucket: str, key: str) -> IO[bytes]:
        """Download data from local filesystem.

        Args:
            bucket: Ignored for local storage.
            key: File key/path.

        Returns:
            BytesIO containing the file contents.
        """
        logger.debug("LocalStorageProvider.download: key={}", key)

        file_path = self._get_file_path(key)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "rb") as f:
            content = BytesIO(f.read())
            content.seek(0)
            return content

    def delete(self, bucket: str, key: str) -> None:
        """Delete a file from local filesystem.

        Args:
            bucket: Ignored for local storage.
            key: File key/path.
        """
        logger.debug("LocalStorageProvider.delete: key={}", key)

        file_path = self._get_file_path(key)

        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Deleted {key} from local storage")

    def delete_prefix(self, bucket: str, prefix: str) -> None:
        """Delete all files with the given prefix (directory).

        Args:
            bucket: Ignored for local storage.
            prefix: The prefix/directory to delete.
        """
        logger.debug("LocalStorageProvider.delete_prefix: prefix={}", prefix)

        # Construct the directory path
        dir_path = os.path.join(self._base_path, prefix.rstrip("/"))

        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            shutil.rmtree(dir_path)
            logger.info(f"Deleted directory {prefix} from local storage")

    def generate_presigned_url(
        self,
        bucket: str,
        key: str,
        ttl_seconds: Optional[int] = None,
    ) -> str:
        """Return the local file path as the "presigned URL".

        For local storage, we simply return the file path since there's
        no actual URL signing needed.

        Args:
            bucket: Ignored for local storage.
            key: File key/path.
            ttl_seconds: Ignored for local storage.

        Returns:
            Local file path.
        """
        logger.debug("LocalStorageProvider.generate_presigned_url: key={}", key)

        return self._get_file_path(key)

    def get_file_size(self, bucket: str, key: str) -> int:
        """Get the size of a local file in bytes.

        Args:
            bucket: Ignored for local storage.
            key: File key/path.

        Returns:
            File size in bytes.
        """
        logger.debug("LocalStorageProvider.get_file_size: key={}", key)

        file_path = self._get_file_path(key)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        return os.path.getsize(file_path)

    def exists(self, bucket: str, key: str) -> bool:
        """Check if a file exists in local filesystem.

        Args:
            bucket: Ignored for local storage.
            key: File key/path.

        Returns:
            True if the file exists, False otherwise.
        """
        logger.debug("LocalStorageProvider.exists: key={}", key)

        try:
            file_path = self._get_file_path(key)
            return os.path.exists(file_path)
        except ValueError:
            # Invalid path (e.g., path traversal attempt)
            return False

    def list_objects(self, bucket: str, prefix: str) -> Iterator[ObjectInfo]:
        """List files in local filesystem with the given prefix.

        Args:
            bucket: Ignored for local storage.
            prefix: The prefix/directory to list.

        Yields:
            ObjectInfo for each matching file.
        """
        logger.debug("LocalStorageProvider.list_objects: prefix={}", prefix)

        dir_path = os.path.join(self._base_path, prefix.rstrip("/"))

        if not os.path.exists(dir_path):
            return

        if os.path.isfile(dir_path):
            # Single file matches
            stat = os.stat(dir_path)
            yield ObjectInfo(
                key=prefix,
                size=stat.st_size,
                last_modified=datetime.fromtimestamp(stat.st_mtime),
            )
            return

        # Walk the directory tree
        for root, _, files in os.walk(dir_path):
            for filename in files:
                file_path = os.path.join(root, filename)
                relative_path = os.path.relpath(file_path, self._base_path)
                stat = os.stat(file_path)

                yield ObjectInfo(
                    key=relative_path,
                    size=stat.st_size,
                    last_modified=datetime.fromtimestamp(stat.st_mtime),
                )
