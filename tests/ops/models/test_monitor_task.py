import pytest
from sqlalchemy.orm import Session

from fides.api.models.monitor_task import MonitorTask, MonitorTaskType
from fides.api.models.worker_task import ExecutionLogStatus


class TestMonitorTask:
    def test_create_monitor_task(self, db: Session, monitor_config) -> None:
        """Test creating a monitor task with valid data."""
        task = MonitorTask.create(
            db=db,
            data={
                "celery_id": "test-celery-id",
                "action_type": MonitorTaskType.DETECTION.value,
                "status": ExecutionLogStatus.pending.value,
                "message": "Test message",
                "monitor_config_id": monitor_config.id,
                "staged_resource_urn": "test-urn",
                "child_resource_urns": ["child-urn-1", "child-urn-2"],
                "task_arguments": {"arg1": "value1"},
            },
        )

        assert task.celery_id == "test-celery-id"
        assert task.action_type == MonitorTaskType.DETECTION.value
        assert task.status.value == ExecutionLogStatus.pending.value
        assert task.message == "Test message"
        assert task.monitor_config_id == monitor_config.id
        assert task.staged_resource_urn == "test-urn"
        assert task.child_resource_urns == ["child-urn-1", "child-urn-2"]
        assert task.task_arguments == {"arg1": "value1"}
        assert task.created_at is not None
        assert task.updated_at is not None

        # Clean up the task
        db.delete(task)
        db.commit()

    def test_create_monitor_task_defaults(self, db: Session, monitor_config) -> None:
        """Test creating a monitor task with minimal required fields and verify default values."""
        task = MonitorTask.create(
            db=db,
            data={
                "celery_id": "test-celery-id",
                "action_type": MonitorTaskType.CLASSIFICATION.value,
                "status": ExecutionLogStatus.in_processing.value,
                "monitor_config_id": monitor_config.id,
                "staged_resource_urn": "test-urn",
            },
        )

        # Required fields should be set
        assert task.celery_id == "test-celery-id"
        assert task.action_type == MonitorTaskType.CLASSIFICATION.value
        assert task.status.value == ExecutionLogStatus.in_processing.value
        assert task.monitor_config_id == monitor_config.id
        assert task.staged_resource_urn == "test-urn"

        # Optional fields should have default values
        assert task.message is None
        assert task.child_resource_urns is None
        assert task.task_arguments is None
        assert task.created_at is not None
        assert task.updated_at is not None

        # Clean up the task
        db.delete(task)
        db.commit()

    def test_allowed_action_types(self) -> None:
        """Test that allowed_action_types returns the correct list of action types."""
        allowed_types = MonitorTask.allowed_action_types()
        assert len(allowed_types) == 3
        assert MonitorTaskType.DETECTION.value in allowed_types
        assert MonitorTaskType.CLASSIFICATION.value in allowed_types
        assert MonitorTaskType.PROMOTION.value in allowed_types

    def test_invalid_action_type(self, db: Session, monitor_config) -> None:
        """Test that creating a task with an invalid action type raises an error."""
        with pytest.raises(ValueError) as exc:
            MonitorTask.create(
                db=db,
                data={
                    "celery_id": "test-celery-id",
                    "action_type": "invalid_type",
                    "status": ExecutionLogStatus.pending.value,
                    "monitor_config_id": monitor_config.id,
                    "staged_resource_urn": "test-urn",
                },
            )
        assert "Invalid action_type 'invalid_type'" in str(exc.value)
