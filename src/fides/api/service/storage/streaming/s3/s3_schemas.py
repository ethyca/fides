from __future__ import annotations

from typing import Annotated, Any, Optional

from pydantic import BaseModel, Field, field_validator

from fides.api.service.storage.streaming.schemas import UploadPartResponse
from fides.api.service.storage.streaming.util import AWS_MIN_PART_SIZE


class AWSUploadPartRequest(BaseModel):
    """Request parameters for uploading a part to a multipart upload"""

    bucket: Annotated[
        str,
        Field(
            ..., description="S3 bucket name where the multipart upload was initiated"
        ),
    ]
    key: Annotated[
        str,
        Field(..., description="S3 object key (file path) for the multipart upload"),
    ]
    upload_id: Annotated[
        str, Field(..., description="Upload ID returned from create_multipart_upload")
    ]
    part_number: Annotated[
        int, Field(..., description="Sequential part number (1-10,000)")
    ]
    body: Annotated[bytes, Field(..., description="Binary data content for this part")]
    metadata: Optional[dict[str, str]] = Field(
        default=None, description="Optional metadata for this specific part"
    )

    @field_validator("upload_id")
    @classmethod
    def validate_upload_id(cls, v: Any) -> str:
        """Validate upload ID format (not empty or whitespace), but allow invalid IDs to pass through to S3."""
        if not isinstance(v, str):
            raise ValueError("Upload ID must be a string")
        if not v or not v.strip():
            raise ValueError("Upload ID cannot be empty or whitespace")
        return v.strip()

    @field_validator("part_number")
    @classmethod
    def validate_part_number(cls, v: Any) -> int:
        """Validate part number is within AWS S3 limits (1-10,000)."""
        if not isinstance(v, int):
            raise ValueError("Part number must be an integer")
        if v < 1 or v > 10000:
            raise ValueError("Part number must be between 1 and 10,000")
        return v

    @field_validator("bucket")
    @classmethod
    def validate_bucket(cls, v: Any) -> str:
        """Validate bucket name is not empty or whitespace."""
        if not isinstance(v, str):
            raise ValueError("Bucket must be a string")
        if not v or not v.strip():
            raise ValueError("Bucket cannot be empty or whitespace")
        return v.strip()

    @field_validator("key")
    @classmethod
    def validate_key(cls, v: Any) -> str:
        """Validate object key is not empty or whitespace."""
        if not isinstance(v, str):
            raise ValueError("Key must be a string")
        if not v or not v.strip():
            raise ValueError("Key cannot be empty or whitespace")
        return v.strip()

    @field_validator("body")
    @classmethod
    def validate_body_size(cls, v: Any, info: Any) -> bytes:
        """Validate that the body is not empty and meets the minimum part size."""
        if not v:
            raise ValueError("Body cannot be empty")
        if len(v) < AWS_MIN_PART_SIZE:
            raise ValueError(f"Body must be at least {AWS_MIN_PART_SIZE} bytes")
        return v

    class Config:
        """Pydantic model configuration"""

        extra = "forbid"  # Don't allow extra fields
        case_sensitive = False


class AWSCreateMultipartUploadRequest(BaseModel):
    """Request parameters for creating a multipart upload"""

    bucket: Annotated[
        str, Field(..., description="S3 bucket name where the file will be stored")
    ]
    key: Annotated[
        str, Field(..., description="S3 object key (file path) within the bucket")
    ]
    content_type: Annotated[
        str, Field(..., description="MIME type of the file being uploaded")
    ]
    metadata: Optional[dict[str, str]] = Field(
        default=None, description="Optional key-value pairs to store as object metadata"
    )

    @field_validator("bucket")
    @classmethod
    def validate_bucket(cls, v: Any) -> str:
        """Validate bucket name is not empty or whitespace."""
        if not isinstance(v, str):
            raise ValueError("Bucket must be a string")
        if not v or not v.strip():
            raise ValueError("Bucket cannot be empty or whitespace")
        return v.strip()

    @field_validator("key")
    @classmethod
    def validate_key(cls, v: Any) -> str:
        """Validate object key is not empty or whitespace."""
        if not isinstance(v, str):
            raise ValueError("Key must be a string")
        if not v or not v.strip():
            raise ValueError("Key cannot be empty or whitespace")
        return v.strip()

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, v: Any) -> str:
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


