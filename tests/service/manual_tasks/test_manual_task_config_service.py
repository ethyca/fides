import pytest
from sqlalchemy.orm import Session

from fides.api.models.manual_tasks.manual_task import ManualTask
from fides.api.models.manual_tasks.manual_task_config import ManualTaskConfig
from fides.api.models.manual_tasks.manual_task_log import (
    ManualTaskLog,
    ManualTaskLogStatus,
)
from fides.api.schemas.manual_tasks.manual_task_config import (
    ManualTaskFieldType,
)
from fides.service.manual_tasks.manual_task_config_service import (
    ManualTaskConfigService,
)
from tests.service.manual_tasks.conftest import CONFIG_TYPE, FIELDS


class TestManualTaskConfigServiceBase:
    """Base test class with common test data and utilities."""

    config_type = CONFIG_TYPE
    fields = FIELDS


class TestManualTaskConfigCreation(TestManualTaskConfigServiceBase):
    """Tests for creating new configurations."""

    def test_create_new_version_no_previous_config(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_config_service: ManualTaskConfigService,
    ):
        """Test creating a new version when there is no previous config."""
        # Execute
        config = manual_task_config_service.create_new_version(
            task=manual_task,
            config_type=self.config_type,
            field_updates=self.fields,
        )

        # Verify
        assert config is not None
        assert config.config_type == self.config_type
        assert config.version == 1
        assert config.is_current is True
        assert len(config.field_definitions) == len(self.fields)
        field1 = next(
            field for field in config.field_definitions if field.field_key == "field1"
        )
        field2 = next(
            field for field in config.field_definitions if field.field_key == "field2"
        )
        assert (
            field1.field_metadata["label"] == self.fields[0]["field_metadata"]["label"]
        )
        assert (
            field2.field_metadata["label"] == self.fields[1]["field_metadata"]["label"]
        )

        # Verify log was created
        log = (
            db.query(ManualTaskLog)
            .filter_by(task_id=manual_task.id)
            .order_by(ManualTaskLog.created_at.desc())
            .first()
        )
        assert log is not None
        assert log.status == ManualTaskLogStatus.created
        assert "Created new version 1 of configuration" in log.message
        assert log.config_id == config.id

    def test_create_new_version_with_previous_config(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_config_service: ManualTaskConfigService,
    ):
        """Test creating a new version when there is a previous config."""
        # Setup - create initial config
        initial_config = manual_task_config_service.create_new_version(
            task=manual_task,
            config_type=self.config_type,
            field_updates=self.fields,
        )

        # Execute - create new version with modified fields
        modified_fields = [
            {
                "field_key": "field1",
                "field_type": ManualTaskFieldType.text,
                "field_metadata": {
                    "label": "Field 1 Updated",
                    "required": True,
                    "help_text": "This is field 1 updated",
                },
            }
        ]
        new_config = manual_task_config_service.create_new_version(
            task=manual_task,
            config_type=self.config_type,
            field_updates=modified_fields,
            previous_config=db.query(ManualTaskConfig)
            .filter_by(id=initial_config.id)
            .first(),
        )

        # Verify
        assert new_config is not None
        assert new_config.config_type == self.config_type
        assert new_config.version == 2
        assert new_config.is_current is True

        # Verify previous config is no longer current
        previous_config = (
            db.query(ManualTaskConfig).filter_by(id=initial_config.id).first()
        )
        assert previous_config.is_current is False

        # Verify fields
        assert (
            len(new_config.field_definitions) == len(self.fields)
        )  # one original field, one modified field
        field1 = next(
            field
            for field in new_config.field_definitions
            if field.field_key == "field1"
        )
        assert field1.field_metadata["label"] == "Field 1 Updated"
        field2 = next(
            field
            for field in new_config.field_definitions
            if field.field_key == "field2"
        )
        assert field2.field_metadata["label"] == "Field 2"


