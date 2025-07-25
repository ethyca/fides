from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.manual_task import (
    ManualTask,
    ManualTaskLog,
    ManualTaskLogStatus,
    ManualTaskParentEntityType,
    ManualTaskReference,
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
        ref = ManualTaskReference.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "reference_id": "test_ref",
                "reference_type": ManualTaskReferenceType.privacy_request,
            },
        )

        # Verify bidirectional relationship
        assert ref.task == manual_task
        assert ref in manual_task.references

    def test_task_reference_deletion(self, db: Session, manual_task: ManualTask):
        """Test deleting task references."""
        # Create a reference
        ref = ManualTaskReference.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "reference_id": "test_ref",
                "reference_type": ManualTaskReferenceType.privacy_request,
            },
        )

        # Delete the reference
        ref.delete(db)

        # Verify reference is gone
        assert len(manual_task.references) == 0
        assert db.query(ManualTaskReference).filter_by(id=ref.id).first() is None

    def test_assigned_users_property(self, db: Session, manual_task: ManualTask):
        """Test the assigned_users property."""
        # Create user references
        user_refs = [
            ManualTaskReference.create(
                db=db,
                data={
                    "task_id": manual_task.id,
                    "reference_id": f"user_{i}",
                    "reference_type": ManualTaskReferenceType.assigned_user,
                },
            )
            for i in range(3)
        ]

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

        # Test enum validation
        with pytest.raises(ValueError) as exc_info:
            ManualTaskReferenceType("invalid_type")
        assert "invalid_type" in str(exc_info)

        # Test database-level validation
        with pytest.raises(LookupError) as exc_info:
            ManualTaskReference.create(
                db=db,
                data={
                    "task_id": manual_task.id,
                    "reference_id": "test_ref",
                    "reference_type": "invalid_type",
                },
            )
        assert "invalid_type" in str(exc_info)


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

    def test_task_parent_entity_relationship(
        self, db: Session, manual_task: ManualTask
    ):
        """Test task parent entity relationship"""

        connection_config = ConnectionConfig.create(
            db=db,
            data={
                "name": str(uuid4()),
                "key": "connection_config_data_use_map_no_system",
                "connection_type": ConnectionType.manual_task,
                "access": AccessLevel.write,
                "disabled": False,
            },
        )
        manual_task = ManualTask.create(
            db=db,
            data={
                "task_type": ManualTaskType.privacy_request,
                "parent_entity_id": connection_config.id,
                "parent_entity_type": ManualTaskParentEntityType.connection_config,
            },
        )

        assert manual_task.parent_entity_id == connection_config.id
        assert connection_config.manual_task == manual_task