class AWSAbortMultipartUploadRequest(BaseModel):
    """Request parameters for aborting a multipart upload"""

    bucket: Annotated[
        str,
        Field(
            ..., description="S3 bucket name where the multipart upload was initiated"
        ),
    ]
    key: Annotated[
        str,
        Field(..., description="S3 object key (file path) for the multipart upload"),
    ]
    upload_id: Annotated[
        str, Field(..., description="Upload ID returned from create_multipart_upload")
    ]

    @field_validator("bucket")
    @classmethod
    def validate_bucket(cls, v: Any) -> str:
        """Validate bucket name is not empty or whitespace."""
        if not isinstance(v, str):
            raise ValueError("Bucket must be a string")
        if not v or not v.strip():
            raise ValueError("Bucket cannot be empty or whitespace")
        return v.strip()

    @field_validator("key")
    @classmethod
    def validate_key(cls, v: Any) -> str:
        """Validate object key is not empty or whitespace."""
        if not isinstance(v, str):
            raise ValueError("Key must be a string")
        if not v or not v.strip():
            raise ValueError("Key cannot be empty or whitespace")
        return v.strip()

    @field_validator("upload_id")
    @classmethod
    def validate_upload_id(cls, v: Any) -> str:
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


class AWSGeneratePresignedUrlRequest(BaseModel):
    """Request parameters for generating a presigned URL"""

    bucket: Annotated[
        str, Field(..., description="S3 bucket name containing the object")
    ]
    key: Annotated[
        str, Field(..., description="S3 object key (file path) within the bucket")
    ]
    ttl_seconds: Optional[int] = Field(
        default=None,
        ge=1,
        le=604800,  # 7 days in seconds
        description="Optional TTL in seconds (max 7 days)",
    )

    @field_validator("bucket")
    @classmethod
    def validate_bucket(cls, v: Any) -> str:
        """Validate bucket name is not empty or whitespace."""
        if not isinstance(v, str):
            raise ValueError("Bucket must be a string")
        if not v or not v.strip():
            raise ValueError("Bucket cannot be empty or whitespace")
        return v.strip()

    @field_validator("key")
    @classmethod
    def validate_key(cls, v: Any) -> str:
        """Validate object key is not empty or whitespace."""
        if not isinstance(v, str):
            raise ValueError("Key must be a string")
        if not v or not v.strip():
            raise ValueError("Key cannot be empty or whitespace")
        return v.strip()

    class Config:
        """Pydantic model configuration"""

        extra = "forbid"
        case_sensitive = False


class AWSCompleteMultipartUploadRequest(BaseModel):
    """Request parameters for completing a multipart upload"""

    bucket: Annotated[
        str,
        Field(
            ..., description="S3 bucket name where the multipart upload was initiated"
        ),
    ]
    key: Annotated[
        str,
        Field(..., description="S3 object key (file path) for the multipart upload"),
    ]
    upload_id: Annotated[
        str, Field(..., description="Upload ID returned from create_multipart_upload")
    ]
    parts: Annotated[
        list[UploadPartResponse],
        Field(..., min_length=1, description="List of uploaded parts"),
    ]
    metadata: Optional[dict[str, str]] = Field(
        default=None, description="Optional metadata for the completed object"
    )

    @field_validator("bucket")
    @classmethod
    def validate_bucket(cls, v: Any) -> str:
        """Validate bucket name is not empty or whitespace."""
        if not isinstance(v, str):
            raise ValueError("Bucket must be a string")
        if not v or not v.strip():
            raise ValueError("Bucket cannot be empty or whitespace")
        return v.strip()

    @field_validator("key")
    @classmethod
    def validate_key(cls, v: Any) -> str:
        """Validate object key is not empty or whitespace."""
        if not isinstance(v, str):
            raise ValueError("Key must be a string")
        if not v or not v.strip():
            raise ValueError("Key cannot be empty or whitespace")
        return v.strip()

    @field_validator("upload_id")
    @classmethod
    def validate_upload_id(cls, v: Any) -> str:
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