class TestManualTaskConfigValidation(TestManualTaskConfigServiceBase):
    """Tests for configuration validation."""

    def test_invalid_config_type(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_config_service: ManualTaskConfigService,
    ):
        """Test creating a config with an invalid config type."""
        with pytest.raises(ValueError, match="Invalid config type: invalid_type"):
            manual_task_config_service.create_new_version(
                task=manual_task,
                config_type="invalid_type",
                field_updates=self.fields,
            )

    def test_invalid_field_type(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_config_service: ManualTaskConfigService,
    ):
        """Test creating a config with an invalid field type."""
        invalid_fields = [
            {
                "field_key": "field1",
                "field_type": "invalid_type",
                "field_metadata": {
                    "label": "Field 1",
                    "required": True,
                },
            }
        ]
        with pytest.raises(ValueError, match="Invalid field type: invalid_type"):
            manual_task_config_service.create_new_version(
                task=manual_task,
                config_type=self.config_type,
                field_updates=invalid_fields,
            )

    def test_invalid_field_metadata(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_config_service: ManualTaskConfigService,
    ):
        """Test creating a config with invalid field metadata."""
        invalid_fields = [
            {
                "field_key": "field1",
                "field_type": ManualTaskFieldType.text,
                "field_metadata": {
                    "invalid_key": "invalid_value",  # Missing required 'label'
                },
            }
        ]
        with pytest.raises(ValueError, match="Invalid field data"):
            manual_task_config_service.create_new_version(
                task=manual_task,
                config_type=self.config_type,
                field_updates=invalid_fields,
            )

    def test_empty_field_key(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_config_service: ManualTaskConfigService,
    ):
        """Test creating a config with empty field key."""
        invalid_fields = [
            {
                "field_key": "",  # Empty field key
                "field_type": ManualTaskFieldType.text,
                "field_metadata": {
                    "label": "Field 1",
                    "required": True,
                },
            }
        ]
        with pytest.raises(ValueError, match="Invalid field data"):
            manual_task_config_service.create_new_version(
                task=manual_task,
                config_type=self.config_type,
                field_updates=invalid_fields,
            )

    def test_duplicate_field_keys(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_config_service: ManualTaskConfigService,
    ):
        """Test that multiple updates to the same field are rejected."""
        duplicate_fields = [
            {
                "field_key": "field1",
                "field_type": ManualTaskFieldType.text,
                "field_metadata": {
                    "label": "Field 1",
                    "required": True,
                },
            },
            {
                "field_key": "field1",  # Duplicate field key
                "field_type": ManualTaskFieldType.text,
                "field_metadata": {
                    "label": "Field 1 Duplicate",
                    "required": False,
                },
            },
        ]
        with pytest.raises(
            ValueError,
            match="Duplicate field keys found in field updates, field keys must be unique.",
        ):
            manual_task_config_service.create_new_version(
                task=manual_task,
                config_type=self.config_type,
                field_updates=duplicate_fields,
            )


class TestManualTaskConfigRetrieval(TestManualTaskConfigServiceBase):
    """Tests for retrieving configurations."""

    def test_get_current_config(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_config_service: ManualTaskConfigService,
    ):
        """Test getting the current config."""
        # Setup - create config
        config = manual_task_config_service.create_new_version(
            task=manual_task,
            config_type=self.config_type,
            field_updates=self.fields,
        )

        # Execute
        current_config = manual_task_config_service.get_current_config(
            task=manual_task,
            config_type=self.config_type,
        )

        # Verify
        assert current_config is not None
        assert current_config.id == config.id
        assert current_config.version == 1
        assert current_config.is_current is True

    def test_get_config_by_id(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_config_service: ManualTaskConfigService,
    ):
        """Test getting a config by its ID."""
        # Setup - create config
        config = manual_task_config_service.create_new_version(
            task=manual_task,
            config_type=self.config_type,
            field_updates=self.fields,
        )

        # Execute
        found_config = manual_task_config_service.get_config(
            task=manual_task,
            config_type=self.config_type,
            field_id=None,
            config_id=config.id,
            field_key=None,
            version=None,
        )

        # Verify
        assert found_config is not None
        assert found_config.id == config.id
        assert found_config.version == 1
        assert found_config.is_current is True

    def test_get_config_by_version(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_config_service: ManualTaskConfigService,
    ):
        """Test getting a config by its version."""
        # Setup - create config
        config = manual_task_config_service.create_new_version(
            task=manual_task,
            config_type=self.config_type,
            field_updates=self.fields,
        )

        # Execute
        found_config = manual_task_config_service.get_config(
            task=manual_task,
            config_type=self.config_type,
            field_id=None,
            config_id=None,
            field_key=None,
            version=1,
        )

        # Verify
        assert found_config is not None
        assert found_config.id == config.id
        assert found_config.version == 1
        assert found_config.is_current is True

    def test_get_config_by_field_key(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_config_service: ManualTaskConfigService,
    ):
        """Test getting a config by field key."""
        # Setup - create config
        config = manual_task_config_service.create_new_version(
            task=manual_task,
            config_type=self.config_type,
            field_updates=self.fields,
        )

        # Execute
        found_config = manual_task_config_service.get_config(
            task=manual_task,
            config_type=self.config_type,
            field_id=None,
            config_id=None,
            field_key="field1",
            version=None,
        )

        # Verify
        assert found_config is not None
        assert found_config.id == config.id
        assert any(
            field.field_key == "field1" for field in found_config.field_definitions
        )

    def test_get_config_no_filters(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_config_service: ManualTaskConfigService,
    ):
        """Test getting a config with no filters."""
        config = manual_task_config_service.get_config(
            task=None,
            config_type=None,
            field_id=None,
            config_id=None,
            field_key=None,
            version=None,
        )
        assert config is None


