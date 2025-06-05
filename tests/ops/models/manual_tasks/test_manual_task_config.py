import pytest
from sqlalchemy.orm import Session

from fides.api.models.manual_tasks.manual_task import (
    ManualTask,
    ManualTaskConfig,
    ManualTaskConfigField,
    ManualTaskInstance,
    ManualTaskSubmission,
)
from fides.api.models.manual_tasks.manual_task_log import ManualTaskLogStatus
from fides.api.schemas.manual_tasks.manual_task_schemas import (
    ManualTaskConfigurationType,
    ManualTaskFieldType,
    ManualTaskType,
)


class TestManualTaskConfigManagement:
    """Tests for managing task configurations."""

    def test_create_config(self, db: Session, manual_task: ManualTask):
        """Test creating a basic task configuration."""
        config = ManualTaskConfig.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_type": ManualTaskConfigurationType.access_privacy_request,
            },
        )
        assert config.id is not None
        assert config.task_id == manual_task.id
        assert config.config_type == ManualTaskConfigurationType.access_privacy_request

    @pytest.mark.parametrize(
        "field_type,field_metadata,expected_data",
        [
            (
                ManualTaskFieldType.form,
                {
                    "label": "Test Form Field",
                    "required": True,
                    "help_text": "This is a test form field",
                },
                {"test_form_field": "test form value"},
            ),
            (
                ManualTaskFieldType.checkbox,
                {
                    "label": "Test Checkbox Field",
                    "required": True,
                    "help_text": "This is a test checkbox field",
                    "default_value": False,
                },
                {"test_checkbox_field": True},
            ),
            (
                ManualTaskFieldType.attachment,
                {
                    "label": "Test Attachment Field",
                    "required": True,
                    "help_text": "This is a test attachment field",
                    "file_types": ["pdf"],
                    "max_file_size": 1048576,
                    "multiple": True,
                    "max_files": 2,
                    "require_attachment_id": True,
                },
                {
                    "test_attachment_field": {
                        "filename": "test.pdf",
                        "size": 1024,
                        "attachment_ids": ["test_attachment_1", "test_attachment_2"],
                    }
                },
            ),
        ],
    )
    def test_add_field(
        self,
        db: Session,
        manual_task_config: ManualTaskConfig,
        field_type,
        field_metadata,
        expected_data,
    ):
        """Test adding different types of fields to a configuration."""
        field = ManualTaskConfigField(
            config_id=manual_task_config.id,
            field_key=f"test_{field_type}_field",
            field_type=field_type,
            field_metadata=field_metadata,
        )
        manual_task_config.add_field(field)
        assert len(manual_task_config.field_definitions) == 1
        assert (
            manual_task_config.field_definitions[0].field_key
            == f"test_{field_type}_field"
        )
        assert manual_task_config.field_definitions[0].field_type == field_type

    def test_remove_field(
        self,
        db: Session,
        manual_task_config: ManualTaskConfig,
        manual_task_field: ManualTaskConfigField,
    ):
        """Test removing a field from a configuration."""
        assert len(manual_task_config.field_definitions) == 1
        manual_task_config.remove_field("test_field")
        assert len(manual_task_config.field_definitions) == 0

    def test_get_field(
        self,
        db: Session,
        manual_task_config: ManualTaskConfig,
        manual_task_field: ManualTaskConfigField,
    ):
        """Test retrieving a field by key."""
        field = manual_task_config.get_field("test_field")
        assert field is not None
        assert field.id == manual_task_field.id


class TestManualTaskConfigValidation:
    """Tests for manual task configuration validation."""

    def test_validate_submission(
        self,
        db: Session,
        manual_task_config_with_fields: ManualTaskConfig,
    ):
        """Test validating submissions against a configuration."""
        # Test valid submission
        valid_submission = {
            "test_form_field": "test value",
            "test_checkbox_field": True,
            "test_attachment_field": {
                "filename": "test.pdf",
                "size": 1024,
                "attachment_ids": ["test_attachment_1"],
            },
        }
        assert (
            manual_task_config_with_fields.validate_submission(valid_submission) is True
        )

        # Test invalid submission (missing required field)
        invalid_submission = {
            "test_form_field": "test value",
            "test_checkbox_field": True,
        }
        assert (
            manual_task_config_with_fields.validate_submission(invalid_submission)
            is False
        )

        # Test invalid submission (wrong type)
        invalid_type_submission = {
            "test_form_field": "test value",
            "test_checkbox_field": "not a boolean",
            "test_attachment_field": {
                "filename": "test.pdf",
                "size": 1024,
                "attachment_ids": ["test_attachment_1"],
            },
        }
        assert (
            manual_task_config_with_fields.validate_submission(invalid_type_submission)
            is False
        )

        # Test invalid submission (missing attachment_ids)
        invalid_attachment_submission = {
            "test_form_field": "test value",
            "test_checkbox_field": True,
            "test_attachment_field": {"filename": "test.pdf", "size": 1024},
        }
        assert (
            manual_task_config_with_fields.validate_submission(
                invalid_attachment_submission
            )
            is False
        )

        # Test invalid submission (too many attachments)
        too_many_attachments_submission = {
            "test_form_field": "test value",
            "test_checkbox_field": True,
            "test_attachment_field": {
                "filename": "test.pdf",
                "size": 1024,
                "attachment_ids": [
                    "test_attachment_1",
                    "test_attachment_2",
                    "test_attachment_3",
                ],
            },
        }
        assert (
            manual_task_config_with_fields.validate_submission(
                too_many_attachments_submission
            )
            is False
        )


