from __future__ import annotations

from typing import Annotated, Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from fides.api.service.storage.streaming.util import GCS_MIN_CHUNK_SIZE


class GCSResumableUploadRequest(BaseModel):
    """Request parameters for creating a GCS resumable upload session"""

    bucket: Annotated[
        str, Field(..., description="GCS bucket name where the file will be stored")
    ]
    key: Annotated[
        str, Field(..., description="GCS object key (file path) within the bucket")
    ]
    content_type: Annotated[
        str, Field(..., description="MIME type of the file being uploaded")
    ]
    metadata: Optional[Dict[str, str]] = Field(
        default=None, description="Optional key-value pairs to store as object metadata"
    )

    @field_validator("bucket")
    @classmethod
    def validate_bucket(cls, v):
        """Validate GCS bucket name format and requirements."""
        if not isinstance(v, str):
            raise ValueError("Bucket must be a string")
        if not v or not v.strip():
            raise ValueError("Bucket cannot be empty or whitespace")

        # GCS bucket naming requirements
        bucket = v.strip()
        if len(bucket) < 3 or len(bucket) > 63:
            raise ValueError("GCS bucket name must be between 3 and 63 characters")
        if not bucket[0].isalnum():
            raise ValueError("GCS bucket name must start with a letter or number")
        if not bucket[-1].isalnum():
            raise ValueError("GCS bucket name must end with a letter or number")
        if not all(c.isalnum() or c in "-_" for c in bucket):
            raise ValueError(
                "GCS bucket name can only contain letters, numbers, hyphens, and underscores"
            )

        return bucket

    @field_validator("key")
    @classmethod
    def validate_key(cls, v):
        """Validate GCS object key format and requirements."""
        if not isinstance(v, str):
            raise ValueError("Key must be a string")
        if not v or not v.strip():
            raise ValueError("Key cannot be empty or whitespace")

        # GCS object key requirements
        key = v.strip()
        if len(key) > 1024:
            raise ValueError("GCS object key cannot exceed 1024 characters")
        if key.startswith("/"):
            raise ValueError("GCS object key cannot start with '/'")

        return key

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, v):
        """Validate content type is not empty or whitespace."""
        if not isinstance(v, str):
            raise ValueError("Content type must be a string")
        if not v or not v.strip():
            raise ValueError("Content type cannot be empty or whitespace")
        return v.strip()

    class Config:
        """Pydantic model configuration"""

        extra = "forbid"
        case_sensitive = False


class GCSResumableUploadResponse(BaseModel):
    """Response from initiating a GCS resumable upload session"""

    upload_id: Annotated[
        str,
        Field(..., description="Unique identifier for the resumable upload session"),
    ]
    resumable_url: Annotated[
        str, Field(..., description="Resumable upload URL for continuing the upload")
    ]
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional metadata from GCS"
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

    @field_validator("resumable_url")
    @classmethod
    def validate_resumable_url(cls, v):
        """Validate resumable URL is a valid HTTPS URL."""
        if not isinstance(v, str):
            raise ValueError("Resumable URL must be a string")
        if not v or not v.strip():
            raise ValueError("Resumable URL cannot be empty or whitespace")

        url = v.strip()
        if not url.startswith("https://"):
            raise ValueError("Resumable URL must be an HTTPS URL")

        return url

    class Config:
        """Pydantic model configuration"""

        extra = "allow"
        case_sensitive = False


class GCSChunkUploadRequest(BaseModel):
    """Request parameters for uploading a chunk to a GCS resumable upload"""

    bucket: Annotated[
        str,
        Field(
            ..., description="GCS bucket name where the resumable upload was initiated"
        ),
    ]
    key: Annotated[
        str,
        Field(..., description="GCS object key (file path) for the resumable upload"),
    ]
    upload_id: Annotated[
        str, Field(..., description="Upload ID returned from create_resumable_upload")
    ]
    chunk_data: Annotated[
        bytes, Field(..., description="Binary data content for this chunk")
    ]
    metadata: Optional[Dict[str, str]] = Field(
        default=None, description="Optional metadata for this specific chunk"
    )

    @field_validator("upload_id")
    @classmethod
    def validate_upload_id(cls, v):
        """Validate upload ID format."""
        if not isinstance(v, str):
            raise ValueError("Upload ID must be a string")
        if not v or not v.strip():
            raise ValueError("Upload ID cannot be empty or whitespace")
        return v.strip()

    @field_validator("chunk_data")
    @classmethod
    def validate_chunk_data(cls, v):
        """Validate that the chunk data meets GCS requirements."""
        if not v:
            raise ValueError("Chunk data cannot be empty")
        if len(v) < GCS_MIN_CHUNK_SIZE:
            raise ValueError(
                f"Chunk data must be at least {GCS_MIN_CHUNK_SIZE // 1024}KB"
            )
        return v

    @field_validator("bucket")
    @classmethod
    def validate_bucket(cls, v):
        """Validate GCS bucket name."""
        if not isinstance(v, str):
            raise ValueError("Bucket must be a string")
        if not v or not v.strip():
            raise ValueError("Bucket cannot be empty or whitespace")
        return v.strip()

    @field_validator("key")
    @classmethod
    def validate_key(cls, v):
        """Validate GCS object key."""
        if not isinstance(v, str):
            raise ValueError("Key must be a string")
        if not v or not v.strip():
            raise ValueError("Key cannot be empty or whitespace")
        return v.strip()

    class Config:
        """Pydantic model configuration"""

        extra = "forbid"
        case_sensitive = False


