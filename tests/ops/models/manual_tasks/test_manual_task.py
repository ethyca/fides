from datetime import datetime, timezone

import pytest
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
    ManualTaskFieldType,
    ManualTaskReferenceType,
    ManualTaskType,
)


@pytest.fixture
def manual_task_submission(
    db: Session,
    manual_task_instance: ManualTaskInstance,
    manual_task_form_field: ManualTaskConfigField,
) -> ManualTaskSubmission:
    """Create a test submission."""
    return ManualTaskSubmission.create_or_update(
        db=db,
        data={
            "task_id": manual_task_instance.task_id,
            "config_id": manual_task_instance.config_id,
            "field_id": manual_task_form_field.id,
            "instance_id": manual_task_instance.id,
            "submitted_by": 1,
            "data": {"test_form_field": "test value"},
        },
    )


class TestManualTaskCreation:
    """Tests for creating and managing manual tasks."""

    def test_create_task(self, db: Session):
        """Test creating a basic manual task."""
        task = ManualTask.create(
            db=db,
            data={
                "task_type": ManualTaskType.privacy_request,
                "parent_entity_id": "test_connection",
                "parent_entity_type": "connection_config",
            },
        )
        assert task.id is not None
        assert task.task_type == ManualTaskType.privacy_request
        assert task.parent_entity_id == "test_connection"
        assert task.parent_entity_type == "connection_config"

    def test_create_task_with_due_date(self, db: Session):
        """Test creating a task with a due date."""
        due_date = datetime.now(timezone.utc).replace(
            tzinfo=None
        )  # Convert to naive datetime
        task = ManualTask.create(
            db=db,
            data={
                "task_type": ManualTaskType.privacy_request,
                "parent_entity_id": "test_connection",
                "parent_entity_type": "connection_config",
                "due_date": due_date,
            },
        )
        assert task.due_date == due_date


class TestManualTaskReferences:
    """Tests for managing task references and relationships."""

    def test_task_references(self, db: Session, manual_task: ManualTask):
        """Test creating and managing task references."""
        # Create references
        ref1 = ManualTaskReference(
            task_id=manual_task.id,
            reference_id="ref1",
            reference_type=ManualTaskReferenceType.privacy_request,
        )
        ref2 = ManualTaskReference(
            task_id=manual_task.id,
            reference_id="ref2",
            reference_type=ManualTaskReferenceType.connection_config,
        )
        db.add_all([ref1, ref2])
        db.commit()

        # Verify references
        assert len(manual_task.references) == 2
        assert any(r.reference_id == "ref1" for r in manual_task.references)
        assert any(r.reference_id == "ref2" for r in manual_task.references)

    def test_task_reference_relationships(self, db: Session, manual_task: ManualTask):
        """Test relationships between tasks and references."""
        # Create a reference
        ref = ManualTaskReference(
            task_id=manual_task.id,
            reference_id="test_ref",
            reference_type=ManualTaskReferenceType.privacy_request,
        )
        db.add(ref)
        db.commit()

        # Verify bidirectional relationship
        assert ref.task == manual_task
        assert ref in manual_task.references

    def test_task_reference_deletion(self, db: Session, manual_task: ManualTask):
        """Test deleting task references."""
        # Create a reference
        ref = ManualTaskReference(
            task_id=manual_task.id,
            reference_id="test_ref",
            reference_type=ManualTaskReferenceType.privacy_request,
        )
        db.add(ref)
        db.commit()

        # Delete the reference
        db.delete(ref)
        db.commit()

        # Verify reference is gone
        assert len(manual_task.references) == 0
        assert db.query(ManualTaskReference).filter_by(id=ref.id).first() is None


class TestManualTaskUserManagement:
    """Tests for managing user assignments."""

    def test_assign_user(self, db: Session, manual_task: ManualTask):
        """Test assigning a user to a task."""
        manual_task.assign_user(db, "test_user")
        assert manual_task.assigned_users == ["test_user"]

    def test_unassign_user(self, db: Session, manual_task: ManualTask):
        """Test unassigning a user from a task."""
        manual_task.assign_user(db, "test_user")
        assert manual_task.assigned_users == ["test_user"]
        manual_task.unassign_user(db)
        assert manual_task.assigned_users == []

    def test_assign_user_error_handling(self, db: Session, manual_task: ManualTask):
        """Test error handling when assigning invalid user."""
        # Test with None user_id
        with pytest.raises(ValueError, match="User ID is required for assignment"):
            manual_task.assign_user(db, None)

        # Test with empty user_id
        with pytest.raises(ValueError, match="User ID is required for assignment"):
            manual_task.assign_user(db, "")


