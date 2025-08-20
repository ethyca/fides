from __future__ import annotations

import abc
from typing import Any, Optional, Protocol

from fideslang.validation import AnyHttpUrlString

from fides.api.service.storage.streaming.schemas import (
    MultipartUploadResponse,
    ProcessingMetrics,
    UploadPartResponse,
)


class CloudStorageClient(abc.ABC):
    """Abstract base class for cloud storage operations"""

    @abc.abstractmethod
    def create_multipart_upload(
        self,
        bucket: str,
        key: str,
        content_type: str,
        metadata: Optional[dict[str, str]] = None,
    ) -> MultipartUploadResponse:
        """Initiate a multipart upload"""
        pass  # pragma: no cover  # noqa: W0107

    @abc.abstractmethod
    def upload_part(
        self,
        bucket: str,
        key: str,
        upload_id: str,
        part_number: int,
        body: bytes,
        metadata: Optional[dict[str, str]] = None,
    ) -> UploadPartResponse:
        """Upload a part of a multipart upload"""
        pass  # pragma: no cover  # noqa: W0107

    @abc.abstractmethod
    def complete_multipart_upload(
        self,
        bucket: str,
        key: str,
        upload_id: str,
        parts: list[UploadPartResponse],
        metadata: Optional[dict[str, str]] = None,
    ) -> None:
        """Complete a multipart upload"""
        pass  # pragma: no cover  # noqa: W0107

    @abc.abstractmethod
    def abort_multipart_upload(self, bucket: str, key: str, upload_id: str) -> None:
        """Abort a multipart upload"""
        pass  # pragma: no cover  # noqa: W0107

    @abc.abstractmethod
    def get_object_head(self, bucket: str, key: str) -> dict[str, Any]:
        """Get object metadata (head)"""
        pass  # pragma: no cover  # noqa: W0107

    @abc.abstractmethod
    def get_object_range(
        self, bucket: str, key: str, start_byte: int, end_byte: int
    ) -> bytes:
        """Get a range of bytes from an object"""
        pass  # pragma: no cover  # noqa: W0107

    @abc.abstractmethod
    def generate_presigned_url(
        self, bucket: str, key: str, ttl_seconds: Optional[int] = None
    ) -> AnyHttpUrlString:
        """Generate a presigned URL for the object"""
        pass  # pragma: no cover  # noqa: W0107


class ProgressCallback(Protocol):
    """Protocol for progress callback functions"""

    def __call__(self, metrics: ProcessingMetrics) -> None: ...
