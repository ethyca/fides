from typing import Annotated, Any, Optional

from pydantic import BaseModel, Field, field_validator

# Storage size constants
S3_MIN_PART_SIZE = 5 * 1024 * 1024  # 5MB minimum part size for AWS S3 multipart uploads
ZIP_BUFFER_THRESHOLD = 5 * 1024 * 1024  # 5MB threshold for zip buffer uploads
DEFAULT_CHUNK_SIZE = 5 * 1024 * 1024  # 5MB default chunk size for streaming operations
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB threshold for large file handling

# Backward compatibility aliases
MIN_PART_SIZE = S3_MIN_PART_SIZE
CHUNK_SIZE_THRESHOLD = DEFAULT_CHUNK_SIZE


class AttachmentInfo(BaseModel):
    """Schema for attachment information in streaming storage"""

    storage_key: str = Field(
        ..., description="Storage key for the attachment (cloud-agnostic)"
    )
    file_name: Optional[str] = Field(None, description="Human-readable filename")
    size: Optional[int] = Field(None, ge=0, description="File size in bytes")
    content_type: Optional[str] = Field(None, description="MIME type of the file")

    @field_validator("storage_key")
    @classmethod
    def validate_storage_key(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("storage_key cannot be empty or whitespace")
        return v.strip()

    @field_validator("file_name")
    @classmethod
    def validate_file_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and (not v or not v.strip()):
            raise ValueError("file_name cannot be empty or whitespace if provided")
        return v.strip() if v else None


class StorageUploadConfig(BaseModel):
    """Configuration for storage upload operations"""

    bucket_name: str = Field(..., description="Storage bucket name")
    file_key: str = Field(..., description="File key in storage")
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


class StreamingBufferConfig(BaseModel):
    """Configuration for streaming buffer operations"""

    zip_buffer_threshold: int = Field(
        default=5 * 1024 * 1024,
        ge=1024 * 1024,
        description="Zip buffer threshold in bytes (default: 5MB)",
    )
    stream_buffer_threshold: int = Field(
        default=1024 * 1024,
        ge=1024 * 1024,
        description="Stream buffer threshold in bytes (default: 1MB)",
    )
    chunk_size_threshold: int = Field(
        default=1024 * 1024,
        ge=1024 * 1024,
        description="Chunk size threshold in bytes (default: 1MB)",
    )
    fail_fast_on_attachment_errors: bool = Field(
        default=True,
        description="If True, stop processing on first attachment error. If False, continue with error placeholders.",
    )
    include_error_details: bool = Field(
        default=True,
        description="If True, include detailed error information in the output ZIP.",
    )


class SmartOpenStreamingStorageConfig(BaseModel):
    """Configuration for SmartOpenStreamingStorage initialization"""

    chunk_size: int = Field(
        default=DEFAULT_CHUNK_SIZE,
        ge=1024,  # 1KB minimum
        le=MAX_FILE_SIZE,  # 2GB maximum
        description="Size of chunks for streaming attachments (default: 5MB)",
    )


class AttachmentProcessingInfo(BaseModel):
    """Information for processing a single attachment"""

    attachment: AttachmentInfo = Field(..., description="Attachment to process")
    base_path: str = Field(..., description="Base path for the attachment in the zip")
    item: dict[str, Any] = Field(..., description="Associated item data")

    @field_validator("base_path")
    @classmethod
    def validate_base_path(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("base_path cannot be empty or whitespace")
        return v.strip()


class MultipartUploadResponse(BaseModel):
    """Response from initiating a multipart upload"""

    upload_id: Annotated[
        str, Field(..., description="Unique identifier for the multipart upload")
    ]
    metadata: Optional[dict[str, Any]] = Field(
        default=None, description="Additional metadata from the storage provider"
    )

    model_config = {
        "extra": "allow",  # Allow extra fields from storage providers
    }

    @field_validator("upload_id")
    @classmethod
    def validate_upload_id(cls, v: Any) -> str:
        """Validate upload ID is not empty or whitespace."""
        if not isinstance(v, str):
            raise ValueError("Upload ID must be a string")
        if not v or not v.strip():
            raise ValueError("Upload ID cannot be empty or whitespace")
        return v.strip()

    def is_valid_upload_id(self) -> bool:
        """Check if the upload ID is valid (not empty or whitespace)"""
        return bool(self.upload_id and self.upload_id.strip())

    def get_provider_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value by key with fallback to default"""
        if self.metadata is not None:
            return self.metadata.get(key, default)  # pylint: disable=no-member
        return default


class UploadPartResponse(BaseModel):
    """Response from uploading a part"""

    etag: Annotated[str, Field(..., description="ETag/checksum of the uploaded part")]
    part_number: Annotated[
        int, Field(..., description="Sequential number of the part (1-10,000)")
    ]
    metadata: Optional[dict[str, Any]] = Field(
        default=None, description="Additional metadata from the storage provider"
    )

    model_config = {
        "extra": "allow",  # Allow extra fields from storage providers
    }

    @field_validator("part_number")
    @classmethod
    def validate_part_number(cls, v: Any) -> int:
        """Validate part number is within AWS S3 limits (1-10,000)."""
        if not isinstance(v, int):
            raise ValueError("Part number must be an integer")
        if v < 1 or v > 10000:
            raise ValueError("Part number must be between 1 and 10,000")
        return v

    def is_valid_etag(self) -> bool:
        """Check if the ETag is valid (not empty and properly formatted)"""
        return bool(self.etag and self.etag.strip())

    def get_provider_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value by key with fallback to default"""
        if self.metadata is not None:
            return self.metadata.get(key, default)  # pylint: disable=no-member
        return default
