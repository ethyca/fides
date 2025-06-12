import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fides.api.models.detection_discovery.monitor_task import (
    MonitorTask,
    MonitorTaskExecutionLog,
    MonitorTaskType,
    TaskRunType,
    create_monitor_task_with_execution_log,
    update_monitor_task_with_execution_log,
)
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
                "staged_resource_urns": ["test-urn"],
                "child_resource_urns": ["child-urn-1", "child-urn-2"],
                "task_arguments": {"arg1": "value1"},
            },
        )

        assert task.celery_id == "test-celery-id"
        assert task.action_type == MonitorTaskType.DETECTION.value
        assert task.status.value == ExecutionLogStatus.pending.value
        assert task.message == "Test message"
        assert task.monitor_config_id == monitor_config.id
        assert task.staged_resource_urns == ["test-urn"]
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
            },
        )

        # Required fields should be set
        assert task.celery_id == "test-celery-id"
        assert task.action_type == MonitorTaskType.CLASSIFICATION.value
        assert task.status.value == ExecutionLogStatus.in_processing.value
        assert task.monitor_config_id == monitor_config.id

        # Optional fields should have default values
        assert task.message is None
        assert task.staged_resource_urns is None
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
                    "staged_resource_urns": ["test-urn"],
                },
            )
        assert "Invalid action_type 'invalid_type'" in str(exc.value)

    def test_duplicate_celery_id(self, db: Session, monitor_config) -> None:
        """Test that creating monitor tasks with duplicate celery_ids raises an error."""
        # Create first monitor task
        task = MonitorTask.create(
            db=db,
            data={
                "celery_id": "ca97b95d-4eb0-4d95-9970-05664e9a5bd8",
                "action_type": MonitorTaskType.DETECTION.value,
                "status": ExecutionLogStatus.pending.value,
                "monitor_config_id": monitor_config.id,
            },
        )

        # Attempt to create second monitor task with same celery_id
        with pytest.raises(IntegrityError) as exc:
            MonitorTask.create(
                db=db,
                data={
                    "celery_id": "ca97b95d-4eb0-4d95-9970-05664e9a5bd8",
                    "action_type": MonitorTaskType.CLASSIFICATION.value,
                    "status": ExecutionLogStatus.in_processing.value,
                    "monitor_config_id": monitor_config.id,
                },
            )
        assert "duplicate key value violates unique constraint" in str(exc)

        # Clean up
        db.delete(task)
        db.commit()

    def test_delete_monitor_task_cascades_to_execution_logs(
        self, db: Session, monitor_config
    ) -> None:
        """Test that deleting a monitor task cascades to its execution logs."""
        # Create a monitor task
        task = MonitorTask.create(
            db=db,
            data={
                "celery_id": "test-celery-id",
                "action_type": MonitorTaskType.DETECTION.value,
                "status": ExecutionLogStatus.pending.value,
                "monitor_config_id": monitor_config.id,
            },
        )

        # Create multiple execution logs for the task
        execution_log_1 = MonitorTaskExecutionLog.create(
            db=db,
            data={
                "celery_id": "test-celery-id-1",
                "monitor_task_id": task.id,
                "status": ExecutionLogStatus.pending.value,
            },
        )
        execution_log_2 = MonitorTaskExecutionLog.create(
            db=db,
            data={
                "celery_id": "test-celery-id-2",
                "monitor_task_id": task.id,
                "status": ExecutionLogStatus.in_processing.value,
            },
        )

        # Store IDs for later verification
        task_id = task.id
        execution_log_1_id = execution_log_1.id
        execution_log_2_id = execution_log_2.id

        # Delete the task
        db.delete(task)
        db.commit()

        # Verify task is deleted
        assert db.query(MonitorTask).filter_by(id=task_id).first() is None

        # Verify execution logs are deleted
        assert (
            db.query(MonitorTaskExecutionLog).filter_by(id=execution_log_1_id).first()
            is None
        )
        assert (
            db.query(MonitorTaskExecutionLog).filter_by(id=execution_log_2_id).first()
            is None
        )