class TestManualTaskConfigVersioning(TestManualTaskConfigServiceBase):
    """Tests for configuration versioning."""

    def test_multiple_versions_sequence(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_config_service: ManualTaskConfigService,
    ):
        """Test creating multiple versions in sequence."""
        # Create initial version
        version1 = manual_task_config_service.create_new_version(
            task=manual_task,
            config_type=self.config_type,
            field_updates=self.fields,
        )

        # Create second version
        version2 = manual_task_config_service.create_new_version(
            task=manual_task,
            config_type=self.config_type,
            field_updates=self.fields,
            previous_config=db.query(ManualTaskConfig)
            .filter_by(id=version1.id)
            .first(),
        )

        # Create third version
        version3 = manual_task_config_service.create_new_version(
            task=manual_task,
            config_type=self.config_type,
            field_updates=self.fields,
            previous_config=db.query(ManualTaskConfig)
            .filter_by(id=version2.id)
            .first(),
        )

        # Verify versions
        versions = manual_task_config_service.list_config_type_versions(
            task=manual_task,
            config_type=self.config_type,
        )
        assert len(versions) == 3
        assert versions[0].version == 3
        assert versions[1].version == 2
        assert versions[2].version == 1
        assert versions[0].is_current is True
        assert versions[1].is_current is False
        assert versions[2].is_current is False


class TestManualTaskConfigFieldUpdates(TestManualTaskConfigServiceBase):
    """Tests for field updates and modifications."""

    def test_update_field_type(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_config_service: ManualTaskConfigService,
    ):
        """Test updating a field's type."""
        # Create initial config with text field
        initial_config = manual_task_config_service.create_new_version(
            task=manual_task,
            config_type=self.config_type,
            field_updates=self.fields,
        )

        # Update field type to checkbox
        modified_fields = [
            {
                "field_key": "field1",
                "field_type": ManualTaskFieldType.checkbox,
                "field_metadata": {
                    "label": "Field 1",
                    "required": True,
                },
            }
        ]
        new_config = manual_task_config_service.create_new_version(
            task=manual_task,
            config_type=self.config_type,
            field_updates=modified_fields,
            previous_config=db.query(ManualTaskConfig)
            .filter_by(id=initial_config.id)
            .first(),
        )

        # Verify field type was updated
        field1 = next(
            field
            for field in new_config.field_definitions
            if field.field_key == "field1"
        )
        assert field1.field_type == ManualTaskFieldType.checkbox

    def test_update_field_metadata_empty(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_config_service: ManualTaskConfigService,
    ):
        """Test updating a field's metadata to empty."""
        # Create initial config
        initial_config = manual_task_config_service.create_new_version(
            task=manual_task,
            config_type=self.config_type,
            field_updates=self.fields,
        )

        # Update field metadata to empty
        modified_fields = [
            {
                "field_key": "field1",
                "field_type": ManualTaskFieldType.text,
                "field_metadata": {},  # Empty metadata
            }
        ]
        new_config = manual_task_config_service.create_new_version(
            task=manual_task,
            config_type=self.config_type,
            field_updates=modified_fields,
            previous_config=db.query(ManualTaskConfig)
            .filter_by(id=initial_config.id)
            .first(),
        )

        # Verify field was removed (empty metadata indicates removal)
        assert all(
            field.field_key != "field1" for field in new_config.field_definitions
        )

    def test_update_nonexistent_field(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_config_service: ManualTaskConfigService,
    ):
        """Test updating a field that doesn't exist."""
        # Create initial config
        initial_config = manual_task_config_service.create_new_version(
            task=manual_task,
            config_type=self.config_type,
            field_updates=self.fields,
        )

        # Try to update non-existent field
        modified_fields = [
            {
                "field_key": "nonexistent_field",
                "field_type": ManualTaskFieldType.text,
                "field_metadata": {
                    "label": "Nonexistent Field",
                    "required": True,
                },
            }
        ]
        new_config = manual_task_config_service.create_new_version(
            task=manual_task,
            config_type=self.config_type,
            field_updates=modified_fields,
            previous_config=db.query(ManualTaskConfig)
            .filter_by(id=initial_config.id)
            .first(),
        )

        # Verify original fields remain unchanged
        assert (
            len(new_config.field_definitions) == len(self.fields) + 1
        )  # one original fields, one new field
        field_keys = [field["field_key"] for field in self.fields]
        assert all(
            field.field_key in field_keys + ["nonexistent_field"]
            for field in new_config.field_definitions
        )


