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


class TestManualTaskFieldMetadata:
    """Tests for the base field metadata schema."""

    def test_base_field_metadata_creation(self):
        """Test creation of base field metadata with required fields."""
        metadata = ManualTaskFieldMetadata(
            label="Test Field", required=True, help_text="This is a test field"
        )
        assert metadata.label == "Test Field"
        assert metadata.required == True
        assert metadata.help_text == "This is a test field"

    def test_base_field_metadata_optional_fields(self):
        """Test creation of base field metadata with optional fields."""
        metadata = ManualTaskFieldMetadata(label="Test Field")
        assert metadata.label == "Test Field"
        assert metadata.required == False
        assert metadata.help_text is None

    def test_base_field_metadata_extra_fields(self):
        """Test that extra fields are allowed in base field metadata."""
        metadata = ManualTaskFieldMetadata(
            label="Test Field",
            required=True,
            help_text="This is a test field",
            extra_field="allowed",
        )
        assert hasattr(metadata, "extra_field")


class TestManualTaskTextFieldMetadata:
    """Tests for text field metadata schema."""

    def test_text_field_metadata_creation(self):
        """Test creation of text field metadata with all fields."""
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

    def test_text_field_metadata_optional_fields(self):
        """Test creation of text field metadata with only required fields."""
        text_metadata = ManualTaskTextFieldMetadata(label="Text Field", required=True)
        assert text_metadata.placeholder is None
        assert text_metadata.default_value is None
        assert text_metadata.max_length is None
        assert text_metadata.min_length is None
        assert text_metadata.pattern is None

    def test_text_field_metadata_length_validation(self):
        """Test validation of min_length and max_length constraints."""
        # Test min_length > max_length
        with pytest.raises(ValueError) as exc_info:
            ManualTaskTextFieldMetadata(
                label="Text Field",
                required=True,
                min_length=100,
                max_length=50,
            )
        assert "min_length cannot be greater than max_length" in str(exc_info.value)

        # Test max_length < min_length (should raise the same error)
        with pytest.raises(ValueError) as exc_info:
            ManualTaskTextFieldMetadata(
                label="Text Field",
                required=True,
                min_length=10,
                max_length=5,
            )
        assert "min_length cannot be greater than max_length" in str(exc_info.value)


class TestManualTaskCheckboxFieldMetadata:
    """Tests for checkbox field metadata schema."""

    def test_checkbox_field_metadata_creation(self):
        """Test creation of checkbox field metadata with all fields."""
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

    def test_checkbox_field_metadata_optional_fields(self):
        """Test creation of checkbox field metadata with only required fields."""
        checkbox_metadata = ManualTaskCheckboxFieldMetadata(
            label="Checkbox Field", required=True
        )
        assert checkbox_metadata.default_value == False
        assert checkbox_metadata.label_true is None
        assert checkbox_metadata.label_false is None

    def test_checkbox_field_metadata_validation(self):
        """Test validation of checkbox field metadata."""
        with pytest.raises(ValueError) as exc_info:
            ManualTaskCheckboxFieldMetadata(
                label="Checkbox Field",
                required=True,
                default_value="not_a_bool",
            )
        assert "Input should be a valid boolean" in str(exc_info.value)


class TestManualTaskAttachmentFieldMetadata:
    """Tests for attachment field metadata schema."""

    def test_attachment_field_metadata_creation(self):
        """Test creation of attachment field metadata with all fields."""
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

    def test_attachment_field_metadata_validation(self):
        """Test validation of attachment field metadata."""
        # Test max_files validation when multiple is True
        with pytest.raises(ValueError) as exc_info:
            ManualTaskAttachmentFieldMetadata(
                label="Attachment Field",
                required=True,
                file_types=["pdf"],
                max_file_size=1024,
                multiple=True,
            )
        assert "max_files must be set when multiple is True" in str(exc_info.value)

        # Test file_types validation
        with pytest.raises(ValueError) as exc_info:
            ManualTaskAttachmentFieldMetadata(
                label="Attachment Field",
                required=True,
                file_types="not_a_list",
                max_file_size=1024,
            )
        assert "Input should be a valid list" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            ManualTaskAttachmentFieldMetadata(
                label="Attachment Field",
                required=True,
                file_types=["pdf", 123],
                max_file_size=1024,
            )
        assert "Input should be a valid string" in str(exc_info.value)


class TestManualTaskField:
    """Tests for field type schemas."""

    def test_text_field_creation(self):
        """Test creation of text field."""
        text_field = ManualTaskTextField(
            field_key="text_field",
            field_type=ManualTaskFieldType.text,
            field_metadata=ManualTaskTextFieldMetadata(
                label="Text Field", required=True
            ),
        )
        assert text_field.field_key == "text_field"
        assert text_field.field_type == ManualTaskFieldType.text

    def test_checkbox_field_creation(self):
        """Test creation of checkbox field."""
        checkbox_field = ManualTaskCheckboxField(
            field_key="checkbox_field",
            field_type=ManualTaskFieldType.checkbox,
            field_metadata=ManualTaskCheckboxFieldMetadata(
                label="Checkbox Field", required=True
            ),
        )
        assert checkbox_field.field_key == "checkbox_field"
        assert checkbox_field.field_type == ManualTaskFieldType.checkbox

    def test_attachment_field_creation(self):
        """Test creation of attachment field."""
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

    def test_invalid_field_type(self):
        """Test validation of field type."""
        with pytest.raises(ValueError):
            ManualTaskTextField(
                field_key="text_field",
                field_type="invalid_type",
                field_metadata=ManualTaskTextFieldMetadata(
                    label="Text Field", required=True
                ),
            )


class TestManualTaskConfig:
    """Tests for config schemas."""

    def test_config_create(self):
        """Test creation of config."""
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

    def test_config_response(self):
        """Test creation of config response."""
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

    def test_config_update(self):
        """Test creation of config update."""
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

    def test_config_validation_errors(self):
        """Test validation errors for config schemas."""
        # Test invalid config type
        with pytest.raises(ValueError):
            ManualTaskConfigCreate(
                task_id="test_task",
                config_type="invalid_type",
                fields=[],
            )

        # Test missing required fields
        with pytest.raises(ValueError):
            ManualTaskConfigCreate(
                task_id="test_task",
                config_type=ManualTaskConfigurationType.access_privacy_request,
                fields=None,
            )

    def test_config_extra_fields(self):
        """Test that extra fields are forbidden in config schemas."""
        # Test config create
        with pytest.raises(ValueError):
            ManualTaskConfigCreate(
                task_id="test_task",
                config_type=ManualTaskConfigurationType.access_privacy_request,
                fields=[],
                extra_field="not_allowed",
            )

        # Test config response
        with pytest.raises(ValueError):
            ManualTaskConfigResponse(
                id="test_config",
                task_id="test_task",
                config_type=ManualTaskConfigurationType.access_privacy_request,
                version=1,
                is_current=True,
                fields=[],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                extra_field="not_allowed",
            )


class TestManualTaskConfigFieldResponse:
    """Tests for field response schema."""

    def test_field_response_creation(self):
        """Test creation of field response."""
        field_response = ManualTaskConfigFieldResponse(
            field_key="text_field",
            field_type=ManualTaskFieldType.text,
            field_metadata=ManualTaskTextFieldMetadata(
                label="Text Field", required=True
            ),
        )
        assert field_response.field_key == "text_field"
        assert field_response.field_type == ManualTaskFieldType.text
