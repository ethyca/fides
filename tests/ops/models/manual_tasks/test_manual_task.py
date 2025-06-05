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


class TestManualTaskUserManagement:
    """Tests for managing user assignments."""

    def test_assign_user(self, db: Session, manual_task: ManualTask):
        """Test assigning a user to a task."""
        manual_task.assign_user(db, "test_user")
        assert manual_task.get_assigned_user() == "test_user"

    def test_unassign_user(self, db: Session, manual_task: ManualTask):
        """Test unassigning a user from a task."""
        manual_task.assign_user(db, "test_user")
        assert manual_task.get_assigned_user() == "test_user"
        manual_task.unassign_user(db)
        assert manual_task.get_assigned_user() is None

    def test_assign_user_error_handling(self, db: Session, manual_task: ManualTask):
        """Test error handling when assigning invalid user."""
        # Test with None user_id
        with pytest.raises(ValueError, match="User ID is required for assignment"):
            manual_task.assign_user(db, None)

        # Test with empty user_id
        with pytest.raises(ValueError, match="User ID is required for assignment"):
            manual_task.assign_user(db, "")

    def test_complete_submission_error_handling(
        self, db: Session, manual_task_submission: ManualTaskSubmission
    ):
        """Test error handling when completing submission with invalid user."""
        # Test with None user_id
        with pytest.raises(ValueError, match="User ID is required for completion"):
            manual_task_submission.complete(db, None)

        # Test with empty user_id
        with pytest.raises(ValueError, match="User ID is required for completion"):
            manual_task_submission.complete(db, "")


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


class TestManualTaskSubmission:
    """Tests for manual task submissions."""

    def test_create_submission_with_invalid_data(
        self, db: Session, manual_task_instance: ManualTaskInstance
    ):
        """Test creating submissions with invalid data."""
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
                    "help_text": "This is a test form field",
                },
            },
        )

        # Add field to config
        config = manual_task_instance.config
        config.field_definitions.append(form_field)
        db.commit()

        # Test with missing required field
        with pytest.raises(ValueError, match="Invalid submission data"):
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

        # Test with invalid type
        with pytest.raises(ValueError, match="Invalid submission data"):
            ManualTaskSubmission.create_or_update(
                db=db,
                data={
                    "task_id": manual_task_instance.task_id,
                    "config_id": manual_task_instance.config_id,
                    "field_id": form_field.id,
                    "instance_id": manual_task_instance.id,
                    "submitted_by": 1,
                    "data": {"test_form_field": 123},
                },
            )

    def test_complete_submission(
        self,
        db: Session,
        manual_task_submission: ManualTaskSubmission,
    ):
        """Test completing a submission."""
        # Complete the submission
        manual_task_submission.complete(db, "test_user")

        # Verify completion
        assert manual_task_submission.status == StatusType.completed
        assert manual_task_submission.completed_at is not None
        assert manual_task_submission.completed_by_id is not None

        # Verify log was created
        log = (
            db.query(ManualTaskLog)
            .filter(
                ManualTaskLog.task_id == manual_task_submission.task_id,
                ManualTaskLog.instance_id == manual_task_submission.instance_id,
                ManualTaskLog.message.like("Completed submission%"),
            )
            .first()
        )
        assert log is not None
        assert log.status == ManualTaskLogStatus.complete

    def test_complete_submission_error_handling(
        self, db: Session, manual_task_submission: ManualTaskSubmission
    ):
        """Test error handling when completing submission with invalid user."""
        # Test with None user_id
        with pytest.raises(ValueError, match="User ID is required for completion"):
            manual_task_submission.complete(db, None)

        # Test with empty user_id
        with pytest.raises(ValueError, match="User ID is required for completion"):
            manual_task_submission.complete(db, "")