class TestMonitorTaskExecutionLog:
    """Tests for the MonitorTaskExecutionLog model"""

    def test_create_monitor_task_execution_log(
        self, db: Session, monitor_config
    ) -> None:
        """Test creating a monitor task execution log with valid data."""
        # First create a monitor task that we can reference
        task = MonitorTask.create(
            db=db,
            data={
                "celery_id": "test-celery-id",
                "action_type": MonitorTaskType.DETECTION.value,
                "status": ExecutionLogStatus.pending.value,
                "monitor_config_id": monitor_config.id,
            },
        )

        # Create the execution log
        execution_log = MonitorTaskExecutionLog.create(
            db=db,
            data={
                "celery_id": "test-celery-id-2",
                "monitor_task_id": task.id,
                "status": ExecutionLogStatus.pending.value,
                "message": "Test execution message",
                "run_type": TaskRunType.MANUAL,
            },
        )

        assert execution_log.celery_id == "test-celery-id-2"
        assert execution_log.monitor_task_id == task.id
        assert execution_log.status.value == ExecutionLogStatus.pending.value
        assert execution_log.message == "Test execution message"
        assert execution_log.run_type == TaskRunType.MANUAL
        assert execution_log.created_at is not None
        assert execution_log.updated_at is not None

        # Clean up
        db.delete(execution_log)
        db.commit()
        db.delete(task)
        db.commit()

    def test_create_monitor_task_execution_log_defaults(
        self, db: Session, monitor_config
    ) -> None:
        """Test creating a monitor task execution log with minimal required fields and verify default values."""
        # First create a monitor task that we can reference
        task = MonitorTask.create(
            db=db,
            data={
                "celery_id": "test-celery-id",
                "action_type": MonitorTaskType.DETECTION.value,
                "status": ExecutionLogStatus.pending.value,
                "monitor_config_id": monitor_config.id,
            },
        )

        # Create the execution log with minimal fields
        execution_log = MonitorTaskExecutionLog.create(
            db=db,
            data={
                "celery_id": "test-celery-id-2",
                "monitor_task_id": task.id,
                "status": ExecutionLogStatus.pending.value,
            },
        )

        # Required fields should be set
        assert execution_log.celery_id == "test-celery-id-2"
        assert execution_log.monitor_task_id == task.id
        assert execution_log.status.value == ExecutionLogStatus.pending.value

        # Optional fields should have default values
        assert execution_log.message is None
        assert execution_log.run_type == TaskRunType.SYSTEM  # Default value from model
        assert execution_log.created_at is not None
        assert execution_log.updated_at is not None

        # Clean up
        db.delete(execution_log)
        db.commit()
        db.delete(task)
        db.commit()

    def test_invalid_monitor_task_id(self, db: Session) -> None:
        """Test that creating an execution log with an invalid monitor_task_id raises an error."""
        with pytest.raises(IntegrityError) as exc:
            MonitorTaskExecutionLog.create(
                db=db,
                data={
                    "celery_id": "61fc9e1d-977d-4e69-a33b-a4edbab375c1",
                    "monitor_task_id": "non-existent-id",
                    "status": ExecutionLogStatus.pending.value,
                },
            )

        assert (
            'Key (monitor_task_id)=(non-existent-id) is not present in table "monitortask"'
            in str(exc)
        )


class TestCreateMonitorTaskWithExecutionLog:
    """Tests for the create_monitor_task_with_execution_log function"""

    def test_create_monitor_task_with_execution_log_success(
        self, db: Session, monitor_config
    ) -> None:
        """Test successful creation of a monitor task with execution log"""
        monitor_task_data = {
            "action_type": MonitorTaskType.DETECTION.value,
            "monitor_config_id": monitor_config.id,
            "staged_resource_urns": ["test-urn"],
            "child_resource_urns": ["child-1", "child-2"],
            "task_arguments": {"arg1": "value1"},
            "message": "Test message",
        }

        task = create_monitor_task_with_execution_log(
            db=db, monitor_task_data=monitor_task_data
        )

        # Verify task was created with correct data
        assert task.action_type == MonitorTaskType.DETECTION.value
        assert task.status == ExecutionLogStatus.pending
        assert task.celery_id is not None
        assert task.task_arguments == {"arg1": "value1"}
        assert task.message == "Test message"
        assert task.monitor_config_id == monitor_config.id
        assert task.staged_resource_urns == ["test-urn"]
        assert task.child_resource_urns == ["child-1", "child-2"]

        # Verify execution log was created
        assert len(task.execution_logs) == 1
        execution_log = task.execution_logs[0]
        assert execution_log.status == ExecutionLogStatus.pending
        assert execution_log.celery_id == task.celery_id
        assert execution_log.monitor_task_id == task.id
        assert execution_log.run_type == TaskRunType.SYSTEM

        # Clean up
        db.delete(execution_log)
        db.delete(task)
        db.commit()

    def test_create_monitor_task_with_execution_log_minimal(
        self, db: Session, monitor_config
    ) -> None:
        """Test creation with minimal required fields"""
        monitor_task_data = {
            "action_type": MonitorTaskType.CLASSIFICATION.value,
            "monitor_config_id": monitor_config.id,
        }

        task = create_monitor_task_with_execution_log(
            db=db, monitor_task_data=monitor_task_data
        )

        # Verify task was created with correct data
        assert task.action_type == MonitorTaskType.CLASSIFICATION.value
        assert task.status == ExecutionLogStatus.pending
        assert task.celery_id is not None
        assert task.task_arguments is None
        assert task.message is None
        assert task.monitor_config_id == monitor_config.id
        assert task.staged_resource_urns is None
        assert task.child_resource_urns is None

        # Verify execution log was created
        assert len(task.execution_logs) == 1
        execution_log = task.execution_logs[0]
        assert execution_log.status == ExecutionLogStatus.pending
        assert execution_log.monitor_task_id == task.id
        assert execution_log.celery_id == task.celery_id
        assert execution_log.run_type == TaskRunType.SYSTEM

        # Clean up
        db.delete(execution_log)
        db.delete(task)
        db.commit()

    def test_create_monitor_task_with_execution_log_invalid_monitor_config(
        self, db: Session
    ) -> None:
        """Test that creating with invalid monitor_config_id raises error"""
        monitor_task_data = {
            "action_type": MonitorTaskType.DETECTION.value,
            "monitor_config_id": "non-existent-id",
        }

        with pytest.raises(IntegrityError) as exc:
            create_monitor_task_with_execution_log(
                db=db, monitor_task_data=monitor_task_data
            )
        db.rollback()  # Ensure we rollback the failed transaction

        assert (
            'Key (monitor_config_id)=(non-existent-id) is not present in table "monitorconfig"'
            in str(exc)
        )

    def test_create_monitor_task_with_execution_log_invalid_action_type(
        self, db: Session, monitor_config
    ) -> None:
        """Test that creating with invalid action_type raises error"""
        monitor_task_data = {
            "action_type": "invalid_type",
            "monitor_config_id": monitor_config.id,
        }

        with pytest.raises(ValueError) as exc:
            create_monitor_task_with_execution_log(
                db=db, monitor_task_data=monitor_task_data
            )

        assert "Invalid action_type 'invalid_type'" in str(exc)


