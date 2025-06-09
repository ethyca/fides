from datetime import datetime, timezone

import pytest

from fides.api.schemas.manual_tasks.manual_task_config import (
    ManualTaskAttachmentField,
    ManualTaskAttachmentFieldMetadata,
    ManualTaskCheckboxField,
    ManualTaskCheckboxFieldMetadata,
    ManualTaskConfigCreate,
    ManualTaskConfigFieldResponse,
    ManualTaskConfigResponse,
    ManualTaskConfigUpdate,
    ManualTaskConfigurationType,
    ManualTaskField,
    ManualTaskFieldMetadata,
    ManualTaskFieldType,
    ManualTaskTextField,
    ManualTaskTextFieldMetadata,
)


class TestManualTaskConfigSchemas:
    def test_field_metadata_validation(self):
        """Test validation of field metadata schemas."""
        # Test base field metadata
        metadata = ManualTaskFieldMetadata(
            label="Test Field", required=True, help_text="This is a test field"
        )
        assert metadata.label == "Test Field"
        assert metadata.required == True
        assert metadata.help_text == "This is a test field"

        # Test text field metadata
        text_metadata = ManualTaskTextFieldMetadata(
            label="Text Field",
            required=True,
            help_text="This is a text field",
            placeholder="Enter text",
            default_value="default",
            max_length=100,
            min_length=1,
            pattern="^[a-zA-Z0-9]+$",
        )
        assert text_metadata.placeholder == "Enter text"
        assert text_metadata.default_value == "default"
        assert text_metadata.max_length == 100
        assert text_metadata.min_length == 1
        assert text_metadata.pattern == "^[a-zA-Z0-9]+$"

        # Test checkbox field metadata
        checkbox_metadata = ManualTaskCheckboxFieldMetadata(
            label="Checkbox Field",
            required=True,
            help_text="This is a checkbox field",
            default_value=False,
            label_true="Yes",
            label_false="No",
        )
        assert checkbox_metadata.default_value == False
        assert checkbox_metadata.label_true == "Yes"
        assert checkbox_metadata.label_false == "No"

        # Test attachment field metadata
        attachment_metadata = ManualTaskAttachmentFieldMetadata(
            label="Attachment Field",
            required=True,
            help_text="This is an attachment field",
            file_types=["pdf", "doc"],
            max_file_size=1024,
            multiple=True,
            max_files=5,
            require_attachment_id=True,
        )
        assert attachment_metadata.file_types == ["pdf", "doc"]
        assert attachment_metadata.max_file_size == 1024
        assert attachment_metadata.multiple == True
        assert attachment_metadata.max_files == 5
        assert attachment_metadata.require_attachment_id == True

    def test_field_validation(self):
        """Test validation of field schemas."""
        # Test text field
        text_field = ManualTaskTextField(
            field_key="text_field",
            field_type=ManualTaskFieldType.text,
            field_metadata=ManualTaskTextFieldMetadata(
                label="Text Field", required=True
            ),
        )
        assert text_field.field_key == "text_field"
        assert text_field.field_type == ManualTaskFieldType.text

        # Test checkbox field
        checkbox_field = ManualTaskCheckboxField(
            field_key="checkbox_field",
            field_type=ManualTaskFieldType.checkbox,
            field_metadata=ManualTaskCheckboxFieldMetadata(
                label="Checkbox Field", required=True
            ),
        )
        assert checkbox_field.field_key == "checkbox_field"
        assert checkbox_field.field_type == ManualTaskFieldType.checkbox

        # Test attachment field
        attachment_field = ManualTaskAttachmentField(
            field_key="attachment_field",
            field_type=ManualTaskFieldType.attachment,
            field_metadata=ManualTaskAttachmentFieldMetadata(
                label="Attachment Field",
                required=True,
                file_types=["pdf"],
                max_file_size=1024,
            ),
        )
        assert attachment_field.field_key == "attachment_field"
        assert attachment_field.field_type == ManualTaskFieldType.attachment

    def test_config_schemas(self):
        """Test validation of config schemas."""
        # Test config create
        config_create = ManualTaskConfigCreate(
            task_id="test_task",
            config_type=ManualTaskConfigurationType.access_privacy_request,
            fields=[
                ManualTaskTextField(
                    field_key="text_field",
                    field_type=ManualTaskFieldType.text,
                    field_metadata=ManualTaskTextFieldMetadata(
                        label="Text Field", required=True
                    ),
                )
            ],
        )
        assert config_create.task_id == "test_task"
        assert (
            config_create.config_type
            == ManualTaskConfigurationType.access_privacy_request
        )
        assert len(config_create.fields) == 1

        # Test config response
        config_response = ManualTaskConfigResponse(
            id="test_config",
            task_id="test_task",
            config_type=ManualTaskConfigurationType.access_privacy_request,
            version=1,
            is_current=True,
            fields=[
                ManualTaskTextField(
                    field_key="text_field",
                    field_type=ManualTaskFieldType.text,
                    field_metadata=ManualTaskTextFieldMetadata(
                        label="Text Field", required=True
                    ),
                )
            ],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        assert config_response.id == "test_config"
        assert config_response.version == 1
        assert config_response.is_current == True

        # Test config update
        config_update = ManualTaskConfigUpdate(
            task_id="test_task",
            config_type=ManualTaskConfigurationType.access_privacy_request,
            fields=[
                ManualTaskTextField(
                    field_key="text_field",
                    field_type=ManualTaskFieldType.text,
                    field_metadata=ManualTaskTextFieldMetadata(
                        label="Text Field", required=True
                    ),
                )
            ],
        )
        assert config_update.task_id == "test_task"
        assert len(config_update.fields) == 1

        # Test field response
        field_response = ManualTaskConfigFieldResponse(
            field_key="text_field",
            field_type=ManualTaskFieldType.text,
            field_metadata=ManualTaskTextFieldMetadata(
                label="Text Field", required=True
            ),
        )
        assert field_response.field_key == "text_field"
        assert field_response.field_type == ManualTaskFieldType.text

    def test_field_metadata_validation_errors(self):
        """Test validation errors for field metadata."""
        # Test invalid text field metadata
        with pytest.raises(ValueError):
            ManualTaskTextFieldMetadata(
                label="Text Field",
                required=True,
                min_length=100,  # Invalid: min_length > max_length
                max_length=50,
            )

        # Test invalid checkbox field metadata
        with pytest.raises(ValueError):
            ManualTaskCheckboxFieldMetadata(
                label="Checkbox Field",
                required=True,
                default_value="not_a_bool",  # Invalid: not a boolean
            )

        # Test invalid attachment field metadata
        with pytest.raises(ValueError):
            ManualTaskAttachmentFieldMetadata(
                label="Attachment Field",
                required=True,
                file_types="not_a_list",  # Invalid: not a list
                max_file_size=1024,
            )

    def test_config_validation_errors(self):
        """Test validation errors for config schemas."""
        # Test invalid config type
        with pytest.raises(ValueError):
            ManualTaskConfigCreate(
                task_id="test_task",
                config_type="invalid_type",  # Invalid: not in ManualTaskConfigurationType
                fields=[],
            )

        # Test invalid field type
        with pytest.raises(ValueError):
            ManualTaskTextField(
                field_key="text_field",
                field_type="invalid_type",  # Invalid: not in ManualTaskFieldType
                field_metadata=ManualTaskTextFieldMetadata(
                    label="Text Field", required=True
                ),
            )

        # Test missing required fields
        with pytest.raises(ValueError):
            ManualTaskConfigCreate(
                task_id="test_task",
                config_type=ManualTaskConfigurationType.access_privacy_request,
                fields=None,  # Invalid: fields is required
            )
