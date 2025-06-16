from unittest.mock import MagicMock, call, patch

import pytest
from pydantic import ValidationError

from fides.api.models.manual_tasks.manual_task_log import ManualTaskLog
from fides.api.schemas.manual_tasks.manual_task_schemas import ManualTaskLogStatus
from fides.api.schemas.manual_tasks.manual_task_status import (
    StatusTransitionNotAllowed,
    StatusType,
)
from fides.service.manual_tasks.utils import TaskLogger, validate_fields


class TestValidateFields:
    def test_validate_fields_success(self):
        """Test successful field validation."""
        fields = [
            {
                "field_key": "test_field",
                "field_type": "text",
                "field_metadata": {
                    "label": "Test Field",
                    "description": "A test field",
                    "required": True,
                },
            }
        ]
        validate_fields(fields)  # Should not raise

    def test_validate_fields_duplicate_keys(self):
        """Test validation fails with duplicate field keys."""
        fields = [
            {"field_key": "same_key", "field_type": "text", "field_metadata": {}},
            {"field_key": "same_key", "field_type": "text", "field_metadata": {}},
        ]
        with pytest.raises(ValueError, match="Duplicate field keys found"):
            validate_fields(fields)

    def test_validate_fields_missing_key(self):
        """Test validation fails when field_key is missing."""
        fields = [{"field_type": "text", "field_metadata": {}}]
        with pytest.raises(ValueError, match="field_key is required"):
            validate_fields(fields)

    def test_validate_fields_missing_type(self):
        """Test validation fails when field_type is missing."""
        fields = [{"field_key": "test", "field_metadata": {}}]
        with pytest.raises(ValueError, match="field_type is required"):
            validate_fields(fields)

    def test_validate_fields_submission_missing_value(self):
        """Test validation fails for submission without value."""
        fields = [{"field_key": "test", "field_type": "text"}]
        with pytest.raises(ValueError, match="value is required for submissions"):
            validate_fields(fields, is_submission=True)

    def test_validate_fields_submission_success(self):
        """Test successful submission field validation."""
        fields = [{"field_key": "test", "field_type": "text", "value": "test value"}]
        validate_fields(fields, is_submission=True)  # Should not raise

    def test_validate_fields_invalid_type(self):
        """Test validation fails with invalid field type."""
        fields = [
            {
                "field_key": "test",
                "field_type": "invalid_type",
                "field_metadata": {"label": "Test"},
            }
        ]
        with pytest.raises(ValueError, match="Invalid field type"):
            validate_fields(fields)

    def test_validate_fields_invalid_metadata(self):
        """Test validation fails with invalid metadata structure."""
        fields = [
            {
                "field_key": "test",
                "field_type": "text",
                "field_metadata": {"invalid_key": "value"},  # Missing required 'label'
            }
        ]
        with pytest.raises(ValueError, match="Invalid field data"):
            validate_fields(fields)

    def test_validate_fields_empty_metadata(self):
        """Test validation skips fields with empty metadata in non-submission case."""
        fields = [
            {
                "field_key": "test",
                "field_type": "text",
                "field_metadata": {},
            }
        ]
        with pytest.raises(ValueError, match="Invalid field data"):
            validate_fields(fields, is_submission=False)

    def test_validate_fields_minimum_required(self):
        """Test validation with minimum required fields."""
        fields = [
            {
                "field_key": "test",
                "field_type": "text",
                "field_metadata": {"label": "Test"},
            }
        ]
        validate_fields(fields)  # Should not raise