class TestManualTaskConfigField:
    """Tests for manual task configuration fields."""

    def test_validate_field_data(
        self,
        db: Session,
        manual_task_form_field: ManualTaskConfigField,
        manual_task_checkbox_field: ManualTaskConfigField,
    ):
        """Test validating field data."""
        # Test form field
        assert manual_task_form_field.validate_field_data("test value") is True
        assert manual_task_form_field.validate_field_data(None) is False

        # Test checkbox field
        assert manual_task_checkbox_field.validate_field_data(True) is True
        assert manual_task_checkbox_field.validate_field_data(False) is True
        assert manual_task_checkbox_field.validate_field_data("not a boolean") is False

    def test_field_properties(
        self,
        db: Session,
        manual_task_form_field: ManualTaskConfigField,
    ):
        """Test field properties and metadata."""
        assert manual_task_form_field.label == "Test Form Field"
        assert manual_task_form_field.required is True
        assert manual_task_form_field.help_text == "This is a test form field"

        # Test updating metadata
        new_metadata = {
            "label": "Updated Field",
            "required": False,
            "help_text": "Updated help text",
        }
        manual_task_form_field.update_metadata(new_metadata)
        assert manual_task_form_field.label == "Updated Field"
        assert manual_task_form_field.required is False
        assert manual_task_form_field.help_text == "Updated help text"


