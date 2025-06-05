import pytest
from sqlalchemy.orm import Session

from fides.api.models.manual_tasks.manual_task import (
    ManualTask,
    ManualTaskConfig,
    ManualTaskConfigField,
    ManualTaskInstance,
    ManualTaskSubmission,
)
from fides.api.models.manual_tasks.status import StatusType
from fides.api.schemas.manual_tasks.manual_task_schemas import (
    ManualTaskConfigurationType,
    ManualTaskFieldType,
    ManualTaskType,
)


class TestStatusTransitions:
    """Tests for status transitions in manual tasks."""

    def test_valid_status_transitions(
        self, db: Session, manual_task: ManualTask, manual_task_config: ManualTaskConfig
    ):
        """Test that status transitions follow the expected rules."""
        # Create an instance using the fixtures
        instance = manual_task.create_entity_instance(
            db=db,
            config_id=manual_task_config.id,
            entity_id="test_entity",
            entity_type="test_type",
        )

        # Test valid transitions
        # pending -> in_progress
        instance.update_status(db, StatusType.in_progress)
        assert instance.status == StatusType.in_progress

        # in_progress -> completed
        instance.update_status(db, StatusType.completed)
        assert instance.status == StatusType.completed

        # Test invalid transitions
        # completed -> completed (should fail)
        with pytest.raises(ValueError, match="Invalid status transition"):
            instance.update_status(db, StatusType.completed)

        # completed -> pending (should fail)
        with pytest.raises(ValueError, match="Invalid status transition"):
            instance.update_status(db, StatusType.pending)

    def test_status_transition_with_submissions(
        self, db: Session, manual_task_instance: ManualTaskInstance
    ):
        """Test status transitions based on submission states with a single field."""
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

        # Initial status should be pending
        assert manual_task_instance.status == StatusType.pending

        # Create a submission
        submission = ManualTaskSubmission.create_or_update(
            db=db,
            data={
                "task_id": manual_task_instance.task_id,
                "config_id": manual_task_instance.config_id,
                "field_id": field.id,
                "instance_id": manual_task_instance.id,
                "submitted_by": 1,
                "data": {"test_field": "test value"},
            },
        )

        # Complete the submission
        submission.complete(db, "test_user")

        # Status should be completed
        assert manual_task_instance.status == StatusType.completed

    def test_status_transition_with_multiple_submissions(
        self, db: Session, manual_task_instance: ManualTaskInstance
    ):
        """Test status transitions with multiple fields."""
        # Create two required fields
        field1 = ManualTaskConfigField.create(
            db=db,
            data={
                "task_id": manual_task_instance.task_id,
                "config_id": manual_task_instance.config_id,
                "field_key": "test_field1",
                "field_type": ManualTaskFieldType.form,
                "field_metadata": {
                    "label": "Test Field 1",
                    "required": True,
                    "help_text": "This is test field 1",
                },
            },
        )

        field2 = ManualTaskConfigField.create(
            db=db,
            data={
                "task_id": manual_task_instance.task_id,
                "config_id": manual_task_instance.config_id,
                "field_key": "test_field2",
                "field_type": ManualTaskFieldType.form,
                "field_metadata": {
                    "label": "Test Field 2",
                    "required": True,
                    "help_text": "This is test field 2",
                },
            },
        )

        # Add fields to config
        config = manual_task_instance.config
        config.field_definitions.extend([field1, field2])
        db.commit()

        # Initial status should be pending
        assert manual_task_instance.status == StatusType.pending

        # Create first submission for field1 only
        submission1 = ManualTaskSubmission.create_or_update(
            db=db,
            data={
                "task_id": manual_task_instance.task_id,
                "config_id": manual_task_instance.config_id,
                "field_id": field1.id,
                "instance_id": manual_task_instance.id,
                "submitted_by": 1,
                "data": {"test_field1": "test value 1"},
            },
        )

        # Status should be in_progress
        assert manual_task_instance.status == StatusType.in_progress

        # Create second submission for field2 only
        submission2 = ManualTaskSubmission.create_or_update(
            db=db,
            data={
                "task_id": manual_task_instance.task_id,
                "config_id": manual_task_instance.config_id,
                "field_id": field2.id,
                "instance_id": manual_task_instance.id,
                "submitted_by": 1,
                "data": {"test_field2": "updated value 2"},
            },
        )

        # Complete both submissions
        submission1.complete(db, "test_user")
        submission2.complete(db, "test_user")

        # Status should be completed
        assert manual_task_instance.status == StatusType.completed

    def test_invalid_status_transitions(
        self, db: Session, manual_task_instance: ManualTaskInstance
    ):
        """Test invalid status transitions."""
        # Test invalid status type
        with pytest.raises(
            ValueError, match="Invalid status transition from pending to invalid_status"
        ):
            manual_task_instance.update_status(db, "invalid_status")

        # Test direct transition from pending to completed
        with pytest.raises(
            ValueError, match="Invalid status transition from pending to completed"
        ):
            manual_task_instance.update_status(db, StatusType.completed)

        # Test transition from completed to in_progress
        manual_task_instance.update_status(db, StatusType.in_progress)
        manual_task_instance.update_status(db, StatusType.completed)
        with pytest.raises(
            ValueError, match="Invalid status transition from completed to in_progress"
        ):
            manual_task_instance.update_status(db, StatusType.in_progress)

    def test_status_transition_with_user(
        self, db: Session, manual_task_instance: ManualTaskInstance
    ):
        """Test status transitions with user information."""
        # Test status transition with user
        manual_task_instance.update_status(
            db, StatusType.in_progress, user_id="test_user"
        )
        assert manual_task_instance.status == StatusType.in_progress
        assert manual_task_instance.completed_by_id is None

        # Test completion with user
        manual_task_instance.update_status(
            db, StatusType.completed, user_id="test_user"
        )
        assert manual_task_instance.status == StatusType.completed
        assert manual_task_instance.completed_by_id == "test_user"
        assert manual_task_instance.completed_at is not None

    def test_status_transition_without_user(
        self, db: Session, manual_task_instance: ManualTaskInstance
    ):
        """Test status transitions without user information."""
        # Test status transition without user
        manual_task_instance.update_status(db, StatusType.in_progress)
        assert manual_task_instance.status == StatusType.in_progress
        assert manual_task_instance.completed_by_id is None

        # Test completion without user
        manual_task_instance.update_status(db, StatusType.completed)
        assert manual_task_instance.status == StatusType.completed
        assert manual_task_instance.completed_by_id is None
        assert manual_task_instance.completed_at is not None
