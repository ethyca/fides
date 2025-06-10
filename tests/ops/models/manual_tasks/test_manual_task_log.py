from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

from fides.api.models.manual_tasks.manual_task import (
    ManualTask,
    ManualTaskConfig,
    ManualTaskConfigField,
    ManualTaskInstance,
    ManualTaskSubmission,
)
from fides.api.models.manual_tasks.manual_task_log import ManualTaskLog
from fides.api.models.manual_tasks.status import StatusType
from fides.api.schemas.manual_tasks.manual_task_schemas import (
    ManualTaskLogStatus,
    ManualTaskType,
)


@pytest.fixture
def manual_task_log(
    db: Session,
    manual_task: ManualTask,
    manual_task_config: ManualTaskConfig,
    manual_task_instance: ManualTaskInstance,
) -> ManualTaskLog:
    """Create a test log entry."""
    # Create the log entry
    ManualTaskLog.create_log(
        db=db,
        task_id=manual_task.id,
        config_id=manual_task_config.id,
        instance_id=manual_task_instance.id,
        status=ManualTaskLogStatus.complete,
        message="Test log message",
        details={"test_key": "test_value"},
    )

    # Query and return the created log
    return (
        db.query(ManualTaskLog)
        .filter(
            ManualTaskLog.task_id == manual_task.id,
            ManualTaskLog.config_id == manual_task_config.id,
            ManualTaskLog.instance_id == manual_task_instance.id,
            ManualTaskLog.message == "Test log message",
        )
        .first()
    )


