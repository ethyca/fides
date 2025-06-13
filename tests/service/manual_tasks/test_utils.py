from typing import Union
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

from fides.api.models.manual_tasks.manual_task_config import ManualTaskConfigField
from fides.api.models.manual_tasks.manual_task_instance import ManualTaskInstance
from fides.api.schemas.manual_tasks.manual_task_schemas import ManualTaskLogStatus
from fides.api.schemas.manual_tasks.manual_task_status import (
    StatusTransitionNotAllowed,
    StatusType,
)
from fides.service.manual_tasks.manual_task_instance_service import (
    ManualTaskInstanceService,
)
from fides.service.manual_tasks.utils import (
    create_error_log,
    create_operation_logs,
    create_status_change_log,
    validate_fields,
    validate_status_transition,
    with_error_logging,
)


class TestValidateFields:
    def test_validate_fields_success(self):
        """Test successful field validation."""
        fields = [
            {
                "field_key": "test_field",
                "field_type": "text",
                "field_metadata": {
                    "required": True,
                    "label": "Test Field",
                    "help_text": "This is a test field",
                    "min_length": 1,
                    "max_length": 100,
                    "pattern": "^[a-zA-Z0-9]+$",
                    "placeholder": "Enter a value",
                    "default_value": "default_value",
                },
            }
        ]
        # Should not raise any exception
        validate_fields(fields, is_submission=False)

    def test_validate_fields_duplicate_keys(self):
        """Test validation fails for duplicate field keys."""
        fields = [
            {"field_key": "test_field", "field_type": "text"},
            {"field_key": "test_field", "field_type": "text"},
        ]
        with pytest.raises(ValueError, match="Duplicate field keys found"):
            validate_fields(fields)

    def test_validate_fields_missing_key(self):
        """Test validation fails for missing field key."""
        fields = [{"field_type": "text"}]
        with pytest.raises(ValueError, match="field_key is required"):
            validate_fields(fields)

    def test_validate_fields_missing_type(self):
        """Test validation fails for missing field type."""
        fields = [{"field_key": "test_field"}]
        with pytest.raises(ValueError, match="field_type is required"):
            validate_fields(fields)

    def test_validate_fields_submission_missing_value(self):
        """Test validation fails for submission without value."""
        fields = [{"field_key": "test_field", "field_type": "text"}]
        with pytest.raises(ValueError, match="value is required for submissions"):
            validate_fields(fields, is_submission=True)

    @pytest.mark.parametrize(
        "test_case, field_data, expected_error_msg",
        [
            pytest.param(
                "missing_value",
                {
                    "field_key": "test_field",
                    "field_type": "text",
                    # Missing "value" field
                },
                "value is required for submissions",
                id="missing_value",
            ),
            pytest.param(
                "missing_field_key",
                {
                    "field_type": "text",
                    "value": "test value",
                    # Missing field_key
                },
                "field_key is required",
                id="missing_field_key",
            ),
            pytest.param(
                "missing_field_type",
                {
                    "field_key": "test_field",
                    "value": "test value",
                    # Missing field_type
                },
                "field_type is required",
                id="missing_field_type",
            ),
            pytest.param(
                "duplicate_field_keys",
                [
                    {
                        "field_key": "test_field",
                        "field_type": "text",
                        "value": "test value 1",
                    },
                    {
                        "field_key": "test_field",  # Duplicate key
                        "field_type": "text",
                        "value": "test value 2",
                    },
                ],
                "Duplicate field keys found",
                id="duplicate_field_keys",
            ),
        ],
    )
    def test_validate_field_for_submission_mismatch(
        self,
        test_case: str,
        field_data: Union[dict, list],
        expected_error_msg: str,
        manual_task_config_field_text: ManualTaskConfigField,
    ) -> None:
        """Test validation fails for various field mismatches.

        Args:
            test_case: Description of the test case
            field_data: The field data to validate (either a single field dict or list of fields)
            expected_error_msg: Expected error message substring
            manual_task_config_field_text: Text field fixture
        """
        fields = field_data if isinstance(field_data, list) else [field_data]
        with pytest.raises(ValueError, match=expected_error_msg):
            validate_fields(fields, is_submission=True)


class TestValidateStatusTransition:
    def test_validate_status_transition_success(self):
        """Test successful status transition."""
        # Should not raise any exception
        validate_status_transition(StatusType.pending, StatusType.in_progress)

    def test_validate_status_transition_from_completed(self):
        """Test transition from completed status is not allowed."""
        with pytest.raises(StatusTransitionNotAllowed):
            validate_status_transition(StatusType.completed, StatusType.in_progress)


