from __future__ import annotations

import abc
from typing import Any, Dict, List, Optional, Protocol

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
        metadata: Optional[Dict[str, str]] = None,
    ) -> MultipartUploadResponse:
        """Initiate a multipart upload"""
        pass

    @abc.abstractmethod
    def upload_part(
        self,
        bucket: str,
        key: str,
        upload_id: str,
        part_number: int,
        body: bytes,
        metadata: Optional[Dict[str, str]] = None,
    ) -> UploadPartResponse:
        """Upload a part of a multipart upload"""
        pass

    @abc.abstractmethod
    def complete_multipart_upload(
        self,
        bucket: str,
        key: str,
        upload_id: str,
        parts: List[UploadPartResponse],
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        """Complete a multipart upload"""
        pass

    @abc.abstractmethod
    def abort_multipart_upload(self, bucket: str, key: str, upload_id: str) -> None:
        """Abort a multipart upload"""
        pass

    @abc.abstractmethod
    def get_object_head(self, bucket: str, key: str) -> Dict[str, Any]:
        """Get object metadata (head)"""
        pass

    @abc.abstractmethod
    def get_object_range(
        self, bucket: str, key: str, start_byte: int, end_byte: int
    ) -> bytes:
        """Get a range of bytes from an object"""
        pass

    @abc.abstractmethod
    def generate_presigned_url(
        self, bucket: str, key: str, ttl_seconds: Optional[int] = None
    ) -> str:
        """Generate a presigned URL for the object"""
        pass


class ProgressCallback(Protocol):
    """Protocol for progress callback functions"""

    def __call__(self, metrics: ProcessingMetrics) -> None: ...