class TestTaskLogger:
    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def mock_service(self, mock_db):
        service = MagicMock()
        service.db = mock_db
        return service

    def test_successful_operation(self, mock_service):
        """Test successful operation logging."""

        @TaskLogger("test operation")
        def test_method(self):
            class TestResult:
                def __init__(self):
                    self.task_id = "123"

            return TestResult()  # Return just the object

        with patch.object(ManualTaskLog, "create_log") as mock_create_log:
            result = test_method(mock_service)
            assert result.task_id == "123"
            mock_create_log.assert_called_once_with(
                db=mock_service.db,
                task_id="123",
                config_id=None,
                instance_id=None,
                status=ManualTaskLogStatus.complete,
                message="test operation",
                details={},
            )

    def test_successful_operation_with_tuple(self, mock_service):
        """Test successful operation logging with tuple return."""

        @TaskLogger("test operation")
        def test_method(self):
            class TestResult:
                def __init__(self):
                    self.task_id = "123"

            return TestResult(), {"details": {"test": "data"}}

        with patch.object(ManualTaskLog, "create_log") as mock_create_log:
            result = test_method(mock_service)
            assert result.task_id == "123"
            mock_create_log.assert_called_once_with(
                db=mock_service.db,
                task_id="123",
                config_id=None,
                instance_id=None,
                status=ManualTaskLogStatus.complete,
                message="test operation",
                details={"test": "data"},
            )

    def test_operation_with_error(self, mock_service):
        """Test error logging."""
        error_msg = "Test error"

        @TaskLogger("test operation")
        def test_method(self, **kwargs):
            raise ValueError(error_msg)

        with patch.object(ManualTaskLog, "create_log") as mock_create_log:
            with pytest.raises(ValueError, match=error_msg):
                test_method(mock_service, task_id="123")

            mock_create_log.assert_called_once_with(
                db=mock_service.db,
                task_id="123",
                config_id=None,
                instance_id=None,
                status=ManualTaskLogStatus.error,
                message=f"Error in test operation: {error_msg}",
                details={},
            )

    def test_log_status_change(self, mock_db):
        """Test status change logging."""
        with patch.object(ManualTaskLog, "create_log") as mock_create_log:
            TaskLogger.log_status_change(
                db=mock_db,
                task_id="123",
                config_id="456",
                instance_id="789",
                previous_status=StatusType.pending,
                new_status=StatusType.in_progress,
                user_id="user123",
            )

            mock_create_log.assert_called_once_with(
                db=mock_db,
                task_id="123",
                config_id="456",
                instance_id="789",
                status=ManualTaskLogStatus.in_progress,
                message="Task instance status transitioning from pending to in_progress",
                details={
                    "previous_status": StatusType.pending,
                    "new_status": StatusType.in_progress,
                    "user_id": "user123",
                },
            )

    def test_log_create(self, mock_db):
        """Test creation logging."""
        with patch.object(ManualTaskLog, "create_log") as mock_create_log:
            # Test task creation
            TaskLogger.log_create(
                db=mock_db,
                task_id="123",
                entity_type="task",
                entity_id="123",
                user_id="user123",
                details={"test": "data"},
            )

            mock_create_log.assert_called_once_with(
                db=mock_db,
                task_id="123",
                status=ManualTaskLogStatus.created,
                message="Created new task",
                details={"test": "data", "user_id": "user123"},
            )

            # Reset mock for next test
            mock_create_log.reset_mock()

            # Test config creation
            TaskLogger.log_create(
                db=mock_db,
                task_id="123",
                entity_type="config",
                entity_id="456",
                details={"template": "standard"},
            )

            mock_create_log.assert_called_once_with(
                db=mock_db,
                task_id="123",
                config_id="456",
                status=ManualTaskLogStatus.created,
                message="Created new config",
                details={"template": "standard"},
            )

    def test_log_create_invalid_entity(self, mock_db):
        """Test creation logging with invalid entity type."""
        with pytest.raises(ValueError, match="Invalid entity type"):
            TaskLogger.log_create(
                db=mock_db, task_id="123", entity_type="invalid", entity_id="456"
            )

    def test_custom_success_status(self, mock_service):
        """Test operation with custom success status."""

        @TaskLogger("test operation", success_status=ManualTaskLogStatus.in_progress)
        def test_method(self):
            class TestResult:
                def __init__(self):
                    self.task_id = "123"

            return TestResult()

        with patch.object(ManualTaskLog, "create_log") as mock_create_log:
            test_method(mock_service)
            mock_create_log.assert_called_once_with(
                db=mock_service.db,
                task_id="123",
                config_id=None,
                instance_id=None,
                status=ManualTaskLogStatus.in_progress,
                message="test operation",
                details={},
            )

    def test_no_db_attribute(self):
        """Test operation when service has no db attribute."""
        service = MagicMock()
        delattr(service, "db")  # Remove db attribute

        @TaskLogger("test operation")
        def test_method(self):
            class TestResult:
                def __init__(self):
                    self.task_id = "123"

            return TestResult()

        result = test_method(service)
        assert result.task_id == "123"  # Operation should complete without logging

    def test_log_success_missing_task_id(self, mock_service):
        """Test successful operation logging without task_id."""

        @TaskLogger("test operation")
        def test_method(self):
            return {"other_key": "value"}  # No task_id

        with patch.object(ManualTaskLog, "create_log") as mock_create_log:
            result = test_method(mock_service)
            mock_create_log.assert_not_called()

    def test_log_success_object_result(self, mock_service):
        """Test successful operation logging with object result."""

        class TestResult:
            def __init__(self):
                self.task_id = "123"
                self.config_id = "456"

        @TaskLogger("test operation")
        def test_method(self):
            return TestResult()

        with patch.object(ManualTaskLog, "create_log") as mock_create_log:
            result = test_method(mock_service)
            mock_create_log.assert_called_once_with(
                db=mock_service.db,
                task_id="123",
                config_id="456",
                instance_id=None,
                status=ManualTaskLogStatus.complete,
                message="test operation",
                details={},
            )

    def test_log_error_different_types(self, mock_service):
        """Test error logging with different error types."""

        @TaskLogger("test operation")
        def test_method(self, error_type, **kwargs):
            if error_type == "value":
                raise ValueError("value error")
            elif error_type == "key":
                raise KeyError("key error")
            else:
                raise Exception("generic error")

        with patch.object(ManualTaskLog, "create_log") as mock_create_log:
            # Test ValueError
            with pytest.raises(ValueError):
                test_method(mock_service, "value", task_id="123")
            mock_create_log.assert_called_with(
                db=mock_service.db,
                task_id="123",
                config_id=None,
                instance_id=None,
                status=ManualTaskLogStatus.error,
                message="Error in test operation: value error",
                details={},
            )

            # Test KeyError
            mock_create_log.reset_mock()
            with pytest.raises(KeyError):
                test_method(mock_service, "key", task_id="123")
            mock_create_log.assert_called_with(
                db=mock_service.db,
                task_id="123",
                config_id=None,
                instance_id=None,
                status=ManualTaskLogStatus.error,
                message="Error in test operation: 'key error'",
                details={},
            )

    def test_log_with_optional_params(self, mock_service):
        """Test logging with various combinations of optional parameters."""

        @TaskLogger("test operation")
        def test_method(self, **kwargs):
            class TestResult:
                def __init__(self, **kwargs):
                    self.task_id = kwargs.get("task_id")
                    self.config_id = kwargs.get("config_id")
                    self.instance_id = kwargs.get("instance_id")

            return TestResult(**kwargs)

        with patch.object(ManualTaskLog, "create_log") as mock_create_log:
            # Test with all optional params
            test_method(
                mock_service,
                task_id="123",
                config_id="456",
                instance_id="789",
                details={"extra": "data"},
            )
            mock_create_log.assert_called_with(
                db=mock_service.db,
                task_id="123",
                config_id="456",
                instance_id="789",
                status=ManualTaskLogStatus.complete,
                message="test operation",
                details={"extra": "data"},
            )

            # Test with minimal params
            mock_create_log.reset_mock()
            test_method(mock_service, task_id="123")
            mock_create_log.assert_called_with(
                db=mock_service.db,
                task_id="123",
                config_id=None,
                instance_id=None,
                status=ManualTaskLogStatus.complete,
                message="test operation",
                details={},
            )
