from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Annotated, Literal, Optional, Union

from pydantic import ConfigDict, Field, ValidationInfo, field_validator, model_validator

from fides.api.schemas.base_class import FidesSchema

if TYPE_CHECKING:  # pragma: no cover
    from fides.api.models.manual_tasks.manual_task import ManualTask  # pragma: no cover


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

    label: Annotated[str, Field(description="Display label for the field")]
    required: Annotated[
        bool, Field(default=False, description="Whether the field is required")
    ]
    help_text: Annotated[
        Optional[str],
        Field(default=None, description="Help text to display with the field"),
    ]
    data_uses: Annotated[
        Optional[list[str]],
        Field(
            default=None,
            description="List of data uses associated with this field",
        ),
    ]


class ManualTaskTextFieldMetadata(ManualTaskFieldMetadata):
    """Schema text field metadata."""

    placeholder: Annotated[
        Optional[str], Field(default=None, description="Placeholder text for the field")
    ]
    default_value: Annotated[
        Optional[str], Field(default=None, description="Default value for the field")
    ]
    max_length: Annotated[
        Optional[int], Field(default=None, description="Maximum length for text fields")
    ]
    min_length: Annotated[
        Optional[int], Field(default=None, description="Minimum length for text fields")
    ]
    pattern: Annotated[
        Optional[str],
        Field(
            default=None,
            description=(
                "Regex pattern for validation, for example if the field is an email address, "
                r"you could use: ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            ),
        ),
    ]

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
                raise ValueError("min_length cannot be greater than max_length")

        return v


class ManualTaskCheckboxFieldMetadata(ManualTaskFieldMetadata):
    """Schema for checkbox field metadata."""

    default_value: Annotated[
        Optional[bool],
        Field(default=False, description="Default value for the checkbox"),
    ]
    label_true: Annotated[
        Optional[str], Field(default=None, description="Label for checked state")
    ]
    label_false: Annotated[
        Optional[str], Field(default=None, description="Label for unchecked state")
    ]


class ManualTaskAttachmentFieldMetadata(ManualTaskFieldMetadata):
    """Schema for attachment field metadata."""

    file_types: Annotated[
        list[str], Field(description="Allowed file types for upload fields")
    ]
    max_file_size: Annotated[
        int, Field(description="Maximum file size in bytes for upload fields")
    ]
    multiple: Annotated[
        bool, Field(default=False, description="Whether multiple files can be uploaded")
    ]
    max_files: Annotated[
        Optional[int],
        Field(
            default=None,
            description="Maximum number of files allowed when multiple is true",
        ),
    ]
    require_attachment_id: Annotated[
        bool,
        Field(
            default=True,
            description="Whether an attachment ID is required for this field",
        ),
    ]
    attachment_ids: Annotated[
        Optional[list[str]],
        Field(
            default=None,
            description="List of attachment IDs associated with this field",
        ),
    ]

    @model_validator(mode="after")
    def validate_multiple_max_files(self) -> "ManualTaskAttachmentFieldMetadata":
        """Validate that max_files is set when multiple is True."""
        if self.multiple and self.max_files is None:
            raise ValueError("max_files must be set when multiple is True")
        return self


class ManualTaskFieldBase(FidesSchema):
    """Base schema for all field definitions."""

    model_config = ConfigDict(extra="allow")

    field_key: Annotated[
        str, Field(description="Unique key for the field", min_length=1)
    ]
    field_type: Annotated[ManualTaskFieldType, Field(description="Type of the field")]
    field_metadata: Annotated[
        ManualTaskFieldMetadata, Field(description="Field metadata and configuration")
    ]

    @classmethod
    def get_field_model_for_type(
        cls, field_type: Union[str, ManualTaskFieldType]
    ) -> type["ManualTaskFieldBase"]:
        """Get the appropriate field model class for a given field type.

        Args:
            field_type: The field type as a string or ManualTaskFieldType enum value

        Returns:
            The appropriate field model class

        Raises:
            ValueError: If the field type is not recognized
        """
        # Handle non-string/non-enum types
        if not isinstance(field_type, (str, ManualTaskFieldType)):
            raise ValueError(
                f"Invalid field type: expected string or ManualTaskFieldType, got {type(field_type).__name__}"
            )

        # Convert string to enum if needed
        if isinstance(field_type, str):
            try:
                field_type = ManualTaskFieldType(field_type)
            except ValueError:
                raise ValueError(
                    f"Invalid field type: '{field_type}' is not a valid ManualTaskFieldType"
                )

        # Map field types to their model classes
        field_type_to_model = {
            ManualTaskFieldType.text: ManualTaskTextField,
            ManualTaskFieldType.checkbox: ManualTaskCheckboxField,
            ManualTaskFieldType.attachment: ManualTaskAttachmentField,
        }

        model_class = field_type_to_model.get(field_type)
        if not model_class:
            raise ValueError(f"No model class found for field type: {field_type}")

        return model_class


class ManualTaskTextField(ManualTaskFieldBase):
    """Schema for text field definition."""

    field_type: Annotated[
        Literal[ManualTaskFieldType.text], Field(description="Type of the field")
    ]
    field_metadata: Annotated[
        ManualTaskTextFieldMetadata,
        Field(description="Field metadata and configuration"),
    ]


class ManualTaskCheckboxField(ManualTaskFieldBase):
    """Schema for checkbox field definition."""

    field_type: Annotated[
        Literal[ManualTaskFieldType.checkbox], Field(description="Type of the field")
    ]
    field_metadata: Annotated[
        ManualTaskCheckboxFieldMetadata,
        Field(description="Field metadata and configuration"),
    ]


class ManualTaskAttachmentField(ManualTaskFieldBase):
    """Schema for attachment field definition."""

    field_type: Annotated[
        Literal[ManualTaskFieldType.attachment], Field(description="Type of the field")
    ]
    field_metadata: Annotated[
        ManualTaskAttachmentFieldMetadata,
        Field(description="Field metadata and configuration"),
    ]


# Type alias for all field types
ManualTaskField = ManualTaskFieldBase


class ManualTaskConfigCreate(FidesSchema):
    """Schema for creating a manual task configuration."""

    model_config = ConfigDict(extra="forbid")

    task_id: Annotated[
        str, Field(description="ID of the task this configuration belongs to")
    ]
    config_type: Annotated[
        ManualTaskConfigurationType, Field(description="Type of configuration")
    ]
    fields: Annotated[
        list[ManualTaskFieldBase], Field(description="List of field definitions")
    ]


class ManualTaskConfigResponse(FidesSchema):
    """Schema for manual task configuration response."""

    model_config = ConfigDict(extra="forbid")

    id: Annotated[str, Field(description="Configuration ID")]
    task_id: Annotated[str, Field(description="Task ID")]
    config_type: Annotated[
        ManualTaskConfigurationType, Field(description="Type of configuration")
    ]
    version: Annotated[int, Field(description="Version of the configuration")]
    is_current: Annotated[
        bool, Field(description="Whether this is the current version")
    ]
    fields: Annotated[
        list[ManualTaskFieldBase], Field(description="List of field definitions")
    ]
    created_at: Annotated[datetime, Field(description="Creation timestamp")]
    updated_at: Annotated[datetime, Field(description="Last update timestamp")]


class ManualTaskConfigUpdate(FidesSchema):
    """Schema for updating a manual task configuration."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    task_id: Annotated[str, Field(description="ID of the task")]
    config_type: Annotated[
        ManualTaskConfigurationType, Field(description="Type of configuration")
    ]
    fields: Annotated[
        list[ManualTaskFieldBase], Field(description="List of field definitions")
    ]


class ManualTaskConfigFieldResponse(FidesSchema):
    """Schema for manual task configuration field response."""

    model_config = ConfigDict(extra="forbid")

    field_key: Annotated[str, Field(description="Unique key for the field")]
    field_type: Annotated[ManualTaskFieldType, Field(description="Type of the field")]
    field_metadata: Annotated[
        ManualTaskFieldMetadata, Field(description="Field metadata and configuration")
    ]