class TestManualTaskInstanceManagement:
    """Tests for managing task instances."""

    def test_create_entity_instance(
        self, db: Session, manual_task: ManualTask, manual_task_config: ManualTaskConfig
    ):
        """Test creating a new task instance for an entity."""
        instance = manual_task.create_entity_instance(
            db=db,
            config_id=manual_task_config.id,
            entity_id="test_entity",
            entity_type="test_type",
        )
        assert instance.id is not None
        assert instance.task_id == manual_task.id
        assert instance.config_id == manual_task_config.id
        assert instance.entity_id == "test_entity"
        assert instance.entity_type == "test_type"
        assert instance.status == StatusType.pending

        # Verify reference was created
        ref = (
            db.query(ManualTaskReference)
            .filter(
                ManualTaskReference.task_id == manual_task.id,
                ManualTaskReference.reference_id == "test_entity",
                ManualTaskReference.reference_type == "test_type",
            )
            .first()
        )
        assert ref is not None

        # Verify log was created
        log = (
            db.query(ManualTaskLog)
            .filter(
                ManualTaskLog.task_id == manual_task.id,
                ManualTaskLog.instance_id == instance.id,
            )
            .first()
        )
        assert log is not None
        assert log.status == ManualTaskLogStatus.complete

    def test_get_entity_instances(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_instance: ManualTaskInstance,
    ):
        """Test retrieving instances for a specific entity type."""
        instances = manual_task.get_entity_instances("privacy_request")
        assert len(instances) == 1
        assert instances[0].id == manual_task_instance.id

    def test_get_entity_instances_with_multiple_types(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_config: ManualTaskConfig,
    ):
        """Test retrieving instances when there are multiple entity types."""
        # Create instances for different entity types
        instance1 = manual_task.create_entity_instance(
            db=db,
            config_id=manual_task_config.id,
            entity_id="test_entity_1",
            entity_type="type_1",
        )
        instance2 = manual_task.create_entity_instance(
            db=db,
            config_id=manual_task_config.id,
            entity_id="test_entity_2",
            entity_type="type_2",
        )

        # Test getting instances for type_1
        type1_instances = manual_task.get_entity_instances("type_1")
        assert len(type1_instances) == 1
        assert type1_instances[0].id == instance1.id

        # Test getting instances for type_2
        type2_instances = manual_task.get_entity_instances("type_2")
        assert len(type2_instances) == 1
        assert type2_instances[0].id == instance2.id

    def test_get_entity_instances_with_empty_task(
        self,
        db: Session,
        manual_task: ManualTask,
    ):
        """Test retrieving instances from a task with no instances."""
        instances = manual_task.get_entity_instances("any_type")
        assert len(instances) == 0
        assert isinstance(instances, list)

    def test_get_instance_for_entity(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_instance: ManualTaskInstance,
    ):
        """Test retrieving a specific instance for an entity."""
        instance = manual_task.get_instance_for_entity(
            "test_privacy_request", "privacy_request"
        )
        assert instance is not None
        assert instance.id == manual_task_instance.id


class TestManualTaskInstance:
    """Tests for manual task instance functionality."""

    def test_get_attachments(
        self, db: Session, manual_task_instance: ManualTaskInstance
    ):
        """Test getting attachments for an instance."""
        # Create a submission with an attachment
        field = ManualTaskConfigField.create(
            db=db,
            data={
                "task_id": manual_task_instance.task_id,
                "config_id": manual_task_instance.config_id,
                "field_key": "test_attachment",
                "field_type": ManualTaskFieldType.attachment,
                "field_metadata": {
                    "label": "Test Attachment",
                    "required": True,
                    "help_text": "Test attachment field",
                    "file_types": ["pdf"],
                    "max_file_size": 1048576,
                    "multiple": True,
                    "max_files": 2,
                    "require_attachment_id": True,
                },
            },
        )

        # Add field to config
        config = manual_task_instance.config
        config.field_definitions.append(field)
        db.commit()

        # Create a submission with attachment references
        submission = ManualTaskSubmission.create_or_update(
            db=db,
            data={
                "task_id": manual_task_instance.task_id,
                "config_id": manual_task_instance.config_id,
                "field_id": field.id,
                "instance_id": manual_task_instance.id,
                "submitted_by": 1,
                "data": {
                    "test_attachment": {
                        "filename": "test.pdf",
                        "size": 1024,
                        "attachment_ids": ["test_attachment_1", "test_attachment_2"],
                    }
                },
            },
        )

        # Get attachments
        attachments = manual_task_instance.get_attachments(db)
        assert isinstance(attachments, list)

    def test_update_status_with_same_status(
        self, db: Session, manual_task_instance: ManualTaskInstance
    ):
        """Test updating status to the same status."""
        # Get initial log count
        initial_logs = (
            db.query(ManualTaskLog)
            .filter(
                ManualTaskLog.task_id == manual_task_instance.task_id,
                ManualTaskLog.instance_id == manual_task_instance.id,
            )
            .all()
        )
        initial_log_count = len(initial_logs)

        # Update to in_progress
        manual_task_instance.update_status(db, StatusType.in_progress)
        assert manual_task_instance.status == StatusType.in_progress

        # Try to update to the same status - should raise ValueError
        with pytest.raises(
            ValueError, match="Invalid status transition: already in status in_progress"
        ):
            manual_task_instance.update_status(db, StatusType.in_progress)

        # Verify no additional log was created
        logs = (
            db.query(ManualTaskLog)
            .filter(
                ManualTaskLog.task_id == manual_task_instance.task_id,
                ManualTaskLog.instance_id == manual_task_instance.id,
            )
            .all()
        )
        assert (
            len(logs) == initial_log_count + 1
        )  # Initial logs + one status change log

    def test_get_attachments_with_invalid_instance(
        self, db: Session, manual_task_instance: ManualTaskInstance
    ):
        """Test getting attachments for an invalid instance."""
        # Create an instance that's not in the database
        invalid_instance = ManualTaskInstance(
            id="invalid",
            task_id=manual_task_instance.task_id,
            config_id=manual_task_instance.config_id,
            entity_id="test",
            entity_type="test",
        )
        attachments = invalid_instance.get_attachments(db)
        assert len(attachments) == 0


