import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

from fides.api.models.manual_tasks.manual_task import (
    ManualTask,
    ManualTaskConfig,
    ManualTaskConfigField,
    ManualTaskInstance,
    ManualTaskReference,
    ManualTaskSubmission,
)
from fides.api.models.manual_tasks.manual_task_log import (
    ManualTaskLog,
    ManualTaskLogStatus,
)
from fides.api.models.manual_tasks.status import StatusType
from fides.api.schemas.manual_tasks.manual_task_schemas import (
    ManualTaskAttachmentField,
    ManualTaskCheckboxField,
    ManualTaskConfigurationType,
    ManualTaskFieldType,
    ManualTaskFormField,
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

    def test_get_by_type(self, db: Session, manual_task: ManualTask):
        """Test getting a config by type."""
        # Create a config
        config = ManualTaskConfig.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_type": ManualTaskConfigurationType.access_privacy_request,
            },
        )

        # Get by type
        found_config = ManualTaskConfig.get_by_type(
            db=db,
            task_id=manual_task.id,
            config_type=ManualTaskConfigurationType.access_privacy_request,
        )
        assert found_config is not None
        assert found_config.id == config.id

        # Test with non-existent type
        not_found = ManualTaskConfig.get_by_type(
            db=db,
            task_id=manual_task.id,
            config_type="non_existent_type",
        )
        assert not_found is None

    def test_get_by_id(self, db: Session, manual_task: ManualTask):
        """Test getting a config by ID."""
        # Create a config
        config = ManualTaskConfig.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_type": ManualTaskConfigurationType.access_privacy_request,
            },
        )

        # Get by ID
        found_config = ManualTaskConfig.get_by_id(
            db=db,
            task_id=manual_task.id,
            task_config_id=config.id,
        )
        assert found_config is not None
        assert found_config.id == config.id

        # Test with non-existent ID
        not_found = ManualTaskConfig.get_by_id(
            db=db,
            task_id=manual_task.id,
            task_config_id="non_existent_id",
        )
        assert not_found is None

    def test_create_for_task(self, db: Session, manual_task: ManualTask):
        """Test creating a config for a task with fields."""
        fields = [
            {
                "field_key": "test_field",
                "field_type": ManualTaskFieldType.form,
                "field_metadata": {
                    "label": "Test Field",
                    "required": True,
                },
            }
        ]

        config = ManualTaskConfig.create_for_task(
            db=db,
            task_id=manual_task.id,
            config_type=ManualTaskConfigurationType.access_privacy_request,
            fields=fields,
        )

        assert config.id is not None
        assert config.task_id == manual_task.id
        assert config.config_type == ManualTaskConfigurationType.access_privacy_request
        assert len(config.field_definitions) == 1
        assert config.field_definitions[0].field_key == "test_field"


class TestManualTaskConfigField:
    """Tests for manual task configuration fields."""

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

    def test_get_field_model(
        self, db: Session, manual_task_form_field: ManualTaskConfigField
    ):
        """Test getting the appropriate field model."""
        # Test form field
        form_model = manual_task_form_field._get_field_model()
        assert form_model == ManualTaskFormField

        # Test checkbox field
        checkbox_field = ManualTaskConfigField.create(
            db=db,
            data={
                "task_id": manual_task_form_field.task_id,
                "config_id": manual_task_form_field.config_id,
                "field_key": "checkbox_field",
                "field_type": ManualTaskFieldType.checkbox,
                "field_metadata": {
                    "label": "Checkbox Field",
                    "required": False,
                },
            },
        )
        checkbox_model = checkbox_field._get_field_model()
        assert checkbox_model == ManualTaskCheckboxField

        # Test attachment field
        attachment_field = ManualTaskConfigField.create(
            db=db,
            data={
                "task_id": manual_task_form_field.task_id,
                "config_id": manual_task_form_field.config_id,
                "field_key": "attachment_field",
                "field_type": ManualTaskFieldType.attachment,
                "field_metadata": {
                    "label": "Attachment Field",
                    "required": True,
                },
            },
        )
        attachment_model = attachment_field._get_field_model()
        assert attachment_model == ManualTaskAttachmentField

        # Test invalid field type by creating a field with invalid type
        with pytest.raises(ValueError, match="Invalid field type"):
            ManualTaskConfigField.create(
                db=db,
                data={
                    "task_id": manual_task_form_field.task_id,
                    "config_id": manual_task_form_field.config_id,
                    "field_key": "invalid_field",
                    "field_type": "invalid_type",
                    "field_metadata": {
                        "label": "Invalid Field",
                        "required": True,
                    },
                },
            )

    def test_get_field_metadata(
        self, db: Session, manual_task_form_field: ManualTaskConfigField
    ):
        """Test getting field metadata."""
        metadata = manual_task_form_field.get_field_metadata()
        assert metadata == manual_task_form_field.field_metadata
        assert metadata["label"] == "Test Form Field"
        assert metadata["required"] is True
        assert metadata["help_text"] == "This is a test form field"


