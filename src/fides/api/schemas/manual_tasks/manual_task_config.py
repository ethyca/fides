from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional, Union

from pydantic import ConfigDict, Field, ValidationInfo, field_validator

from fides.api.schemas.base_class import FidesSchema

if TYPE_CHECKING:
    from fides.api.models.manual_tasks.manual_task import ManualTask


class ManualTaskConfigurationType(str, Enum):
    """Enum for manual task configuration types."""

    access_privacy_request = "access_privacy_request"
    erasure_privacy_request = "erasure_privacy_request"
    # Add more configuration types as needed


class ManualTaskFieldType(str, Enum):
    """Enum for manual task field types."""

    text = "text"  # Key-value pairs
    checkbox = "checkbox"  # Boolean value
    attachment = "attachment"  # File upload
    # Add more field types as needed


class ManualTaskFieldMetadata(FidesSchema):
    """Base schema for manual task field metadata."""

    model_config = ConfigDict(extra="allow")

    label: str = Field(..., description="Display label for the field")
    required: bool = Field(default=False, description="Whether the field is required")
    help_text: Optional[str] = Field(
        None, description="Help text to display with the field"
    )


class ManualTaskTextFieldMetadata(ManualTaskFieldMetadata):
    """Schema text field metadata."""

    placeholder: Optional[str] = Field(
        None, description="Placeholder text for the field"
    )
    default_value: Optional[str] = Field(
        None, description="Default value for the field"
    )
    max_length: Optional[int] = Field(
        None, description="Maximum length for text fields"
    )
    min_length: Optional[int] = Field(
        None, description="Minimum length for text fields"
    )
    pattern: Optional[str] = Field(
        None,
        description=(
            "Regex pattern for validation, for example if the field is an email address, "
            "you could use: ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        ),
    )

    @field_validator("min_length", "max_length")
    @classmethod
    def validate_lengths(cls, v: Optional[int], info: ValidationInfo) -> Optional[int]:
        """Validate that min_length is not greater than max_length."""
        if v is None:
            return v

        if info.field_name == "min_length":
            max_length = info.data.get("max_length")
            if max_length is not None and v > max_length:
                raise ValueError("min_length cannot be greater than max_length")
        elif info.field_name == "max_length":
            min_length = info.data.get("min_length")
            if min_length is not None and v < min_length:
                raise ValueError("max_length cannot be less than min_length")

        return v


class ManualTaskCheckboxFieldMetadata(ManualTaskFieldMetadata):
    """Schema for checkbox field metadata."""

    default_value: Optional[bool] = Field(
        False, description="Default value for the checkbox"
    )
    label_true: Optional[str] = Field(None, description="Label for checked state")
    label_false: Optional[str] = Field(None, description="Label for unchecked state")

    @field_validator("default_value")
    @classmethod
    def validate_default_value(cls, v: Optional[bool]) -> Optional[bool]:
        """Validate that default_value is a boolean."""
        if v is not None and not isinstance(v, bool):
            raise ValueError("default_value must be a boolean")
        return v


class ManualTaskAttachmentFieldMetadata(ManualTaskFieldMetadata):
    """Schema for attachment field metadata."""

    file_types: list[str] = Field(
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
    attachment_ids: Optional[list[str]] = Field(
        None, description="List of attachment IDs associated with this field"
    )

    @field_validator("file_types")
    @classmethod
    def validate_file_types(cls, v: list[str]) -> list[str]:
        """Validate that file_types is a list of strings."""
        if not isinstance(v, list):
            raise ValueError("file_types must be a list")
        if not all(isinstance(t, str) for t in v):
            raise ValueError("file_types must be a list of strings")
        return v

    @field_validator("max_files")
    @classmethod
    def validate_max_files(
        cls, v: Optional[int], info: ValidationInfo
    ) -> Optional[int]:
        """Validate that max_files is set when multiple is True."""
        if info.data.get("multiple") and v is None:
            raise ValueError("max_files must be set when multiple is True")
        return v


class ManualTaskTextField(FidesSchema):
    """Schema for text field definition."""

    model_config = ConfigDict(extra="allow")

    field_key: str = Field(..., description="Unique key for the field")
    field_type: ManualTaskFieldType = Field(
        ManualTaskFieldType.text, description="Type of the field"
    )
    field_metadata: ManualTaskTextFieldMetadata = Field(
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
    ManualTaskTextField, ManualTaskCheckboxField, ManualTaskAttachmentField
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
    fields: list[ManualTaskField] = Field(..., description="List of field definitions")


class ManualTaskConfigResponse(FidesSchema):
    """Schema for manual task configuration response."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Configuration ID")
    task_id: str = Field(..., description="Task ID")
    config_type: ManualTaskConfigurationType = Field(
        ..., description="Type of configuration"
    )
    version: int = Field(..., description="Version of the configuration")
    is_current: bool = Field(..., description="Whether this is the current version")
    fields: list[ManualTaskField] = Field(..., description="List of field definitions")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class ManualTaskConfigUpdate(FidesSchema):
    """Schema for updating a manual task configuration."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    task_id: str = Field(..., description="ID of the task")
    config_type: ManualTaskConfigurationType = Field(
        ..., description="Type of configuration"
    )
    fields: list[ManualTaskField] = Field(..., description="List of field definitions")


class ManualTaskConfigFieldResponse(FidesSchema):
    """Schema for manual task configuration field response."""

    model_config = ConfigDict(extra="forbid")

    field_key: str = Field(..., description="Unique key for the field")
    field_type: ManualTaskFieldType = Field(..., description="Type of the field")
    field_metadata: ManualTaskFieldMetadata = Field(
        ..., description="Field metadata and configuration"
    )