class GCSChunkUploadResponse(BaseModel):
    """Response from uploading a chunk to a GCS resumable upload"""

    bytes_uploaded: Annotated[
        int, Field(..., description="Total bytes uploaded so far in this session")
    ]
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional metadata from GCS"
    )

    @field_validator("bytes_uploaded")
    @classmethod
    def validate_bytes_uploaded(cls, v):
        """Validate bytes uploaded is non-negative."""
        if not isinstance(v, int):
            raise ValueError("Bytes uploaded must be an integer")
        if v < 0:
            raise ValueError("Bytes uploaded cannot be negative")
        return v

    class Config:
        """Pydantic model configuration"""

        extra = "allow"
        case_sensitive = False


class GCSCompleteResumableUploadRequest(BaseModel):
    """Request parameters for completing a GCS resumable upload"""

    bucket: Annotated[
        str,
        Field(
            ..., description="GCS bucket name where the resumable upload was initiated"
        ),
    ]
    key: Annotated[
        str,
        Field(..., description="GCS object key (file path) for the resumable upload"),
    ]
    upload_id: Annotated[
        str, Field(..., description="Upload ID returned from create_resumable_upload")
    ]
    metadata: Optional[Dict[str, str]] = Field(
        default=None, description="Optional metadata for the completed object"
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

    @field_validator("bucket")
    @classmethod
    def validate_bucket(cls, v):
        """Validate GCS bucket name."""
        if not isinstance(v, str):
            raise ValueError("Bucket must be a string")
        if not v or not v.strip():
            raise ValueError("Bucket cannot be empty or whitespace")
        return v.strip()

    @field_validator("key")
    @classmethod
    def validate_key(cls, v):
        """Validate GCS object key."""
        if not isinstance(v, str):
            raise ValueError("Key must be a string")
        if not v or not v.strip():
            raise ValueError("Key cannot be empty or whitespace")
        return v.strip()

    class Config:
        """Pydantic model configuration"""

        extra = "forbid"
        case_sensitive = False


class GCSAbortResumableUploadRequest(BaseModel):
    """Request parameters for aborting a GCS resumable upload"""

    bucket: Annotated[
        str,
        Field(
            ..., description="GCS bucket name where the resumable upload was initiated"
        ),
    ]
    key: Annotated[
        str,
        Field(..., description="GCS object key (file path) for the resumable upload"),
    ]
    upload_id: Annotated[
        str, Field(..., description="Upload ID returned from create_resumable_upload")
    ]

    @field_validator("bucket")
    @classmethod
    def validate_bucket(cls, v):
        """Validate GCS bucket name."""
        if not isinstance(v, str):
            raise ValueError("Bucket must be a string")
        if not v or not v.strip():
            raise ValueError("Bucket cannot be empty or whitespace")
        return v.strip()

    @field_validator("key")
    @classmethod
    def validate_key(cls, v):
        """Validate GCS object key."""
        if not isinstance(v, str):
            raise ValueError("Key must be a string")
        if not v or not v.strip():
            raise ValueError("Key cannot be empty or whitespace")
        return v.strip()

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

        extra = "forbid"
        case_sensitive = False


class GCSGetObjectRequest(BaseModel):
    """Request parameters for getting GCS object metadata or content"""

    bucket: Annotated[
        str, Field(..., description="GCS bucket name containing the object")
    ]
    key: Annotated[
        str, Field(..., description="GCS object key (file path) within the bucket")
    ]

    @field_validator("bucket")
    @classmethod
    def validate_bucket(cls, v):
        """Validate GCS bucket name."""
        if not isinstance(v, str):
            raise ValueError("Bucket must be a string")
        if not v or not v.strip():
            raise ValueError("Bucket cannot be empty or whitespace")
        return v.strip()

    @field_validator("key")
    @classmethod
    def validate_key(cls, v):
        """Validate GCS object key."""
        if not isinstance(v, str):
            raise ValueError("Key must be a string")
        if not v or not v.strip():
            raise ValueError("Key cannot be empty or whitespace")
        return v.strip()

    class Config:
        """Pydantic model configuration"""

        extra = "forbid"
        case_sensitive = False


class GCSGetObjectRangeRequest(GCSGetObjectRequest):
    """Request parameters for getting a specific byte range from a GCS object"""

    start_byte: Annotated[
        int, Field(..., ge=0, description="Starting byte position (inclusive, 0-based)")
    ]
    end_byte: Annotated[
        int, Field(..., ge=0, description="Ending byte position (inclusive, 0-based)")
    ]

    @field_validator("end_byte")
    @classmethod
    def validate_end_byte(cls, v, info):
        """Validate that end_byte is greater than or equal to start_byte."""
        if "start_byte" in info.data and v < info.data["start_byte"]:
            raise ValueError("end_byte must be greater than or equal to start_byte")
        return v

    class Config:
        """Pydantic model configuration"""

        extra = "forbid"
        case_sensitive = False


class GCSGenerateSignedUrlRequest(GCSGetObjectRequest):
    """Request parameters for generating a GCS signed URL"""

    ttl_seconds: Optional[int] = Field(
        default=None,
        ge=1,
        le=604800,  # 7 days in seconds
        description="Optional TTL in seconds (max 7 days)",
    )

    class Config:
        """Pydantic model configuration"""

        extra = "forbid"
        case_sensitive = False