class TestManualTaskLog:
    def test_create_log(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_config: ManualTaskConfig,
        manual_task_instance: ManualTaskInstance,
    ):
        """Test creating a log entry."""
        test_message = "Test log message"
        # Create a log entry
        ManualTaskLog.create_log(
            db=db,
            task_id=manual_task.id,
            config_id=manual_task_config.id,
            instance_id=manual_task_instance.id,
            status=ManualTaskLogStatus.complete,
            message=test_message,
            details={"test_key": "test_value"},
        )

        # Verify log was created
        log = (
            db.query(ManualTaskLog)
            .filter(
                ManualTaskLog.task_id == manual_task.id,
                ManualTaskLog.config_id == manual_task_config.id,
                ManualTaskLog.instance_id == manual_task_instance.id,
                ManualTaskLog.message == test_message,
            )
            .first()
        )
        assert log is not None
        assert log.status == ManualTaskLogStatus.complete
        assert log.message == test_message
        assert log.details == {"test_key": "test_value"}
        assert log.created_at is not None

    def test_create_log_without_config(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_instance: ManualTaskInstance,
    ):
        """Test creating a log entry without a config."""
        test_message = "Test log message without config"
        # Create a log entry without config
        ManualTaskLog.create_log(
            db=db,
            task_id=manual_task.id,
            instance_id=manual_task_instance.id,
            status=ManualTaskLogStatus.complete,
            message=test_message,
        )

        # Verify log was created
        log = (
            db.query(ManualTaskLog)
            .filter(
                ManualTaskLog.task_id == manual_task.id,
                ManualTaskLog.instance_id == manual_task_instance.id,
                ManualTaskLog.config_id.is_(None),
                ManualTaskLog.message == test_message,
            )
            .first()
        )
        assert log is not None
        assert log.status == ManualTaskLogStatus.complete
        assert log.message == test_message
        assert log.config_id is None

    def test_create_log_without_instance(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_config: ManualTaskConfig,
    ):
        """Test creating a log entry without an instance."""
        test_message = "Test log message without instance"
        # Create a log entry without instance
        ManualTaskLog.create_log(
            db=db,
            task_id=manual_task.id,
            config_id=manual_task_config.id,
            status=ManualTaskLogStatus.complete,
            message=test_message,
        )

        # Verify log was created
        log = (
            db.query(ManualTaskLog)
            .filter(
                ManualTaskLog.task_id == manual_task.id,
                ManualTaskLog.config_id == manual_task_config.id,
                ManualTaskLog.instance_id.is_(None),
                ManualTaskLog.message == test_message,
            )
            .first()
        )
        assert log is not None
        assert log.status == ManualTaskLogStatus.complete
        assert log.message == test_message
        assert log.instance_id is None

    def test_log_relationships(
        self,
        db: Session,
        manual_task_log: ManualTaskLog,
        manual_task: ManualTask,
        manual_task_config: ManualTaskConfig,
        manual_task_instance: ManualTaskInstance,
    ):
        """Test log relationships."""
        # Verify relationships
        assert manual_task_log.task == manual_task
        assert manual_task_log.config == manual_task_config
        assert manual_task_log.instance == manual_task_instance

    def test_log_creation_with_submission(
        self,
        db: Session,
        manual_task_instance: ManualTaskInstance,
        manual_task_form_field: ManualTaskConfigField,
    ):
        """Test log creation when creating a submission."""
        # Create a submission
        submission = ManualTaskSubmission.create_or_update(
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

        # Get all logs for this instance
        all_logs = manual_task_instance.get_all_logs()

        # Verify we have all expected logs
        assert len(all_logs) >= 3, "Expected at least 3 logs to be created"

        # Verify task instance creation log
        instance_log = all_logs[0]
        assert (
            instance_log.message
            == "Created task instance for privacy_request test_privacy_request"
        )
        assert instance_log.details is not None
        assert instance_log.details.get("entity_type") == "privacy_request"
        assert instance_log.details.get("entity_id") == "test_privacy_request"

        # Find submission creation log by message
        submission_log = next(
            (
                log
                for log in all_logs
                if log.message == "Created submission for field test_form_field"
            ),
            None,
        )
        assert submission_log is not None, "Could not find submission creation log"
        assert submission_log.details is not None
        assert (
            submission_log.details.get("field_key") == manual_task_form_field.field_key
        )
        assert (
            submission_log.details.get("field_type")
            == manual_task_form_field.field_type
        )
        assert submission_log.details.get("submitted_by") == 1
        assert submission_log.details.get("status") == "completed"

    def test_log_creation_with_completion(
        self,
        db: Session,
        manual_task_instance: ManualTaskInstance,
        manual_task_form_field: ManualTaskConfigField,
    ):
        """Test log creation when completing a submission."""
        # Create and complete a submission
        submission = ManualTaskSubmission.create_or_update(
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

        # Verify submission log was created
        log = (
            db.query(ManualTaskLog)
            .filter(
                ManualTaskLog.task_id == submission.task_id,
                ManualTaskLog.instance_id == submission.instance_id,
                ManualTaskLog.message == "Created submission for field test_form_field",
            )
            .first()
        )
        assert log is not None
        assert log.status == ManualTaskLogStatus.complete
        assert log.details["field_key"] == "test_form_field"
        assert log.details["field_type"] == manual_task_form_field.field_type
        assert log.details["submitted_by"] == 1

    def test_get_all_logs(self, db: Session, manual_task_instance: ManualTaskInstance):
        """Test getting all logs for an instance."""
        # Create some task-level logs
        ManualTaskLog.create_log(
            db=db,
            task_id=manual_task_instance.task_id,
            status=ManualTaskLogStatus.complete,
            message="Task level log 1",
        )
        ManualTaskLog.create_log(
            db=db,
            task_id=manual_task_instance.task_id,
            status=ManualTaskLogStatus.complete,
            message="Task level log 2",
        )

        # Create some instance-level logs
        ManualTaskLog.create_log(
            db=db,
            task_id=manual_task_instance.task_id,
            instance_id=manual_task_instance.id,
            status=ManualTaskLogStatus.complete,
            message="Instance level log 1",
        )
        ManualTaskLog.create_log(
            db=db,
            task_id=manual_task_instance.task_id,
            instance_id=manual_task_instance.id,
            status=ManualTaskLogStatus.complete,
            message="Instance level log 2",
        )

        # Get all logs
        all_logs = manual_task_instance.get_all_logs()
        # Account for instance creation log and any other system logs
        assert len(all_logs) >= 3  # At least + 2 instance-level logs
        assert all(log.created_at is not None for log in all_logs)

    def test_get_all_logs_error_handling(
        self, db: Session, manual_task_instance: ManualTaskInstance
    ):
        """Test error handling in get_all_logs."""
        # Create a new task for testing
        test_task = ManualTask.create(
            db=db,
            data={
                "task_type": ManualTaskType.privacy_request,
                "parent_entity_id": "test_connection",
                "parent_entity_type": "connection_config",
            },
        )

        # Create a new config for the test task
        test_config = ManualTaskConfig.create(
            db=db,
            data={
                "task_id": test_task.id,
                "config_type": "test_config",
                "fields": [
                    {
                        "field_key": "test_field",
                        "field_type": "form",
                        "field_metadata": {
                            "label": "Test Field",
                            "required": True,
                            "help_text": "Test field",
                        },
                    }
                ],
            },
        )

        # Create a new instance properly
        instance = test_task.create_entity_instance(
            db=db,
            config_id=test_config.id,
            entity_id="test",
            entity_type="test",
        )

        # Get logs for the valid instance
        logs = instance.get_all_logs()
        assert len(logs) == 1  # Should have the instance creation log
        assert logs[0].message == "Created task instance for test test"

        # Test with an instance that doesn't exist in the database
        non_existent_instance = ManualTaskInstance(
            id="non_existent",
            task_id=test_task.id,
            config_id=test_config.id,
            entity_id="test",
            entity_type="test",
        )
        non_existent_instance.task = test_task
        logs = non_existent_instance.get_all_logs()
        assert len(logs) == 0  # Should have no logs for non-existent instance

    def test_create_log_with_different_statuses(
        self,
        db: Session,
        manual_task: ManualTask,
    ):
        """Test creating log entries with different statuses."""
        # Create a unique prefix for this test's logs
        test_prefix = f"TEST_STATUS_{datetime.now(timezone.utc).timestamp()}"

        # Test each status type
        for status in ManualTaskLogStatus:
            test_message = f"{test_prefix} Test log with status {status}"
            ManualTaskLog.create_log(
                db=db,
                task_id=manual_task.id,
                status=status,
                message=test_message,
            )

            # Verify log was created with correct status
            log = (
                db.query(ManualTaskLog)
                .filter(
                    ManualTaskLog.task_id == manual_task.id,
                    ManualTaskLog.status == status,
                    ManualTaskLog.message == test_message,
                )
                .first()
            )
            assert log is not None
            assert log.status == status
            assert log.message == test_message

    def test_create_log_with_minimal_parameters(
        self,
        db: Session,
        manual_task: ManualTask,
    ):
        """Test creating a log entry with only required parameters."""
        # Create a unique prefix for this test's log
        test_prefix = f"TEST_MINIMAL_{datetime.now(timezone.utc).timestamp()}"

        # Create a log entry with only task_id and status
        ManualTaskLog.create_log(
            db=db,
            task_id=manual_task.id,
            status=ManualTaskLogStatus.complete,
            message=test_prefix,  # Use unique prefix to identify this log
        )

        # Verify log was created
        log = (
            db.query(ManualTaskLog)
            .filter(
                ManualTaskLog.task_id == manual_task.id,
                ManualTaskLog.status == ManualTaskLogStatus.complete,
                ManualTaskLog.message == test_prefix,
            )
            .first()
        )
        assert log is not None
        assert log.message == test_prefix
        assert log.details is None
        assert log.config_id is None
        assert log.instance_id is None

    def test_create_log_with_complex_details(
        self,
        db: Session,
        manual_task: ManualTask,
    ):
        """Test creating a log entry with complex details structure."""
        complex_details = {
            "nested": {
                "array": [1, 2, 3],
                "object": {"key": "value"},
            },
            "boolean": True,
            "number": 42,
            "null_value": None,
        }

        ManualTaskLog.create_log(
            db=db,
            task_id=manual_task.id,
            status=ManualTaskLogStatus.complete,
            message="Test log with complex details",
            details=complex_details,
        )

        # Verify log was created with correct details
        log = (
            db.query(ManualTaskLog)
            .filter(
                ManualTaskLog.task_id == manual_task.id,
                ManualTaskLog.message == "Test log with complex details",
            )
            .first()
        )
        assert log is not None
        assert log.details == complex_details

    def test_create_log_with_special_characters(
        self,
        db: Session,
        manual_task: ManualTask,
    ):
        """Test creating a log entry with special characters in message and details."""
        special_message = "Test log with special chars: !@#$%^&*()_+{}|:\"<>?[]\\;',./"
        special_details = {
            "special_key!@#": "special_value$%^",
            "unicode": "测试日志",
            "emoji": "🌟",
        }

        ManualTaskLog.create_log(
            db=db,
            task_id=manual_task.id,
            status=ManualTaskLogStatus.complete,
            message=special_message,
            details=special_details,
        )

        # Verify log was created with correct special characters
        log = (
            db.query(ManualTaskLog)
            .filter(
                ManualTaskLog.task_id == manual_task.id,
                ManualTaskLog.message == special_message,
            )
            .first()
        )
        assert log is not None
        assert log.message == special_message
        assert log.details == special_details

    def test_create_log_with_different_timestamps(
        self,
        db: Session,
        manual_task: ManualTask,
    ):
        """Test that logs are created with correct timestamps."""
        # Create multiple logs with small delays
        logs = []
        for i in range(3):
            ManualTaskLog.create_log(
                db=db,
                task_id=manual_task.id,
                status=ManualTaskLogStatus.complete,
                message=f"Test log {i}",
            )
            logs.append(
                db.query(ManualTaskLog)
                .filter(
                    ManualTaskLog.task_id == manual_task.id,
                    ManualTaskLog.message == f"Test log {i}",
                )
                .first()
            )

        # Verify timestamps are set and in correct order
        assert all(log.created_at is not None for log in logs)
        assert logs[0].created_at <= logs[1].created_at <= logs[2].created_at

    def test_log_statuses_in_operations(
        self, db: Session, manual_task_instance: ManualTaskInstance
    ):
        """Test that different operations log appropriate statuses."""
        # Create a field definition
        field = ManualTaskConfigField.create(
            db=db,
            data={
                "task_id": manual_task_instance.task_id,
                "config_id": manual_task_instance.config_id,
                "field_key": "test_form_field",
                "field_type": "form",
                "field_metadata": {
                    "label": "Test Field",
                    "required": True,
                    "help_text": "Test field",
                },
            },
        )
        manual_task_instance.config.field_definitions.append(field)
        db.commit()

        # Test status transition log
        manual_task_instance.update_status(db, StatusType.in_progress)
        log = (
            db.query(ManualTaskLog)
            .filter(
                ManualTaskLog.task_id == manual_task_instance.task_id,
                ManualTaskLog.instance_id == manual_task_instance.id,
                ManualTaskLog.status == ManualTaskLogStatus.in_processing,
                ManualTaskLog.message.like("%status transitioning%"),
            )
            .first()
        )
        assert log is not None
        assert log.status == ManualTaskLogStatus.in_processing
        assert "status transitioning" in log.message

        # Test submission to completed task
        manual_task_instance.update_status(db, StatusType.completed)
        submission = ManualTaskSubmission.create_or_update(
            db=db,
            data={
                "task_id": manual_task_instance.task_id,
                "config_id": manual_task_instance.config_id,
                "field_id": field.id,
                "instance_id": manual_task_instance.id,
                "submitted_by": 1,
                "data": {"test_form_field": "test value"},
            },
        )
        # Submission should be None for completed tasks
        assert submission is None

        # Verify error log was created
        log = (
            db.query(ManualTaskLog)
            .filter(
                ManualTaskLog.task_id == manual_task_instance.task_id,
                ManualTaskLog.instance_id == manual_task_instance.id,
                ManualTaskLog.status == ManualTaskLogStatus.error,
                ManualTaskLog.message == "Cannot submit to a completed task instance",
            )
            .first()
        )
        assert log is not None
        assert log.status == ManualTaskLogStatus.error
        assert log.message == "Cannot submit to a completed task instance"
        assert log.details is not None
        assert log.details["field_key"] == "test_form_field"
        assert log.details["field_type"] == "form"
        assert log.details["submitted_by"] == 1
