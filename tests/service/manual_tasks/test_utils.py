from unittest.mock import MagicMock, patch

import pytest

from fides.api.models.manual_tasks.manual_task_log import ManualTaskLog
from fides.api.schemas.manual_tasks.manual_task_schemas import ManualTaskLogStatus
from fides.api.schemas.manual_tasks.manual_task_status import StatusType
from fides.service.manual_tasks.utils import TaskLogger, validate_fields


def verify_expected_reference_types(manual_task, expected_reference_types):
    """Verify that all references in the manual task have expected types."""
    assert all(
        ref.reference_type in expected_reference_types for ref in manual_task.references
    )


def verify_expected_reference_ids(manual_task, expected_reference_ids):
    """Verify that all references in the manual task have expected IDs."""
    assert all(
        ref.reference_id in expected_reference_ids for ref in manual_task.references
    )


def verify_expected_logs(logs, expected_messages):
    """Verify that all logs have expected messages."""
    assert len(logs) == len(expected_messages)
    assert all(log.message in expected_messages for log in logs)


class TestValidateFields:
    """Tests for the validate_fields function."""

    @pytest.mark.parametrize(
        "fields,is_submission,expected_error",
        [
            # Valid cases
            pytest.param(
                [
                    {
                        "field_key": "test_field",
                        "field_type": "text",
                        "field_metadata": {
                            "label": "Test Field",
                            "description": "A test field",
                            "required": True,
                        },
                    }
                ],
                False,
                None,
                id="valid_fields",
            ),
            pytest.param(
                [{"field_key": "test", "field_type": "text", "value": "test value"}],
                True,
                None,
                id="valid_submission",
            ),
            # Error cases
            pytest.param(
                [
                    {
                        "field_key": "same_key",
                        "field_type": "text",
                        "field_metadata": {},
                    },
                    {
                        "field_key": "same_key",
                        "field_type": "text",
                        "field_metadata": {},
                    },
                ],
                False,
                "Duplicate field keys found",
                id="duplicate_field_keys",
            ),
            pytest.param(
                [{"field_type": "text", "field_metadata": {}}],
                False,
                "field_key is required",
                id="duplicate_field_keys",
            ),
            pytest.param(
                [{"field_key": "test", "field_metadata": {}}],
                False,
                "field_type is required",
                id="field_type_required",
            ),
            pytest.param(
                [{"field_key": "test", "field_type": "text"}],
                True,
                "value is required for submissions",
                id="value_required_for_submissions",
            ),
            pytest.param(
                [
                    {
                        "field_key": "test",
                        "field_type": "invalid_type",
                        "field_metadata": {"label": "Test"},
                    }
                ],
                False,
                "Invalid field type",
                id="invalid_field_type",
            ),
            pytest.param(
                [
                    {
                        "field_key": "test",
                        "field_type": "text",
                        "field_metadata": {"invalid_key": "value"},
                    }
                ],
                False,
                "Invalid field data",
                id="invalid_field_data",
            ),
        ],
    )
    def test_validate_fields(self, fields, is_submission, expected_error):
        """Test field validation with various scenarios."""
        if expected_error:
            with pytest.raises(ValueError, match=expected_error):
                validate_fields(fields, is_submission)
        else:
            validate_fields(fields, is_submission)  # Should not raise


class TestTaskLogger:
    """Tests for the TaskLogger decorator and utility methods."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def mock_service(self, mock_db):
        service = MagicMock()
        service.db = mock_db
        return service

    @pytest.mark.parametrize(
        "return_value,expected_details,expected_status",
        [
            # Simple object return
            (
                type("TestResult", (), {"task_id": "123"}),
                {},
                ManualTaskLogStatus.complete,
            ),
            # Object with config_id
            (
                type("TestResult", (), {"task_id": "123", "config_id": "456"}),
                {},
                ManualTaskLogStatus.complete,
            ),
            # Tuple return with details
            (
                (
                    type("TestResult", (), {"task_id": "123"}),
                    {"details": {"test": "data"}},
                ),
                {"test": "data"},
                ManualTaskLogStatus.complete,
            ),
            # Custom status
            (
                type("TestResult", (), {"task_id": "123"}),
                {},
                ManualTaskLogStatus.in_progress,
            ),
        ],
    )
    def test_successful_operations(
        self, mock_service, return_value, expected_details, expected_status
    ):
        """Test successful operation logging with various return types."""

        @TaskLogger("test operation", success_status=expected_status)
        def test_method(self):
            return return_value

        with patch.object(ManualTaskLog, "create_log") as mock_create_log:
            result = test_method(mock_service)

            # Verify result
            if isinstance(return_value, tuple):
                assert result.task_id == return_value[0].task_id
            else:
                assert result.task_id == return_value.task_id

            # Verify log
            mock_create_log.assert_called_once()
            call_args = mock_create_log.call_args[1]
            assert call_args["task_id"] == "123"
            assert call_args["status"] == expected_status
            assert call_args["message"] == "test operation"
            assert call_args["details"] == expected_details

    @pytest.mark.parametrize(
        "error_type,error_msg,task_id,expected_msg",
        [
            pytest.param(
                ValueError,
                "value error",
                "123",
                "Error in test operation: value error",
            ),
            pytest.param(
                KeyError,
                "key error",
                "123",
                "Error in test operation: 'key error'",
            ),
        ],
        ids=["value_error", "key_error"],
    )
    def test_error_handling(
        self, mock_service, error_type, error_msg, task_id, expected_msg
    ):
        """Test error logging with different error types."""

        @TaskLogger("test operation")
        def test_method(self, **kwargs):
            raise error_type(error_msg)

        with patch.object(ManualTaskLog, "create_log") as mock_create_log:
            with pytest.raises(error_type):
                test_method(mock_service, task_id=task_id)

            if task_id:
                mock_create_log.assert_called_once()
                call_args = mock_create_log.call_args[1]
                assert call_args["task_id"] == task_id
                assert call_args["status"] == ManualTaskLogStatus.error
                assert call_args["message"] == expected_msg
            else:
                mock_create_log.assert_not_called()

    @pytest.mark.parametrize(
        "entity_type,entity_id,expected_id_fields",
        [
            ("task", "123", {"task_id": "123"}),
            ("config", "456", {"task_id": "123", "config_id": "456"}),
        ],
        ids=["task", "config"],
    )
    def test_log_create(self, mock_db, entity_type, entity_id, expected_id_fields):
        """Test creation logging for different entity types."""
        with patch.object(ManualTaskLog, "create_log") as mock_create_log:
            TaskLogger.log_create(
                db=mock_db,
                task_id="123",
                entity_type=entity_type,
                entity_id=entity_id,
                details={"test": "data"},
                user_id="user123",
            )

            mock_create_log.assert_called_once()
            call_args = mock_create_log.call_args[1]
            assert all(call_args[k] == v for k, v in expected_id_fields.items())
            assert call_args["status"] == ManualTaskLogStatus.created
            assert call_args["message"] == f"Created new {entity_type}"
            assert call_args["details"] == {"test": "data", "user_id": "user123"}

    def test_invalid_entity_type(self, mock_db):
        """Test log_create with invalid entity type."""
        with pytest.raises(ValueError, match="Invalid entity type"):
            TaskLogger.log_create(
                db=mock_db,
                task_id="123",
                entity_type="invalid",
                entity_id="456",
            )