class TestCreateOperationLogs:
    def test_create_operation_logs_success(self):
        """Test creating success operation logs."""
        logs = create_operation_logs(
            task_id="test_task",
            config_id="test_config",
            instance_id="test_instance",
            operation="test operation",
            details={"test": "data"},
        )
        assert len(logs) == 1
        log = logs[0]
        assert log["task_id"] == "test_task"
        assert log["status"] == ManualTaskLogStatus.complete
        assert log["details"] == {"test": "data"}

    def test_create_operation_logs_error(self):
        """Test creating error operation logs."""
        error = ValueError("test error")
        logs = create_operation_logs(
            task_id="test_task",
            config_id="test_config",
            instance_id="test_instance",
            operation="test operation",
            error=error,
        )
        assert len(logs) == 1
        log = logs[0]
        assert log["task_id"] == "test_task"
        assert log["status"] == ManualTaskLogStatus.error
        assert log["message"] == "test error"


class TestCreateStatusChangeLog:
    def test_create_status_change_log(self):
        """Test creating status change log."""
        log = create_status_change_log(
            task_id="test_task",
            config_id="test_config",
            instance_id="test_instance",
            previous_status=StatusType.pending,
            new_status=StatusType.in_progress,
            user_id="test_user",
        )
        assert log["task_id"] == "test_task"
        assert log["status"] == ManualTaskLogStatus.in_progress
        assert "pending" in log["message"]
        assert "in_progress" in log["message"]
        assert log["details"]["user_id"] == "test_user"


class TestCreateErrorLog:
    def test_create_error_log(self):
        """Test creating error log."""
        error = ValueError("test error")
        context = {"test": "context"}
        log = create_error_log(
            task_id="test_task",
            config_id="test_config",
            instance_id="test_instance",
            error=error,
            context=context,
        )
        assert log["task_id"] == "test_task"
        assert log["status"] == ManualTaskLogStatus.error
        assert log["message"] == "test error"
        assert log["details"] == context


class TestWithErrorLogging:
    def test_with_error_logging_success(self):
        """Test error logging decorator with successful execution."""

        @with_error_logging("test operation")
        def test_function(self):
            return {"task_id": "test_task", "details": {"test": "data"}}

        # Mock the db and create_log
        with patch(
            "fides.api.models.manual_tasks.manual_task_log.ManualTaskLog.create_log"
        ) as mock_create_log:

            class TestClass:
                def __init__(self):
                    self.db = MagicMock()

            result = test_function(TestClass())
            assert result["task_id"] == "test_task"
            assert result["details"] == {"test": "data"}
            mock_create_log.assert_called_once()

    def test_with_error_logging_error(self):
        """Test error logging decorator with error."""

        @with_error_logging("test operation")
        def test_function(self, task_id=None):  # Add task_id parameter
            raise ValueError("test error")

        # Mock the db and create_log
        with patch(
            "fides.api.models.manual_tasks.manual_task_log.ManualTaskLog.create_log"
        ) as mock_create_log:

            class TestClass:
                def __init__(self):
                    self.db = MagicMock()

            with pytest.raises(ValueError, match="test error"):
                test_function(TestClass(), task_id="test_task")  # Pass task_id

            mock_create_log.assert_called_once()
            call_args = mock_create_log.call_args[1]
            assert call_args["task_id"] == "test_task"
            assert call_args["status"] == ManualTaskLogStatus.error
            assert "Error in test operation: test error" in call_args["message"]

    def test_with_error_logging_error_no_task_id(self):
        """Test error logging decorator with error but no task_id."""

        @with_error_logging("test operation")
        def test_function(self):
            raise ValueError("test error")

        # Mock the db and create_log
        with patch(
            "fides.api.models.manual_tasks.manual_task_log.ManualTaskLog.create_log"
        ) as mock_create_log:

            class TestClass:
                def __init__(self):
                    self.db = MagicMock()

            with pytest.raises(ValueError, match="test error"):
                test_function(TestClass())  # No task_id

            mock_create_log.assert_not_called()  # No log should be created without task_id

    def test_with_error_logging_no_task_id(self):
        """Test error logging decorator when no task_id is present."""

        @with_error_logging("test operation")
        def test_function(self):
            return {"some_key": "some_value"}  # No task_id

        # Mock the db and create_log
        with patch(
            "fides.api.models.manual_tasks.manual_task_log.ManualTaskLog.create_log"
        ) as mock_create_log:

            class TestClass:
                def __init__(self):
                    self.db = MagicMock()

            result = test_function(TestClass())
            assert result["some_key"] == "some_value"
            mock_create_log.assert_not_called()

    def test_with_error_logging_creates_log(self):
        """Test that the decorator creates a log entry with correct parameters."""

        @with_error_logging("test operation")
        def test_function(self):
            return {"task_id": "test_task", "details": {"test": "data"}}

        with patch(
            "fides.api.models.manual_tasks.manual_task_log.ManualTaskLog.create_log"
        ) as mock_create_log:

            class TestClass:
                def __init__(self):
                    self.db = MagicMock()

            test_function(TestClass())
            mock_create_log.assert_called_once()
            call_args = mock_create_log.call_args[1]
            assert call_args["task_id"] == "test_task"
            assert call_args["status"] == ManualTaskLogStatus.complete
            assert call_args["message"] == "test operation"
            assert call_args["details"] == {"test": "data"}