class TestManualTaskConfig:
    def test_create_config_with_invalid_fields(
        self, db: Session, manual_task: ManualTask
    ):
        """Test creating a config with invalid field definitions."""
        # Test with missing required field metadata
        with pytest.raises(ValueError, match="Field metadata is required"):
            ManualTaskConfig.create(
                db=db,
                data={
                    "task_id": manual_task.id,
                    "config_type": ManualTaskConfigurationType.access_privacy_request,
                    "fields": [
                        {
                            "field_key": "test_field",
                            "field_type": ManualTaskFieldType.form,
                        }
                    ],
                },
            )

        # Test with invalid field type
        with pytest.raises(ValueError, match="Invalid field type"):
            ManualTaskConfig.create(
                db=db,
                data={
                    "task_id": manual_task.id,
                    "config_type": ManualTaskConfigurationType.access_privacy_request,
                    "fields": [
                        {
                            "field_key": "test_field",
                            "field_type": "invalid_type",
                            "field_metadata": {
                                "label": "Test Field",
                                "required": True,
                            },
                        }
                    ],
                },
            )

    def test_validate_submission_with_invalid_data(
        self, db: Session, manual_task_config: ManualTaskConfig
    ):
        """Test validation of submissions with invalid data."""
        # Create a required field
        field = ManualTaskConfigField.create(
            db=db,
            data={
                "task_id": manual_task_config.task_id,
                "config_id": manual_task_config.id,
                "field_key": "test_field",
                "field_type": ManualTaskFieldType.form,
                "field_metadata": {
                    "label": "Test Field",
                    "required": True,
                    "help_text": "This is a test field",
                },
            },
        )

        # Test with missing required field
        assert not manual_task_config.validate_submission({}, field_id=field.id)

        # Test with invalid field type
        assert not manual_task_config.validate_submission(
            {"test_field": 123}, field_id=field.id
        )

        # Test with invalid field_id
        assert not manual_task_config.validate_submission(
            {"test_field": "test value"}, field_id="invalid_field_id"
        )

    def test_config_with_multiple_field_types(
        self, db: Session, manual_task: ManualTask
    ):
        """Test creating a config with multiple field types."""
        config = ManualTaskConfig.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_type": ManualTaskConfigurationType.access_privacy_request,
                "fields": [
                    {
                        "field_key": "form_field",
                        "field_type": ManualTaskFieldType.form,
                        "field_metadata": {
                            "label": "Form Field",
                            "required": True,
                            "help_text": "This is a form field",
                        },
                    },
                    {
                        "field_key": "checkbox_field",
                        "field_type": ManualTaskFieldType.checkbox,
                        "field_metadata": {
                            "label": "Checkbox Field",
                            "required": False,
                            "help_text": "This is a checkbox field",
                            "default_value": False,
                        },
                    },
                    {
                        "field_key": "attachment_field",
                        "field_type": ManualTaskFieldType.attachment,
                        "field_metadata": {
                            "label": "Attachment Field",
                            "required": True,
                            "help_text": "This is an attachment field",
                            "file_types": ["pdf"],
                            "max_file_size": 1048576,
                            "multiple": True,
                            "max_files": 2,
                            "require_attachment_id": True,
                        },
                    },
                ],
            },
        )

        assert len(config.field_definitions) == 3
        assert any(f.field_type == ManualTaskFieldType.form for f in config.field_definitions)
        assert any(f.field_type == ManualTaskFieldType.checkbox for f in config.field_definitions)
        assert any(f.field_type == ManualTaskFieldType.attachment for f in config.field_definitions)

    def test_config_deletion_with_active_instances(
        self, db: Session, manual_task_config: ManualTaskConfig
    ):
        """Test attempting to delete a config with active instances."""
        # Create an instance
        instance = ManualTaskInstance.create(
            db=db,
            data={
                "task_id": manual_task_config.task_id,
                "config_id": manual_task_config.id,
                "entity_id": "test_entity",
                "entity_type": "test_type",
            },
        )

        # Try to delete the config
        with pytest.raises(ValueError, match="Cannot delete configuration with active instances"):
            manual_task_config.delete(db)

        # Verify the config still exists
        assert (
            db.query(ManualTaskConfig)
            .filter(ManualTaskConfig.id == manual_task_config.id)
            .first()
            is not None
        )

    def test_config_deletion_without_instances(
        self, db: Session, manual_task_config: ManualTaskConfig
    ):
        """Test deleting a config without any instances."""
        # Delete the config
        manual_task_config.delete(db)

        # Verify the config is deleted
        assert (
            db.query(ManualTaskConfig)
            .filter(ManualTaskConfig.id == manual_task_config.id)
            .first()
            is None
        )

    def test_config_field_validation(
        self, db: Session, manual_task_config: ManualTaskConfig
    ):
        """Test validation of different field types."""
        # Create a checkbox field
        checkbox_field = ManualTaskConfigField.create(
            db=db,
            data={
                "task_id": manual_task_config.task_id,
                "config_id": manual_task_config.id,
                "field_key": "checkbox_field",
                "field_type": ManualTaskFieldType.checkbox,
                "field_metadata": {
                    "label": "Checkbox Field",
                    "required": True,
                    "help_text": "This is a checkbox field",
                    "default_value": False,
                },
            },
        )

        # Test checkbox validation
        assert manual_task_config.validate_submission(
            {"checkbox_field": True}, field_id=checkbox_field.id
        )
        assert not manual_task_config.validate_submission(
            {"checkbox_field": "not_a_boolean"}, field_id=checkbox_field.id
        )

        # Create an attachment field
        attachment_field = ManualTaskConfigField.create(
            db=db,
            data={
                "task_id": manual_task_config.task_id,
                "config_id": manual_task_config.id,
                "field_key": "attachment_field",
                "field_type": ManualTaskFieldType.attachment,
                "field_metadata": {
                    "label": "Attachment Field",
                    "required": True,
                    "help_text": "This is an attachment field",
                    "file_types": ["pdf"],
                    "max_file_size": 1048576,
                    "multiple": True,
                    "max_files": 2,
                    "require_attachment_id": True,
                },
            },
        )

        # Test attachment validation
        valid_attachment_data = {
            "attachment_field": {
                "filename": "test.pdf",
                "size": 1024,
                "attachment_ids": ["test_attachment_1", "test_attachment_2"],
            }
        }
        assert manual_task_config.validate_submission(
            valid_attachment_data, field_id=attachment_field.id
        )

        # Test invalid attachment data - wrong file type
        invalid_file_type_data = {
            "attachment_field": {
                "filename": "test.txt",
                "size": 1024,
                "attachment_ids": ["test_attachment_1"],
            }
        }
        assert not manual_task_config.validate_submission(
            invalid_file_type_data, field_id=attachment_field.id
        )

        # Test invalid attachment data - file too large
        invalid_size_data = {
            "attachment_field": {
                "filename": "test.pdf",
                "size": 2048576,
                "attachment_ids": ["test_attachment_1"],
            }
        }
        assert not manual_task_config.validate_submission(
            invalid_size_data, field_id=attachment_field.id
        )

        # Test invalid attachment data - too many files
        too_many_files_data = {
            "attachment_field": {
                "filename": "test.pdf",
                "size": 1024,
                "attachment_ids": ["test_attachment_1", "test_attachment_2", "test_attachment_3"],
            }
        }
        assert not manual_task_config.validate_submission(
            too_many_files_data, field_id=attachment_field.id
        )

        # Test invalid attachment data - missing required attachment_ids
        missing_attachment_ids_data = {
            "attachment_field": {
                "filename": "test.pdf",
                "size": 1024,
            }
        }
        assert not manual_task_config.validate_submission(
            missing_attachment_ids_data, field_id=attachment_field.id
        )