class TestManualTaskInstance:
    """Tests for manual task instance logging functionality."""

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
        submission = ManualTaskSubmission.create_or_update(
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
        # Complete the submission
        submission.complete(db, "test_user")

        # Get incomplete fields again
        incomplete_fields = manual_task_instance.get_incomplete_fields()
        assert len(incomplete_fields) == 0  # No incomplete fields now


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

    def test_create_manual_task_config_with_invalid_fields(
        self, db: Session, manual_task: ManualTask
    ):
        """Test creating a config with invalid field definitions."""
        with pytest.raises(ValueError, match="Invalid field type"):
            manual_task.create_manual_task_config(
                db=db,
                config_type="test_type",
                fields=[
                    {
                        "field_key": "test_field",
                        "field_type": "invalid_type",
                        "field_metadata": {
                            "label": "Test Field",
                            "required": True,
                        },
                    }
                ],
            )

    def test_assign_user_with_invalid_user(
        self, db: Session, manual_task: ManualTask
    ):
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
        assert manual_task.get_assigned_user() is None

    def test_create_submission_with_invalid_field(
        self, db: Session, manual_task_instance: ManualTaskInstance
    ):
        """Test creating a submission with an invalid field ID."""
        with pytest.raises(ValueError, match="Field not found"):
            ManualTaskSubmission.create_or_update(
                db=db,
                data={
                    "task_id": manual_task_instance.task_id,
                    "config_id": manual_task_instance.config_id,
                    "field_id": "invalid_field_id",
                    "instance_id": manual_task_instance.id,
                    "submitted_by": 1,
                    "data": {"test_field": "test value"},
                },
            )

    def test_complete_submission_with_invalid_user(
        self, db: Session, manual_task_submission: ManualTaskSubmission
    ):
        """Test completing a submission with an invalid user ID."""
        with pytest.raises(ValueError, match="User ID is required for completion"):
            manual_task_submission.complete(db, None)

        with pytest.raises(ValueError, match="User ID is required for completion"):
            manual_task_submission.complete(db, "")

    def test_complete_already_completed_submission(
        self, db: Session, manual_task_submission: ManualTaskSubmission
    ):
        """Test completing a submission that is already completed."""
        # Complete the submission first
        manual_task_submission.complete(db, "test_user")
        assert manual_task_submission.status == StatusType.completed

        # Try to complete it again
        manual_task_submission.complete(db, "test_user")
        assert manual_task_submission.status == StatusType.completed

        # Verify log was created for the second attempt
        log = (
            db.query(ManualTaskLog)
            .filter(
                ManualTaskLog.task_id == manual_task_submission.task_id,
                ManualTaskLog.instance_id == manual_task_submission.instance_id,
                ManualTaskLog.message.like("Submission for field%already completed%"),
            )
            .first()
        )
        assert log is not None
        assert log.status == ManualTaskLogStatus.awaiting_input

    def test_update_status_with_same_status(
        self, db: Session, manual_task_instance: ManualTaskInstance
    ):
        """Test updating status to the same status."""
        # Update to in_progress
        manual_task_instance.update_status(db, StatusType.in_progress)
        assert manual_task_instance.status == StatusType.in_progress

        # Update to the same status
        manual_task_instance.update_status(db, StatusType.in_progress)
        assert manual_task_instance.status == StatusType.in_progress

        # Verify no additional log was created
        logs = (
            db.query(ManualTaskLog)
            .filter(
                ManualTaskLog.task_id == manual_task_instance.task_id,
                ManualTaskLog.instance_id == manual_task_instance.id,
            )
            .all()
        )
        assert len(logs) == 1  # Only the initial creation log

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

        # Create a submission with invalid data
        submission = ManualTaskSubmission.create_or_update(
            db=db,
            data={
                "task_id": manual_task_instance.task_id,
                "config_id": manual_task_instance.config_id,
                "field_id": field.id,
                "instance_id": manual_task_instance.id,
                "submitted_by": 1,
                "data": {"test_field": 123},  # Invalid type
            },
        )

        # Update status
        manual_task_instance.update_status_from_submissions(db)
        assert manual_task_instance.status == StatusType.in_progress  # Should not be completed due to invalid data