class TestManualTaskConfig:
    """Tests for manual task configuration."""

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
        assert any(
            f.field_type == ManualTaskFieldType.form for f in config.field_definitions
        )
        assert any(
            f.field_type == ManualTaskFieldType.checkbox
            for f in config.field_definitions
        )
        assert any(
            f.field_type == ManualTaskFieldType.attachment
            for f in config.field_definitions
        )

    def test_config_relationships(self, db: Session, manual_task: ManualTask):
        """Test relationships between config and related models."""
        # Create a config
        config = ManualTaskConfig.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_type": ManualTaskConfigurationType.access_privacy_request,
                "fields": [
                    {
                        "field_key": "test_field",
                        "field_type": ManualTaskFieldType.form,
                        "field_metadata": {
                            "label": "Test Field",
                            "required": True,
                        },
                    },
                ],
            },
        )

        # Create reference using the model
        ManualTaskReference.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "reference_id": config.id,
                "reference_type": "manual_task_config",
            },
        )

        # Verify relationships
        assert config.task == manual_task
        assert config in manual_task.configs
        assert len(config.field_definitions) == 1
        assert config.field_definitions[0].config == config

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
        with pytest.raises(
            ValueError, match="Cannot delete configuration with 1 active instances"
        ):
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

    def test_config_update(self, db: Session, manual_task: ManualTask):
        """Test updating a config's fields."""
        # Create initial config
        config = ManualTaskConfig.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_type": ManualTaskConfigurationType.access_privacy_request,
                "fields": [
                    {
                        "field_key": "initial_field",
                        "field_type": ManualTaskFieldType.form,
                        "field_metadata": {
                            "label": "Initial Field",
                            "required": True,
                        },
                    },
                ],
            },
        )

        # Update config with new fields
        updated_config = config.update(
            db=db,
            data={
                "fields": [
                    {
                        "field_key": "updated_field",
                        "field_type": ManualTaskFieldType.form,
                        "field_metadata": {
                            "label": "Updated Field",
                            "required": True,
                        },
                    },
                ],
            },
        )

        # Verify fields were updated
        assert len(updated_config.field_definitions) == 1
        assert updated_config.field_definitions[0].field_key == "updated_field"
        assert (
            updated_config.field_definitions[0].field_metadata["label"]
            == "Updated Field"
        )


class TestManualTaskSubmission:
    """Tests for manual task submissions."""

    def test_create_submission(
        self, db: Session, manual_task_instance: ManualTaskInstance
    ):
        """Test creating a new submission."""
        form_field = ManualTaskConfigField.create(
            db=db,
            data={
                "task_id": manual_task_instance.task_id,
                "config_id": manual_task_instance.config_id,
                "field_key": "test_form_field",
                "field_type": ManualTaskFieldType.form,
                "field_metadata": {
                    "label": "Test Form Field",
                    "required": True,
                },
            },
        )

        # Add field to config
        config = manual_task_instance.config
        config.field_definitions.append(form_field)
        db.commit()

        # Create submission
        submission = ManualTaskSubmission.create(
            db=db,
            data={
                "task_id": manual_task_instance.task_id,
                "config_id": manual_task_instance.config_id,
                "field_id": form_field.id,
                "instance_id": manual_task_instance.id,
                "submitted_by": 1,
                "data": {"test_form_field": "test value"},
            },
            check_name=True,
        )

        assert submission.id is not None
        assert submission.task_id == manual_task_instance.task_id
        assert submission.config_id == manual_task_instance.config_id
        assert submission.field_id == form_field.id
        assert submission.instance_id == manual_task_instance.id
        assert submission.submitted_by == 1
        assert submission.data == {"test_form_field": "test value"}

    def test_create_submission_with_invalid_data(
        self, db: Session, manual_task_instance: ManualTaskInstance
    ):
        """Test creating a submission with invalid data."""
        form_field = ManualTaskConfigField.create(
            db=db,
            data={
                "task_id": manual_task_instance.task_id,
                "config_id": manual_task_instance.config_id,
                "field_key": "test_form_field",
                "field_type": ManualTaskFieldType.form,
                "field_metadata": {
                    "label": "Test Form Field",
                    "required": True,
                },
            },
        )

        # Add field to config
        config = manual_task_instance.config
        config.field_definitions.append(form_field)
        db.commit()

        # Test with no data
        with pytest.raises(
            ValueError, match="Submission must contain data for exactly one field"
        ):
            ManualTaskSubmission.create(
                db=db,
                data={
                    "task_id": manual_task_instance.task_id,
                    "config_id": manual_task_instance.config_id,
                    "field_id": form_field.id,
                    "instance_id": manual_task_instance.id,
                    "submitted_by": 1,
                    "data": {},
                },
                check_name=True,
            )

        # Test with multiple fields
        with pytest.raises(
            ValueError, match="Submission must contain data for exactly one field"
        ):
            ManualTaskSubmission.create(
                db=db,
                data={
                    "task_id": manual_task_instance.task_id,
                    "config_id": manual_task_instance.config_id,
                    "field_id": form_field.id,
                    "instance_id": manual_task_instance.id,
                    "submitted_by": 1,
                    "data": {
                        "test_form_field": "value1",
                        "another_field": "value2",
                    },
                },
                check_name=True,
            )

        # Test with wrong field key
        with pytest.raises(ValueError, match="Data must be for field test_form_field"):
            ManualTaskSubmission.create(
                db=db,
                data={
                    "task_id": manual_task_instance.task_id,
                    "config_id": manual_task_instance.config_id,
                    "field_id": form_field.id,
                    "instance_id": manual_task_instance.id,
                    "submitted_by": 1,
                    "data": {"wrong_field": "value"},
                },
                check_name=True,
            )


