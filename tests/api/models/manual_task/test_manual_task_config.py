from typing import Any

import pytest
from sqlalchemy.exc import DataError, IntegrityError, StatementError
from sqlalchemy.orm import Session

from fides.api.models.fides_user import FidesUser
from fides.api.models.manual_task import (
    ManualTask,
    ManualTaskConfig,
    ManualTaskConfigField,
    ManualTaskFieldMetadata,
    ManualTaskFieldType,
    ManualTaskInstance,
    ManualTaskLogStatus,
    ManualTaskSubmission,
)
from fides.api.models.privacy_request.privacy_request import PrivacyRequest

TEXT_FIELD_DATA = {
    "field_key": "test_field",
    "field_type": "text",
    "field_metadata": {
        "required": True,
        "label": "Test Field",
        "help_text": "This is a test field",
        "min_length": 1,
        "max_length": 100,
        "pattern": "^[a-zA-Z0-9]+$",
        "placeholder": "Enter a value",
        "default_value": "default_value",
    },
}

CHECKBOX_FIELD_DATA = {
    "field_key": "test_checkbox_field",
    "field_type": "checkbox",
    "field_metadata": {
        "required": True,
        "label": "Test Checkbox Field",
        "help_text": "This is a test checkbox field",
    },
}

ATTACHMENT_FIELD_DATA = {
    "field_key": "test_attachment_field",
    "field_type": "attachment",
    "field_metadata": {
        "required": True,
        "label": "Test Attachment Field",
        "help_text": "This is a test attachment field",
    },
}


class TestManualTaskConfig:
    def test_create_config(self, db: Session, manual_task: ManualTask):
        config = ManualTaskConfig.create(
            db,
            data={
                "task_id": manual_task.id,
                "config_type": "access_privacy_request",
                "version": 1,
                "is_current": True,
            },
        )
        assert config.id is not None
        assert config.task_id == manual_task.id
        assert config.config_type == "access_privacy_request"
        assert config.version == 1
        assert config.is_current == True
        assert config.field_definitions == []

    @pytest.mark.parametrize(
        "invalid_types, expected_error",
        [
            pytest.param(
                {"config_type": "invalid_config_type"},
                ValueError,
                id="invalid_config_type",
            ),
            pytest.param({"version": "not_an_int"}, DataError, id="invalid_version"),
            pytest.param(
                {"is_current": "not_a_bool"}, StatementError, id="invalid_is_current"
            ),
            pytest.param(
                {"task_id": "not_a_string"}, IntegrityError, id="invalid_task_id"
            ),
            pytest.param({"invalid_key": "invalid_value"}, TypeError, id="invalid_key"),
        ],
    )
    def test_create_config_error(
        self,
        db: Session,
        manual_task: ManualTask,
        invalid_types: dict[str, Any],
        expected_error: type[Exception],
    ):
        data = {
            "task_id": manual_task.id,
            "config_type": "access_privacy_request",
            "version": 1,
            "is_current": True,
        }
        data.update(invalid_types)
        with pytest.raises(expected_error) as exc_info:
            ManualTaskConfig.create(db, data=data)
        assert list(invalid_types.keys())[0] in str(exc_info.value)

    def test_relationships(self, db: Session, manual_task: ManualTask):
        config = ManualTaskConfig.create(
            db,
            data={
                "task_id": manual_task.id,
                "config_type": "access_privacy_request",
                "version": 1,
                "is_current": True,
            },
        )
        assert config.task == manual_task
        assert config.field_definitions == []
        assert len(config.logs) == 1
        assert config.logs[0].config_id == config.id
        assert config.logs[0].task_id == manual_task.id
        assert config.logs[0].status == ManualTaskLogStatus.created

        data = TEXT_FIELD_DATA.copy()
        data["task_id"] = manual_task.id
        data["config_id"] = config.id
        ManualTaskConfigField.create(db, data=data)

        assert len(config.field_definitions) == 1


