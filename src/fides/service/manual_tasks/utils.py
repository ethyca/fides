from typing import Any

from pydantic import ValidationError

from fides.api.schemas.manual_tasks.manual_task_config import (
    ManualTaskFieldType,
    ManualTaskAttachmentField,
    ManualTaskCheckboxField,
    ManualTaskTextField,
)


def validate_fields(fields: list[dict[str, Any]]) -> None:
        """Validate field data against the appropriate Pydantic model.
        Raises a ValueError if the field data is invalid.
        """
        # Check for duplicate field keys
        field_keys_set: set[str] = {str(field.get("field_key")) for field in fields}
        if len(field_keys_set) != len(fields):
            raise ValueError(
                "Duplicate field keys found in field updates, field keys must be unique."
            )
        # Check that field_key is present for each field
        for field in fields:
            field_key = field.get("field_key")
            if not field_key:
                raise ValueError("Invalid field data: field_key is required")
            # Skip validation for fields with empty metadata (used for removal)
            if field.get("field_metadata") == {}:
                continue

            try:
                field_type = field.get("field_type")
                if not field_type:
                    raise ValueError("Invalid field data: field_type is required")
                if field_type == ManualTaskFieldType.text:
                    ManualTaskTextField.model_validate(field)
                elif field_type == ManualTaskFieldType.checkbox:
                    ManualTaskCheckboxField.model_validate(field)
                elif field_type == ManualTaskFieldType.attachment:
                    ManualTaskAttachmentField.model_validate(field)
                else:
                    raise ValueError(f"Invalid field type: {field_type}")
            except ValidationError as e:
                raise ValueError(f"Invalid field data: {str(e)}")
