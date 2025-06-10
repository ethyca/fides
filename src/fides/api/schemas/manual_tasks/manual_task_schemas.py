from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import ConfigDict, Field

from fides.api.schemas.base_class import FidesSchema


class ManualTaskType(str, Enum):
    """Enum for manual task types."""

    privacy_request = "privacy_request"
    # Add more task types as needed


class ManualTaskParentEntityType(str, Enum):
    """Enum for manual task parent entity types."""

    CONNECTION_CONFIG = (
        "connection_config"  # used for access and erasure privacy requests
    )
    # Add more parent entity types as needed


class ManualTaskReferenceType(str, Enum):
    """Enum for manual task reference types."""

    privacy_request = "privacy_request"
    connection_config = "connection_config"
    manual_task_config = "manual_task_config"
    assigned_user = "assigned_user"  # Reference to the user assigned to the task
    # Add more reference types as needed


class ManualTaskConfigurationType(str, Enum):
    """Enum for manual task configuration types."""

    access_privacy_request = "access_privacy_request"
    erasure_privacy_request = "erasure_privacy_request"
    # Add more configuration types as needed


class ManualTaskLogStatus(str, Enum):
    """Enum for manual task log status."""

    in_processing = "in_processing"
    complete = "complete"
    error = "error"
    retrying = "retrying"
    paused = "paused"
    awaiting_input = "awaiting_input"


class ManualTaskFieldType(str, Enum):
    """Enum for manual task field types."""

    form = "form"  # Key-value pairs
    checkbox = "checkbox"  # Boolean value
    attachment = "attachment"  # File upload


class ManualTaskFieldMetadata(FidesSchema):
    """Base schema for manual task field metadata."""

    model_config = ConfigDict(extra="allow")

    label: str = Field(..., description="Display label for the field")
    required: bool = Field(default=False, description="Whether the field is required")
    help_text: Optional[str] = Field(
        None, description="Help text to display with the field"
    )


class ManualTaskFormFieldMetadata(ManualTaskFieldMetadata):
    """Schema for form field metadata."""

    placeholder: Optional[str] = Field(
        None, description="Placeholder text for the field"
    )
    default_value: Optional[str] = Field(
        None, description="Default value for the field"
    )
    validation_rules: Optional[Dict[str, Any]] = Field(
        None, description="Validation rules for the field"
    )
    max_length: Optional[int] = Field(
        None, description="Maximum length for text fields"
    )
    min_length: Optional[int] = Field(
        None, description="Minimum length for text fields"
    )
    pattern: Optional[str] = Field(None, description="Regex pattern for validation")


class ManualTaskCheckboxFieldMetadata(ManualTaskFieldMetadata):
    """Schema for checkbox field metadata."""

    default_value: Optional[bool] = Field(
        False, description="Default value for the checkbox"
    )
    label_true: Optional[str] = Field(None, description="Label for checked state")
    label_false: Optional[str] = Field(None, description="Label for unchecked state")


class ManualTaskAttachmentFieldMetadata(ManualTaskFieldMetadata):
    """Schema for attachment field metadata."""

    file_types: List[str] = Field(
        ..., description="Allowed file types for upload fields"
    )
    max_file_size: int = Field(
        ..., description="Maximum file size in bytes for upload fields"
    )
    multiple: bool = Field(
        default=False, description="Whether multiple files can be uploaded"
    )
    max_files: Optional[int] = Field(
        None, description="Maximum number of files allowed when multiple is true"
    )
    require_attachment_id: bool = Field(
        default=True, description="Whether an attachment ID is required for this field"
    )
    attachment_ids: Optional[List[str]] = Field(
        None, description="List of attachment IDs associated with this field"
    )