class TestUpdateMonitorTaskWithExecutionLog:
    """Tests for the update_monitor_task_with_execution_log function"""

    def test_update_with_celery_id(self, db: Session, monitor_config) -> None:
        """Test updating a task using celery_id"""
        # First create a task and execution log.
        # Create an execution log to verify that the update function creates a
        # new one instead of modifying an existing one.
        monitor_task_data = {
            "action_type": MonitorTaskType.DETECTION.value,
            "monitor_config_id": monitor_config.id,
        }
        task = create_monitor_task_with_execution_log(
            db=db, monitor_task_data=monitor_task_data
        )
        original_celery_id = task.celery_id

        # Update the task with new status and message
        updated_task = update_monitor_task_with_execution_log(
            db=db,
            celery_id=original_celery_id,
            status=ExecutionLogStatus.in_processing,
            message="Processing task",
            run_type=TaskRunType.MANUAL,
        )

        # Verify task was updated
        assert updated_task.id == task.id
        assert updated_task.celery_id == original_celery_id
        assert updated_task.status == ExecutionLogStatus.in_processing
        assert updated_task.message == "Processing task"

        # Verify new execution log was created
        assert len(updated_task.execution_logs) == 2  # Original + new log
        latest_log = updated_task.execution_logs[1]
        assert latest_log.status == ExecutionLogStatus.in_processing
        assert latest_log.message == "Processing task"
        assert latest_log.celery_id == original_celery_id
        assert latest_log.run_type == TaskRunType.MANUAL

        # Clean up
        db.delete(task)
        db.commit()

    def test_update_with_task_record(self, db: Session, monitor_config) -> None:
        """Test updating a task using task_record"""
        # First create a task and execution log.
        # Create an execution log to verify that the update function creates a
        # new one instead of modifying an existing one.
        monitor_task_data = {
            "action_type": MonitorTaskType.CLASSIFICATION.value,
            "monitor_config_id": monitor_config.id,
        }
        task = create_monitor_task_with_execution_log(
            db=db, monitor_task_data=monitor_task_data
        )
        prev_celery_id = task.celery_id

        # Update the task with new status and message
        updated_task = update_monitor_task_with_execution_log(
            db=db,
            task_record=task,
            status=ExecutionLogStatus.complete,
            message="Task completed",
        )

        # Verify task was updated with new celery_id
        assert updated_task.id == task.id
        assert updated_task.celery_id != prev_celery_id  # Should have new celery_id
        assert updated_task.status == ExecutionLogStatus.complete
        assert updated_task.message == "Task completed"

        # Verify new execution log was created
        assert len(updated_task.execution_logs) == 2  # Original + new log
        latest_log = updated_task.execution_logs[1]
        assert latest_log.status == ExecutionLogStatus.complete
        assert latest_log.message == "Task completed"
        assert latest_log.celery_id == updated_task.celery_id
        assert latest_log.run_type == TaskRunType.SYSTEM  # Default value

        # Clean up
        db.delete(task)
        db.commit()

    def test_update_with_invalid_celery_id(self, db: Session) -> None:
        """Test that updating with non-existent celery_id raises error"""
        with pytest.raises(ValueError) as exc:
            update_monitor_task_with_execution_log(
                db=db,
                celery_id="non-existent-id",
                status=ExecutionLogStatus.in_processing,
            )
        assert "Could not find MonitorTask with celery_id non-existent-id" in str(exc)

    def test_update_without_required_params(self, db: Session) -> None:
        """Test that updating without celery_id or task_record raises error"""
        with pytest.raises(ValueError) as exc:
            update_monitor_task_with_execution_log(
                db=db,
                status=ExecutionLogStatus.in_processing,
            )
        assert "Either celery_id or task_record must be provided" in str(exc)
