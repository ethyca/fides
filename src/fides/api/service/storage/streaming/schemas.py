from datetime import datetime, timezone
from typing import Annotated, Any, Dict, List, Optional

from pydantic import BaseModel, Field, computed_field, field_validator, model_validator

from fides.api.service.storage.streaming.util import (
    AWS_MIN_PART_SIZE,
    GCS_MIN_CHUNK_SIZE,
)


class AttachmentInfo(BaseModel):
    """Schema for attachment information in streaming storage"""

    s3_key: str = Field(..., description="Storage key for the attachment")
    file_name: Optional[str] = Field(None, description="Human-readable filename")
    size: Optional[int] = Field(None, ge=0, description="File size in bytes")
    content_type: Optional[str] = Field(None, description="MIME type of the file")

    @field_validator("s3_key")
    @classmethod
    def validate_s3_key(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("s3_key cannot be empty or whitespace")
        return v.strip()

    @field_validator("file_name")
    @classmethod
    def validate_file_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and (not v or not v.strip()):
            raise ValueError("file_name cannot be empty or whitespace if provided")
        return v.strip() if v else None


class StorageUploadConfig(BaseModel):
    """Configuration for storage upload operations"""

    bucket_name: str = Field(..., min_length=1, description="Storage bucket name")
    file_key: str = Field(..., min_length=1, description="File key in storage")
    max_workers: int = Field(
        default=5, ge=1, le=20, description="Maximum parallel workers"
    )
    resp_format: str = Field(..., description="Response format (csv, json, html)")

    @field_validator("bucket_name", "file_key")
    @classmethod
    def validate_storage_identifiers(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Storage identifier cannot be empty or whitespace")
        return v.strip()


class ChunkDownloadConfig(BaseModel):
    """Configuration for chunk download operations"""

    start_byte: int = Field(..., ge=0, description="Starting byte position")
    end_byte: int = Field(..., ge=0, description="Ending byte position")
    max_retries: int = Field(
        default=3, ge=1, le=10, description="Maximum retry attempts"
    )

    @model_validator(mode="after")
    def validate_byte_range(self) -> "ChunkDownloadConfig":
        if self.start_byte > self.end_byte:
            raise ValueError("start_byte cannot be greater than end_byte")
        return self


class PackageSplitConfig(BaseModel):
    """Configuration for package splitting operations"""

    max_attachments: int = Field(
        default=100, ge=1, le=1000, description="Max attachments per package"
    )

    @field_validator("max_attachments")
    @classmethod
    def validate_max_attachments(cls, v: int) -> int:
        if v < 1:
            raise ValueError("max_attachments must be at least 1")
        return v


class StreamingBufferConfig(BaseModel):
    """Configuration for streaming buffer operations"""

    zip_buffer_threshold: int = Field(
        default=5 * 1024 * 1024,
        ge=1024 * 1024,
        description="Zip buffer threshold in bytes (default: 5MB)",
    )
    stream_buffer_threshold: int = Field(
        default=512 * 1024,
        ge=1024 * 1024,
        description="Stream buffer threshold in bytes (default: 512KB)",
    )
    chunk_size_threshold: int = Field(
        default=1024 * 1024,
        ge=1024 * 1024,
        description="Chunk size threshold in bytes (default: 1MB)",
    )


class AttachmentProcessingInfo(BaseModel):
    """Information for processing a single attachment"""

    attachment: AttachmentInfo = Field(..., description="Attachment to process")
    base_path: str = Field(..., description="Base path for the attachment in the zip")
    item: Dict[str, Any] = Field(..., description="Associated item data")

    @field_validator("base_path")
    @classmethod
    def validate_base_path(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("base_path cannot be empty or whitespace")
        return v.strip()


class ProcessingMetrics(BaseModel):
    """Metrics for tracking processing progress and performance."""

    total_attachments: int = Field(
        default=0, ge=0, description="Total number of attachments to process"
    )
    processed_attachments: int = Field(
        default=0, ge=0, description="Number of attachments processed so far"
    )
    total_bytes: int = Field(default=0, ge=0, description="Total bytes to process")
    processed_bytes: int = Field(default=0, ge=0, description="Bytes processed so far")
    start_time: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When processing started",
    )
    current_attachment: Optional[str] = Field(
        None, description="Currently processing attachment filename"
    )
    current_attachment_progress: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Current attachment progress percentage",
    )
    errors: List[str] = Field(
        default_factory=list, description="List of error messages encountered"
    )

    @model_validator(mode="after")
    def validate_processed_values(self):
        """Validate that processed values don't exceed total values."""
        if self.processed_attachments > self.total_attachments:
            raise ValueError("processed_attachments cannot exceed total_attachments")

        if self.processed_bytes > self.total_bytes:
            raise ValueError("processed_bytes cannot exceed total_bytes")

        return self

    @computed_field
    def overall_progress(self) -> float:
        """Calculate overall progress percentage."""
        if self.total_attachments == 0:
            return 100.0
        return min(100.0, (self.processed_attachments / self.total_attachments) * 100)

    @computed_field
    def bytes_progress(self) -> float:
        """Calculate bytes processing progress percentage."""
        if self.total_bytes == 0:
            return 100.0
        return min(100.0, (self.processed_bytes / self.total_bytes) * 100)

    @computed_field
    def elapsed_time(self) -> float:
        """Calculate elapsed time in seconds."""
        return (datetime.now(timezone.utc) - self.start_time).total_seconds()

    @computed_field
    def estimated_remaining_time(self) -> float:
        """Estimate remaining time in seconds."""
        if self.overall_progress <= 0:
            return 0.0
        elapsed = self.elapsed_time
        remaining = (elapsed / self.overall_progress) * (100 - self.overall_progress)
        return max(0.0, remaining)

    model_config = {
        "validate_assignment": True,
        "json_schema_extra": {
            "example": {
                "total_attachments": 100,
                "processed_attachments": 45,
                "total_bytes": 1073741824,  # 1GB
                "processed_bytes": 483183820,  # ~460MB
                "current_attachment": "document.pdf",
                "current_attachment_progress": 67.5,
                "errors": [],
            }
        },
    }


class MultipartUploadResponse(BaseModel):
    """Response from initiating a multipart upload"""

    upload_id: Annotated[
        str, Field(..., description="Unique identifier for the multipart upload")
    ]
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional metadata from the storage provider"
    )

    @field_validator("upload_id")
    @classmethod
    def validate_upload_id(cls, v):
        """Validate upload ID is not empty or whitespace."""
        if not isinstance(v, str):
            raise ValueError("Upload ID must be a string")
        if not v or not v.strip():
            raise ValueError("Upload ID cannot be empty or whitespace")
        return v.strip()

    class Config:
        """Pydantic model configuration"""

        # Allow extra fields from storage providers
        extra = "allow"
        # Use case-insensitive field names
        case_sensitive = False

    def is_valid_upload_id(self) -> bool:
        """Check if the upload ID is valid (not empty and properly formatted)"""
        return bool(self.upload_id and self.upload_id.strip())

    def get_provider_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value by key with fallback to default"""
        if self.metadata:
            return self.metadata.get(key, default)
        return default


class UploadPartResponse(BaseModel):
    """Response from uploading a part"""

    etag: Annotated[str, Field(..., description="ETag/checksum of the uploaded part")]
    part_number: Annotated[
        int, Field(..., description="Sequential number of the part (1-10,000)")
    ]
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional metadata from the storage provider"
    )

    @field_validator("part_number")
    @classmethod
    def validate_part_number(cls, v):
        """Validate part number is within AWS S3 limits (1-10,000)."""
        if not isinstance(v, int):
            raise ValueError("Part number must be an integer")
        if v < 1 or v > 10000:
            raise ValueError("Part number must be between 1 and 10,000")
        return v

    class Config:
        """Pydantic model configuration"""

        # Allow extra fields from storage providers
        extra = "allow"
        # Use case-insensitive field names
        case_sensitive = False

    def is_valid_etag(self) -> bool:
        """Check if the ETag is valid (not empty and properly formatted)"""
        return bool(self.etag and self.etag.strip())

    def get_provider_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value by key with fallback to default"""
        if self.metadata:
            return self.metadata.get(key, default)
        return default
