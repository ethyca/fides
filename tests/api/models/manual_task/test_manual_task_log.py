from sqlalchemy.orm import Session

from fides.api.models.manual_task import (
    ManualTask,
    ManualTaskConfig,
    ManualTaskInstance,
    ManualTaskLog,
    ManualTaskLogStatus,
)
from fides.api.models.privacy_request import PrivacyRequest


class TestManualTaskLog:
    """Tests for manual task logs."""

    def test_create_log(self, db: Session, manual_task: ManualTask):
        """Test creating a basic log entry."""
        log = ManualTaskLog.create_log(
            db=db,
            task_id=manual_task.id,
            status=ManualTaskLogStatus.complete,
            message="Test log",
        )

        # Verify log was created
        assert log.id is not None
        assert log.task_id == manual_task.id
        assert log.status == ManualTaskLogStatus.complete
        assert log.message == "Test log"
        assert log.details is None
        assert log.config_id is None
        assert log.instance_id is None
        assert log.created_at is not None

    def test_create_log_with_details(self, db: Session, manual_task: ManualTask):
        """Test creating a log entry with details."""
        details = {"key": "value", "nested": {"field": "data"}}
        log = ManualTaskLog.create_log(
            db=db,
            task_id=manual_task.id,
            status=ManualTaskLogStatus.complete,
            message="Test log with details",
            details=details,
        )

        # Verify log was created with details
        assert log.details == details

    def test_create_error_log(self, db: Session, manual_task: ManualTask):
        """Test creating an error log entry."""
        error_message = "Task failed due to invalid input"
        error_details = {"error_code": "INVALID_INPUT", "field": "email"}

        log = ManualTaskLog.create_error_log(
            db=db,
            task_id=manual_task.id,
            message=error_message,
            details=error_details,
        )

        # Verify error log was created
        assert log.id is not None
        assert log.task_id == manual_task.id
        assert log.status == ManualTaskLogStatus.error
        assert log.message == error_message
        assert log.details == error_details
        assert log.created_at is not None

    def test_create_error_log_with_config(
        self, db: Session, manual_task: ManualTask, manual_task_config: ManualTaskConfig
    ):
        """Test creating an error log entry with config reference."""
        log = ManualTaskLog.create_error_log(
            db=db,
            task_id=manual_task.id,
            message="Config validation failed",
            config_id=manual_task_config.id,
        )

        # Verify error log was created with config
        assert log.config_id == manual_task_config.id
        assert log.status == ManualTaskLogStatus.error

    def test_create_error_log_with_instance(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_config: ManualTaskConfig,
        privacy_request: PrivacyRequest,
    ):
        """Test creating an error log entry with instance reference."""
        # Create a real instance first
        instance = ManualTaskInstance.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": manual_task_config.id,
                "entity_id": privacy_request.id,
                "entity_type": "privacy_request",
            },
        )

        log = ManualTaskLog.create_error_log(
            db=db,
            task_id=manual_task.id,
            message="Instance execution failed",
            instance_id=instance.id,
        )

        # Verify error log was created with instance
        assert log.instance_id == instance.id
        assert log.status == ManualTaskLogStatus.error

    def test_create_error_log_with_all_fields(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_config: ManualTaskConfig,
        privacy_request: PrivacyRequest,
    ):
        """Test creating an error log entry with all fields populated."""
        # Create a real instance first
        instance = ManualTaskInstance.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": manual_task_config.id,
                "entity_id": privacy_request.id,
                "entity_type": "privacy_request",
            },
        )

        error_message = "Complete error scenario"
        error_details = {
            "error_code": "SYSTEM_ERROR",
            "stack_trace": "Error at line 42",
            "context": {"user_id": "123", "action": "update"},
        }

        log = ManualTaskLog.create_error_log(
            db=db,
            task_id=manual_task.id,
            message=error_message,
            config_id=manual_task_config.id,
            instance_id=instance.id,
            details=error_details,
        )

        # Verify all fields are populated
        assert log.task_id == manual_task.id
        assert log.status == ManualTaskLogStatus.error
        assert log.message == error_message
        assert log.config_id == manual_task_config.id
        assert log.instance_id == instance.id
        assert log.details == error_details
        assert log.created_at is not None

    def test_error_log_relationship(self, db: Session, manual_task: ManualTask):
        """Test that error logs are properly associated with the task."""
        log = ManualTaskLog.create_error_log(
            db=db,
            task_id=manual_task.id,
            message="Test error",
        )

        # Verify relationship
        assert log.task == manual_task
        assert log in manual_task.logs
        assert len(manual_task.logs) == 2  # One from creation + one error log

    def test_model_relationships(self):
        # Verify that the model has the expected relationships
        assert hasattr(ManualTaskLog, "task")
        # TODO: Add config and instance relationships when they are implemented
        # assert hasattr(ManualTaskLog, "config")
        # assert hasattr(ManualTaskLog, "instance")

    def test_model_columns(self):
        # Verify that the model has the expected columns
        assert hasattr(ManualTaskLog, "task_id")
        assert hasattr(ManualTaskLog, "config_id")
        assert hasattr(ManualTaskLog, "instance_id")
        assert hasattr(ManualTaskLog, "status")
        assert hasattr(ManualTaskLog, "message")
        assert hasattr(ManualTaskLog, "details")
        assert hasattr(ManualTaskLog, "created_at")

    def test_model_table_name(self):
        # Verify the table name
        assert ManualTaskLog.__tablename__ == "manual_task_log"