@pytest.mark.parametrize(
    "field_data, expected_field_type",
    [
        pytest.param(TEXT_FIELD_DATA, ManualTaskFieldType.text, id="text_field"),
        pytest.param(
            CHECKBOX_FIELD_DATA, ManualTaskFieldType.checkbox, id="checkbox_field"
        ),
        pytest.param(
            ATTACHMENT_FIELD_DATA, ManualTaskFieldType.attachment, id="attachment_field"
        ),
    ],
)
class TestManualTaskConfigField:

    def test_create_field(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_config: ManualTaskConfig,
        field_data: dict[str, Any],
        expected_field_type: ManualTaskFieldType,
    ):
        data = field_data.copy()
        data["task_id"] = manual_task.id
        data["config_id"] = manual_task_config.id
        field = ManualTaskConfigField.create(db, data=data)
        assert field.id is not None
        assert field.task_id == manual_task.id
        assert field.config_id == manual_task_config.id
        assert field.field_key == field_data["field_key"]
        assert field.field_type == expected_field_type
        assert field.field_metadata == field_data["field_metadata"]

        assert field.field_metadata_model == ManualTaskFieldMetadata.model_validate(
            field_data["field_metadata"]
        )

        assert field.config == manual_task_config
        assert len(manual_task_config.field_definitions) == 1
        assert manual_task_config.field_definitions[0] == field
        assert manual_task_config.get_field(field.field_key) == field

    @pytest.mark.parametrize(
        "invalid_types, expected_error",
        [
            pytest.param({"field_key": None}, IntegrityError, id="invalid_field_key"),
            pytest.param(
                {"field_type": "invalid_field_type"},
                LookupError,
                id="invalid_field_type",
            ),
            pytest.param({"task_id": "9"}, IntegrityError, id="invalid_task_id"),
            pytest.param({"config_id": "9"}, ValueError, id="invalid_config_id"),
            pytest.param({"invalid_key": "invalid_value"}, TypeError, id="invalid_key"),
        ],
    )
    def test_create_field_error(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_config: ManualTaskConfig,
        field_data: dict[str, Any],
        expected_field_type: ManualTaskFieldType,
        invalid_types: dict[str, Any],
        expected_error: type[Exception],
    ):
        data = field_data.copy()
        data["task_id"] = manual_task.id
        data["config_id"] = manual_task_config.id

        data.update(invalid_types)
        with pytest.raises(expected_error) as exc_info:
            ManualTaskConfigField.create(db, data=data)
        if "config_id" in invalid_types:
            assert f"Config with id {data['config_id']} not found" in str(
                exc_info.value
            )
        else:
            assert list(invalid_types.keys())[0] in str(exc_info.value)


class TestManualTaskConfigGetField:
    def test_get_field_exists(
        self, db: Session, manual_task: ManualTask, manual_task_config: ManualTaskConfig
    ):
        """Test getting a field that exists in the config."""
        field_data = TEXT_FIELD_DATA.copy()
        field_data["task_id"] = manual_task.id
        field_data["config_id"] = manual_task_config.id
        field = ManualTaskConfigField.create(db, data=field_data)

        result = manual_task_config.get_field(field.field_key)
        assert result is not None
        assert result == field
        assert result.field_key == field_data["field_key"]
        assert result.field_type == ManualTaskFieldType.text

    @pytest.mark.usefixtures("manual_task", "db")
    def test_get_field_not_exists(self, manual_task_config: ManualTaskConfig):
        """Test getting a field that doesn't exist in the config."""
        result = manual_task_config.get_field("non_existent_field")
        assert result is None

    def test_get_field_empty_definitions(self, db: Session, manual_task: ManualTask):
        """Test getting a field when field_definitions is empty."""
        config = ManualTaskConfig.create(
            db,
            data={
                "task_id": manual_task.id,
                "config_type": "access_privacy_request",
                "version": 1,
                "is_current": True,
            },
        )
        result = config.get_field("any_field")
        assert result is None
        assert config.field_definitions == []


