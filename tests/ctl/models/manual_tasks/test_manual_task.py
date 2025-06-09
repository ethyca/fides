from datetime import datetime, timezone
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fides.api.models.manual_tasks.manual_task import ManualTask, ManualTaskReference
from fides.api.models.manual_tasks.manual_task_log import (
    ManualTaskLog,
    ManualTaskLogStatus,
)
from fides.api.schemas.manual_tasks.manual_task_schemas import (
    ManualTaskParentEntityType,
    ManualTaskReferenceType,
    ManualTaskType,
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
        due_date = datetime.now(timezone.utc)
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

    def test_create_task_creates_log(self, db: Session):
        """Test that task creation creates a log entry."""
        task = ManualTask.create(
            db=db,
            data={
                "task_type": ManualTaskType.privacy_request,
                "parent_entity_id": "test_connection",
                "parent_entity_type": "connection_config",
            },
        )

        # Verify log was created
        log = db.query(ManualTaskLog).filter_by(task_id=task.id).first()
        assert log is not None
        assert log.status == ManualTaskLogStatus.created
        assert "Created manual task" in log.message

    def test_unique_parent_entity_constraint(
        self, db: Session, manual_task: ManualTask
    ):
        """Test the unique constraint on parent entity."""
        # Setup - try to create another task with the same parent entity
        data = {
            "task_type": ManualTaskType.privacy_request,
            "parent_entity_id": manual_task.parent_entity_id,
            "parent_entity_type": manual_task.parent_entity_type,
        }

        # Execute and Verify
        with pytest.raises(IntegrityError) as exc_info:
            ManualTask.create(db=db, data=data)
        assert "uq_manual_task_parent_entity" in str(exc_info.value)

    def test_different_parent_entity_allowed(
        self, db: Session, manual_task: ManualTask
    ):
        """Test creating a task with a different parent entity."""
        # Setup - create a task with a different parent entity
        data = {
            "task_type": ManualTaskType.privacy_request,
            "parent_entity_id": "different_connection",
            "parent_entity_type": ManualTaskParentEntityType.connection_config,
        }

        # Execute
        task = ManualTask.create(db=db, data=data)

        # Verify
        assert task.parent_entity_id == "different_connection"
        assert task.parent_entity_type == ManualTaskParentEntityType.connection_config


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

    def test_assigned_users_property(self, db: Session, manual_task: ManualTask):
        """Test the assigned_users property."""
        # Create user references
        user_refs = [
            ManualTaskReference(
                task_id=manual_task.id,
                reference_id=f"user_{i}",
                reference_type=ManualTaskReferenceType.assigned_user,
            )
            for i in range(3)
        ]
        db.add_all(user_refs)
        db.commit()

        # Verify assigned_users property
        assert len(manual_task.assigned_users) == 3
        assert all(f"user_{i}" in manual_task.assigned_users for i in range(3))

    def test_reference_type_validation(self, db: Session, manual_task: ManualTask):
        """Test that reference types are properly validated."""
        # Test valid reference type
        ref = ManualTaskReference.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "reference_id": "test_ref",
                "reference_type": ManualTaskReferenceType.privacy_request,
            },
        )

        assert ref.reference_type == ManualTaskReferenceType.privacy_request
        ref.delete(db)

        # Test invalid reference type
        with pytest.raises(LookupError):
            ManualTaskReference.create(
                db=db,
                data={
                    "task_id": manual_task.id,
                    "reference_id": "test_ref",
                    "reference_type": "invalid_type",
                },
            )


class TestManualTaskRelationships:
    """Tests for task relationships with other models."""

    def test_task_logs_relationship(self, db: Session, manual_task: ManualTask):
        """Test relationship with task logs."""
        # Create a log
        log = ManualTaskLog(
            task_id=manual_task.id,
            status=ManualTaskLogStatus.complete,
            message="Test log",
        )
        db.add(log)
        db.commit()

        # Verify logs relationship
        assert len(manual_task.logs) == 2  # One from creation + one we just added
        assert any(l.message == "Test log" for l in manual_task.logs)