class TestManualTaskErrorHandling:
    """Test error handling in manual task operations."""

    def test_create_entity_instance_with_invalid_config(
        self, db: Session, manual_task: ManualTask
    ):
        """Test creating an instance with an invalid config ID."""
        with pytest.raises(ValueError, match="Configuration not found"):
            manual_task.create_entity_instance(
                db=db,
                config_id="invalid_config_id",
                entity_id="test_entity",
                entity_type="test_type",
            )

    def test_create_entity_instance_with_existing_reference(
        self, db: Session, manual_task: ManualTask, manual_task_config: ManualTaskConfig
    ):
        """Test creating an instance when a reference already exists."""
        # Create first instance
        instance1 = manual_task.create_entity_instance(
            db=db,
            config_id=manual_task_config.id,
            entity_id="test_entity",
            entity_type="test_type",
        )

        # Try to create another instance for the same entity
        with pytest.raises(ValueError, match="Instance already exists for this entity"):
            manual_task.create_entity_instance(
                db=db,
                config_id=manual_task_config.id,
                entity_id="test_entity",
                entity_type="test_type",
            )

    def test_get_instance_for_nonexistent_entity(
        self, db: Session, manual_task: ManualTask
    ):
        """Test getting an instance for a non-existent entity."""
        instance = manual_task.get_instance_for_entity(
            "nonexistent_entity", "test_type"
        )
        assert instance is None

    def test_get_entity_instances_with_no_instances(
        self, db: Session, manual_task: ManualTask
    ):
        """Test getting instances for an entity type with no instances."""
        instances = manual_task.get_entity_instances("nonexistent_type")
        assert len(instances) == 0

    def test_assign_user_with_invalid_user(self, db: Session, manual_task: ManualTask):
        """Test assigning an invalid user to a task."""
        with pytest.raises(ValueError, match="User ID is required for assignment"):
            manual_task.assign_user(db, None)

        with pytest.raises(ValueError, match="User ID is required for assignment"):
            manual_task.assign_user(db, "")

    def test_unassign_user_with_no_assignment(
        self, db: Session, manual_task: ManualTask
    ):
        """Test unassigning a user when no user is assigned."""
        manual_task.unassign_user(db)  # Should not raise an error
        assert manual_task.assigned_users == []

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

    def test_update_status_from_submissions_with_invalid_data(
        self, db: Session, manual_task_instance: ManualTaskInstance
    ):
        """Test updating status from submissions with invalid data."""
        # Create a required field
        field = ManualTaskConfigField.create(
            db=db,
            data={
                "task_id": manual_task_instance.task_id,
                "config_id": manual_task_instance.config_id,
                "field_key": "test_field",
                "field_type": ManualTaskFieldType.form,
                "field_metadata": {
                    "label": "Test Field",
                    "required": True,
                    "help_text": "This is a test field",
                },
            },
        )

        # Add field to config
        config = manual_task_instance.config
        config.field_definitions.append(field)
        db.commit()

        # Create a submission with invalid data - wrong field key
        with pytest.raises(ValueError, match="Data must be for field test_field"):
            ManualTaskSubmission.create_or_update(
                db=db,
                data={
                    "task_id": manual_task_instance.task_id,
                    "config_id": manual_task_instance.config_id,
                    "field_id": field.id,
                    "instance_id": manual_task_instance.id,
                    "submitted_by": 1,
                    "data": {"wrong_field": "test value"},
                },
            )

        # Create a submission with invalid data - multiple fields
        with pytest.raises(
            ValueError, match="Submission must contain data for exactly one field"
        ):
            ManualTaskSubmission.create_or_update(
                db=db,
                data={
                    "task_id": manual_task_instance.task_id,
                    "config_id": manual_task_instance.config_id,
                    "field_id": field.id,
                    "instance_id": manual_task_instance.id,
                    "submitted_by": 1,
                    "data": {"test_field": "value1", "another_field": "value2"},
                },
            )

        # Status should remain pending since no valid submission was created
        assert manual_task_instance.status == StatusType.pending