class TestManualTaskFieldValidation:
    """Tests for field validation and status updates."""

    def test_get_incomplete_fields(
        self, db: Session, manual_task_instance: ManualTaskInstance
    ):
        """Test getting incomplete fields for an instance."""
        # Create required fields
        required_field = ManualTaskConfigField.create(
            db=db,
            data={
                "task_id": manual_task_instance.task_id,
                "config_id": manual_task_instance.config_id,
                "field_key": "required_field",
                "field_type": ManualTaskFieldType.form,
                "field_metadata": {
                    "label": "Required Field",
                    "required": True,
                    "help_text": "This field is required",
                },
            },
        )

        optional_field = ManualTaskConfigField.create(
            db=db,
            data={
                "task_id": manual_task_instance.task_id,
                "config_id": manual_task_instance.config_id,
                "field_key": "optional_field",
                "field_type": ManualTaskFieldType.form,
                "field_metadata": {
                    "label": "Optional Field",
                    "required": False,
                    "help_text": "This field is optional",
                },
            },
        )

        # Add fields to config
        config = manual_task_instance.config
        config.field_definitions.extend([required_field, optional_field])
        db.commit()

        # Get incomplete fields
        incomplete_fields = manual_task_instance.get_incomplete_fields()
        assert len(incomplete_fields) == 1  # Only required field should be incomplete
        assert incomplete_fields[0].field_key == "required_field"

        # Create a submission for the required field
        ManualTaskSubmission.create_or_update(
            db=db,
            data={
                "task_id": manual_task_instance.task_id,
                "config_id": manual_task_instance.config_id,
                "field_id": required_field.id,
                "instance_id": manual_task_instance.id,
                "submitted_by": 1,
                "data": {"required_field": "test value"},
            },
        )

        # Get incomplete fields again
        incomplete_fields = manual_task_instance.get_incomplete_fields()
        assert len(incomplete_fields) == 0  # No incomplete fields now

    def test_get_incomplete_fields_with_no_fields(
        self, db: Session, manual_task_instance: ManualTaskInstance
    ):
        """Test getting incomplete fields when there are no fields."""
        # Remove all fields from the config
        manual_task_instance.config.field_definitions = []
        db.commit()

        incomplete_fields = manual_task_instance.get_incomplete_fields()
        assert len(incomplete_fields) == 0

    def test_update_status_from_submissions_with_no_submissions(
        self, db: Session, manual_task_instance: ManualTaskInstance
    ):
        """Test updating status from submissions when there are no submissions."""
        manual_task_instance.update_status_from_submissions(db)
        assert manual_task_instance.status == StatusType.pending


