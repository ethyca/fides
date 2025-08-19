from pydantic import BaseModel, Field, model_validator, computed_field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone



class ProcessingMetrics(BaseModel):
    """Metrics for tracking processing progress and performance."""

    total_attachments: int = Field(
        default=0,
        ge=0,
        description="Total number of attachments to process"
    )
    processed_attachments: int = Field(
        default=0,
        ge=0,
        description="Number of attachments processed so far"
    )
    total_bytes: int = Field(
        default=0,
        ge=0,
        description="Total bytes to process"
    )
    processed_bytes: int = Field(
        default=0,
        ge=0,
        description="Bytes processed so far"
    )
    start_time: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When processing started"
    )
    current_attachment: Optional[str] = Field(
        None,
        description="Currently processing attachment filename"
    )
    current_attachment_progress: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Current attachment progress percentage"
    )
    errors: List[str] = Field(
        default_factory=list,
        description="List of error messages encountered"
    )

    @model_validator(mode='after')
    def validate_processed_values(self):
        """Validate that processed values don't exceed total values."""
        if self.processed_attachments > self.total_attachments:
            raise ValueError('processed_attachments cannot exceed total_attachments')

        if self.processed_bytes > self.total_bytes:
            raise ValueError('processed_bytes cannot exceed total_bytes')

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
                "errors": []
            }
        }
    }


class MultipartUploadResponse(BaseModel):
    """Response from initiating a multipart upload"""
    upload_id: str = Field(..., description="Unique identifier for the multipart upload")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata from the storage provider"
    )

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
    etag: str = Field(..., description="ETag/checksum of the uploaded part")
    part_number: int = Field(..., ge=1, description="Sequential number of the part (must be >= 1)")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata from the storage provider"
    )

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