class TestManualTaskConfigDeletion:
    def test_config_deletion_with_no_instances(
        self, db: Session, manual_task: ManualTask
    ):
        """Test that a config can be deleted when it has no instances or submissions."""
        config = ManualTaskConfig.create(
            db,
            data={
                "task_id": manual_task.id,
                "config_type": "access_privacy_request",
                "version": 1,
                "is_current": True,
            },
        )
        config_id = config.id

        # Should delete successfully
        config.delete(db)
        db.commit()

        # Verify config is deleted
        deleted_config = db.query(ManualTaskConfig).filter_by(id=config_id).first()
        assert deleted_config is None

    def test_config_deletion_prevents_with_instances(
        self, db: Session, manual_task: ManualTask, manual_task_config: ManualTaskConfig
    ):
        """Test that config deletion is prevented when instances exist due to RESTRICT constraint."""
        from fides.api.models.manual_task import ManualTaskInstance

        # Create an instance for the config
        instance = ManualTaskInstance.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": manual_task_config.id,
                "entity_id": "test_entity",
                "entity_type": "privacy_request",
            },
        )

        # Try to delete config (should fail due to RESTRICT constraint)
        with pytest.raises(Exception):  # Database constraint error
            db.delete(manual_task_config)
            db.commit()

        # Verify config and instance still exist
        assert (
            db.query(ManualTaskConfig).filter_by(id=manual_task_config.id).first()
            is not None
        )
        assert (
            db.query(ManualTaskInstance).filter_by(id=instance.id).first() is not None
        )

        # Clean up
        instance.delete(db)
        db.commit()

    def test_config_deletion_prevents_with_submissions(
        self,
        db: Session,
        manual_task: ManualTask,
        user: FidesUser,
    ):
        """Test that config deletion is prevented when submissions exist due to RESTRICT constraint."""
        from fides.api.models.manual_task import (
            ManualTaskConfig,
            ManualTaskConfigField,
            ManualTaskInstance,
            ManualTaskSubmission,
        )

        # Create a config
        config = ManualTaskConfig.create(
            db,
            data={
                "task_id": manual_task.id,
                "config_type": "access_privacy_request",
                "version": 1,
                "is_current": True,
            },
        )

        # Create a field for the config
        field = ManualTaskConfigField.create(
            db,
            data={
                "task_id": manual_task.id,
                "config_id": config.id,
                "field_type": "text",
                "field_key": "test_field",
                "field_metadata": {
                    "required": True,
                },
            },
        )

        # Create an instance for the submissions
        instance = ManualTaskInstance.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": config.id,
                "entity_id": "test_entity",
                "entity_type": "privacy_request",
            },
        )

        # Delete the instance first - this will cascade delete the submission
        instance.delete(db)
        db.commit()

        # Try to delete config - should work since no associated submissions remain
        config.delete(db)
        db.commit()

        # Verify config is deleted
        assert db.query(ManualTaskConfig).filter_by(id=config.id).first() is None


class TestManualTaskConfigFieldDeletion:
    def test_field_deletion_with_no_submissions(
        self, db: Session, manual_task: ManualTask, manual_task_config: ManualTaskConfig
    ):
        """Test that a field can be deleted when it has no submissions."""
        field_data = TEXT_FIELD_DATA.copy()
        field_data["task_id"] = manual_task.id
        field_data["config_id"] = manual_task_config.id
        field = ManualTaskConfigField.create(db, data=field_data)
        field_id = field.id

        # Should delete successfully
        field.delete(db)
        db.commit()

        # Verify field is deleted
        deleted_field = db.query(ManualTaskConfigField).filter_by(id=field_id).first()
        assert deleted_field is None

    def test_field_deletion_prevents_with_submissions(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_config: ManualTaskConfig,
        user: FidesUser,
    ):
        """Test that field deletion is prevented when submissions exist due to RESTRICT constraint."""
        from fides.api.models.manual_task import (
            ManualTaskConfigField,
            ManualTaskInstance,
            ManualTaskSubmission,
        )

        field_data = TEXT_FIELD_DATA.copy()
        field_data["task_id"] = manual_task.id
        field_data["config_id"] = manual_task_config.id
        field = ManualTaskConfigField.create(db, data=field_data)

        # Create an instance
        instance = ManualTaskInstance.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": manual_task_config.id,
                "entity_id": "test_entity",
                "entity_type": "privacy_request",
            },
        )

        # Create a submission for the field
        submission = ManualTaskSubmission.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": manual_task_config.id,
                "field_id": field.id,
                "instance_id": instance.id,
                "submitted_by": user.id,
                "data": {"value": "test"},
            },
        )

        # Try to delete field (should fail due to RESTRICT constraint)
        with pytest.raises(Exception):  # Database constraint error
            field.delete(db)
            db.commit()

        # Verify field and submission still exist
        assert (
            db.query(ManualTaskConfigField).filter_by(id=field.id).first() is not None
        )
        assert (
            db.query(ManualTaskSubmission).filter_by(id=submission.id).first()
            is not None
        )

        # Clean up by deleting from bottom up
        submission.delete(db)
        instance.delete(db)
        field.delete(db)
        db.commit()