class TestManualTaskConfigFieldValidation:
    """Tests for field validation at the model level."""

    @pytest.fixture
    def task_config(self, db: Session, manual_task: ManualTask):
        """Create a config for the test."""
        return ManualTaskConfig.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_type": ManualTaskConfigurationType.access_privacy_request,
            },
        )

    def test_invalid_field_type(
        self, db: Session, manual_task: ManualTask, task_config: ManualTaskConfig
    ):
        """Test that invalid field types are rejected."""
        with pytest.raises(ValueError, match="Invalid field type"):
            ManualTaskConfigField.create(
                db=db,
                data={
                    "task_id": manual_task.id,
                    "config_id": task_config.id,
                    "field_key": "test_field",
                    "field_type": "invalid_type",
                    "field_metadata": {
                        "label": "Test Field",
                        "required": True,
                    },
                },
            )

    def test_missing_field_metadata(
        self, db: Session, manual_task: ManualTask, task_config: ManualTaskConfig
    ):
        """Test that field metadata is required."""
        with pytest.raises(ValueError, match="Field metadata is required"):
            ManualTaskConfigField.create(
                db=db,
                data={
                    "task_id": manual_task.id,
                    "config_id": task_config.id,
                    "field_key": "test_field",
                    "field_type": ManualTaskFieldType.form,
                },
            )

    def test_field_metadata_validation(
        self, db: Session, manual_task: ManualTask, task_config: ManualTaskConfig
    ):
        """Test that field metadata is required and field type is valid."""

        # Test with valid field type and metadata
        field = ManualTaskConfigField.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": task_config.id,
                "field_key": "test_field",
                "field_type": ManualTaskFieldType.form,
                "field_metadata": {
                    "label": "Test Field",
                    "required": True,
                },
            },
        )
        assert field.id is not None
        assert field.field_type == ManualTaskFieldType.form
        assert field.field_metadata["label"] == "Test Field"
        assert field.field_metadata["required"] is True


class TestManualTaskSubmissionValidation:
    """Tests for submission validation at the model level."""

    def test_submission_with_multiple_fields(
        self, db: Session, manual_task_instance: ManualTaskInstance
    ):
        """Test that submissions must contain exactly one field."""
        form_field = ManualTaskConfigField.create(
            db=db,
            data={
                "task_id": manual_task_instance.task_id,
                "config_id": manual_task_instance.config_id,
                "field_key": "test_form_field",
                "field_type": ManualTaskFieldType.form,
                "field_metadata": {
                    "label": "Test Form Field",
                    "required": True,
                },
            },
        )

        # Add field to config
        config = manual_task_instance.config
        config.field_definitions.append(form_field)
        db.commit()

        # Test with multiple fields
        with pytest.raises(
            ValueError, match="Submission must contain data for exactly one field"
        ):
            ManualTaskSubmission.create_or_update(
                db=db,
                data={
                    "task_id": manual_task_instance.task_id,
                    "config_id": manual_task_instance.config_id,
                    "field_id": form_field.id,
                    "instance_id": manual_task_instance.id,
                    "submitted_by": 1,
                    "data": {"test_form_field": "value1", "another_field": "value2"},
                },
            )

    def test_submission_with_no_fields(
        self, db: Session, manual_task_instance: ManualTaskInstance
    ):
        """Test that submissions must contain at least one field."""
        form_field = ManualTaskConfigField.create(
            db=db,
            data={
                "task_id": manual_task_instance.task_id,
                "config_id": manual_task_instance.config_id,
                "field_key": "test_form_field",
                "field_type": ManualTaskFieldType.form,
                "field_metadata": {
                    "label": "Test Form Field",
                    "required": True,
                },
            },
        )

        # Add field to config
        config = manual_task_instance.config
        config.field_definitions.append(form_field)
        db.commit()

        # Test with no fields
        with pytest.raises(
            ValueError, match="Submission must contain data for exactly one field"
        ):
            ManualTaskSubmission.create_or_update(
                db=db,
                data={
                    "task_id": manual_task_instance.task_id,
                    "config_id": manual_task_instance.config_id,
                    "field_id": form_field.id,
                    "instance_id": manual_task_instance.id,
                    "submitted_by": 1,
                    "data": {},
                },
            )

    def test_submission_with_nonexistent_field(
        self, db: Session, manual_task_instance: ManualTaskInstance
    ):
        """Test that submissions must reference an existing field."""
        with pytest.raises(ValueError, match="No field found with ID"):
            ManualTaskSubmission.create_or_update(
                db=db,
                data={
                    "task_id": manual_task_instance.task_id,
                    "config_id": manual_task_instance.config_id,
                    "field_id": "nonexistent_field_id",
                    "instance_id": manual_task_instance.id,
                    "submitted_by": 1,
                    "data": {"test_field": "value"},
                },
            )