class ManualTaskFormField(FidesSchema):
    """Schema for form field definition."""

    model_config = ConfigDict(extra="allow")

    field_key: str = Field(..., description="Unique key for the field")
    field_type: ManualTaskFieldType = Field(
        ManualTaskFieldType.form, description="Type of the field"
    )
    field_metadata: ManualTaskFormFieldMetadata = Field(
        ..., description="Field metadata and configuration"
    )


class ManualTaskCheckboxField(FidesSchema):
    """Schema for checkbox field definition."""

    model_config = ConfigDict(extra="allow")

    field_key: str = Field(..., description="Unique key for the field")
    field_type: ManualTaskFieldType = Field(
        ManualTaskFieldType.checkbox, description="Type of the field"
    )
    field_metadata: ManualTaskCheckboxFieldMetadata = Field(
        ..., description="Field metadata and configuration"
    )


class ManualTaskAttachmentField(FidesSchema):
    """Schema for attachment field definition."""

    model_config = ConfigDict(extra="allow")

    field_key: str = Field(..., description="Unique key for the field")
    field_type: ManualTaskFieldType = Field(
        ManualTaskFieldType.attachment, description="Type of the field"
    )
    field_metadata: ManualTaskAttachmentFieldMetadata = Field(
        ..., description="Field metadata and configuration"
    )


# Union type for all field types
ManualTaskField = Union[
    ManualTaskFormField, ManualTaskCheckboxField, ManualTaskAttachmentField
]


class ManualTaskConfigCreate(FidesSchema):
    """Schema for creating a manual task configuration."""

    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(
        ..., description="ID of the task this configuration belongs to"
    )
    config_type: ManualTaskConfigurationType = Field(
        ..., description="Type of configuration"
    )
    fields: List[ManualTaskField] = Field(..., description="List of field definitions")


class ManualTaskConfigResponse(FidesSchema):
    """Schema for manual task configuration response."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Configuration ID")
    task_id: str = Field(..., description="Task ID")
    config_type: ManualTaskConfigurationType = Field(
        ..., description="Type of configuration"
    )
    fields: List[ManualTaskField] = Field(..., description="List of field definitions")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class ManualTaskSubmissionCreate(FidesSchema):
    """Schema for creating a manual task submission."""

    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(..., description="ID of the task")
    config_id: str = Field(..., description="ID of the configuration")
    field_id: str = Field(..., description="ID of the field")
    instance_id: Optional[str] = Field(None, description="ID of the instance")
    data: Dict[str, Any] = Field(..., description="Submission data")
    submitted_by: int = Field(..., description="ID of the user submitting")


class ManualTaskSubmissionResponse(FidesSchema):
    """Schema for manual task submission response."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Submission ID")
    task_id: str = Field(..., description="Task ID")
    config_id: str = Field(..., description="Configuration ID")
    field_id: str = Field(..., description="Field ID")
    instance_id: Optional[str] = Field(None, description="Instance ID")
    submitted_by: int = Field(..., description="ID of the user who submitted")
    submitted_at: datetime = Field(..., description="Submission timestamp")
    data: Dict[str, Any] = Field(..., description="Submission data")
    status: str = Field(..., description="Submission status")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    completed_by_id: Optional[str] = Field(
        None, description="ID of the user who completed"
    )


class ManualTaskLogCreate(FidesSchema):
    """Schema for creating a manual task log entry."""

    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(..., description="ID of the task")
    status: ManualTaskLogStatus = Field(..., description="Log status")
    message: Optional[str] = Field(None, description="Log message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")
    config_id: Optional[str] = Field(None, description="Configuration ID")
    instance_id: Optional[str] = Field(None, description="Instance ID")


class ManualTaskLogResponse(FidesSchema):
    """Schema for manual task log response."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Log ID")
    task_id: str = Field(..., description="Task ID")
    status: ManualTaskLogStatus = Field(..., description="Log status")
    message: Optional[str] = Field(None, description="Log message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")
    config_id: Optional[str] = Field(None, description="Configuration ID")
    instance_id: Optional[str] = Field(None, description="Instance ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