class TestManualTaskConfigFieldManagement(TestManualTaskConfigServiceBase):
    """Tests for field management operations."""

    def test_add_fields(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_config_service: ManualTaskConfigService,
    ):
        """Test adding fields to a configuration."""
        # Setup - create initial config
        initial_config = manual_task_config_service.create_new_version(
            task=manual_task,
            config_type=self.config_type,
            field_updates=self.fields,
        )

        # Execute - add new field
        new_field = {
            "field_key": "field3",
            "field_type": ManualTaskFieldType.text,
            "field_metadata": {
                "label": "Field 3",
                "required": False,
                "help_text": "This is field 3",
            },
        }
        manual_task_config_service.add_fields(
            manual_task, self.config_type, [new_field]
        )

        # Verify
        current_config = manual_task_config_service.get_current_config(
            manual_task, self.config_type
        )
        assert current_config is not None
        assert len(current_config.field_definitions) == len(self.fields) + 1
        field3 = next(
            field
            for field in current_config.field_definitions
            if field.field_key == "field3"
        )
        assert field3.field_metadata["label"] == "Field 3"

    def test_add_fields_no_current_config(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_config_service: ManualTaskConfigService,
    ):
        """Test adding fields when no current config exists."""
        new_field = {
            "field_key": "field1",
            "field_type": ManualTaskFieldType.text,
            "field_metadata": {
                "label": "Field 1",
                "required": True,
            },
        }
        with pytest.raises(
            ValueError,
            match=f"No current config found for task {manual_task.id} and type {self.config_type}",
        ):
            manual_task_config_service.add_fields(
                manual_task, self.config_type, [new_field]
            )

    def test_remove_fields(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_config_service: ManualTaskConfigService,
    ):
        """Test removing fields from a configuration."""
        # Setup - create initial config
        initial_config = manual_task_config_service.create_new_version(
            task=manual_task,
            config_type=self.config_type,
            field_updates=self.fields,
        )
        # Execute - remove field1
        manual_task_config_service.remove_fields(
            manual_task, self.config_type, ["field1"]
        )

        # Verify
        current_config = manual_task_config_service.get_current_config(
            manual_task, self.config_type
        )
        assert current_config is not None
        assert len(current_config.field_definitions) == len(self.fields) - 1
        assert all(
            field.field_key != "field1" for field in current_config.field_definitions
        )
        field2 = next(
            field
            for field in current_config.field_definitions
            if field.field_key == "field2"
        )
        assert field2.field_metadata["label"] == "Field 2"

    def test_remove_fields_no_current_config(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_config_service: ManualTaskConfigService,
    ):
        """Test removing fields when no current config exists."""
        with pytest.raises(
            ValueError,
            match=f"No current config found for task {manual_task.id} and type {self.config_type}",
        ):
            manual_task_config_service.remove_fields(
                manual_task, self.config_type, ["field1"]
            )


class TestManualTaskConfigDeletion(TestManualTaskConfigServiceBase):
    """Tests for configuration deletion."""

    def test_delete_config(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_config_service: ManualTaskConfigService,
    ):
        """Test deleting a configuration."""
        # Setup - create config
        response = manual_task_config_service.create_new_version(
            task=manual_task,
            config_type=self.config_type,
            field_updates=self.fields,
        )

        # Execute
        manual_task_config_service.delete_config(manual_task, response.id)

        # Verify
        assert db.query(ManualTaskConfig).filter_by(id=response.id).first() is None

    def test_delete_config_not_found(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_config_service: ManualTaskConfigService,
    ):
        """Test deleting a non-existent configuration."""
        with pytest.raises(ValueError, match="Config with ID invalid-id not found"):
            manual_task_config_service.delete_config(manual_task, "invalid-id")


class TestManualTaskConfigResponseConversion(TestManualTaskConfigServiceBase):
    """Tests for converting config models to response objects."""

    def test_to_response(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_config_service: ManualTaskConfigService,
    ):
        """Test converting a config model to a response object."""
        # Create a config
        config = manual_task_config_service.create_new_version(
            task=manual_task,
            config_type=self.config_type,
            field_updates=self.fields,
        )

        # Convert to response
        response = manual_task_config_service.to_response(config)

        # Verify response
        assert response is not None
        assert response.id == config.id
        assert response.task_id == config.task_id
        assert response.config_type == config.config_type
        assert response.version == config.version
        assert response.is_current == config.is_current
        assert len(response.fields) == len(self.fields)
        for field, expected_field in zip(response.fields, self.fields):
            assert field.field_key == expected_field["field_key"]
            assert field.field_type == expected_field["field_type"]
            assert (
                field.field_metadata.label == expected_field["field_metadata"]["label"]
            )
            assert (
                field.field_metadata.required
                == expected_field["field_metadata"]["required"]
            )
