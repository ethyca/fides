from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from fides.api.schemas.manual_tasks.manual_task_schemas import (
    ManualTaskLogCreate,
    ManualTaskLogResponse,
    ManualTaskLogStatus,
    ManualTaskParentEntityType,
    ManualTaskReferenceType,
    ManualTaskType,
)


class TestManualTaskEnums:
    """Tests for manual task enums."""

    def test_manual_task_type(self):
        """Test ManualTaskType enum values."""
        assert ManualTaskType.privacy_request == "privacy_request"
        # Test invalid value
        with pytest.raises(ValueError):
            ManualTaskType("invalid_type")

    def test_manual_task_parent_entity_type(self):
        """Test ManualTaskParentEntityType enum values."""
        assert ManualTaskParentEntityType.connection_config == "connection_config"
        # Test invalid value
        with pytest.raises(ValueError):
            ManualTaskParentEntityType("invalid_type")

    def test_manual_task_reference_type(self):
        """Test ManualTaskReferenceType enum values."""
        assert ManualTaskReferenceType.privacy_request == "privacy_request"
        assert ManualTaskReferenceType.connection_config == "connection_config"
        assert ManualTaskReferenceType.manual_task_config == "manual_task_config"
        assert ManualTaskReferenceType.assigned_user == "assigned_user"
        # Test invalid value
        with pytest.raises(ValueError):
            ManualTaskReferenceType("invalid_type")

    def test_manual_task_log_status(self):
        """Test ManualTaskLogStatus enum values."""
        assert ManualTaskLogStatus.created == "created"
        assert ManualTaskLogStatus.in_progress == "in_progress"
        assert ManualTaskLogStatus.complete == "complete"
        assert ManualTaskLogStatus.error == "error"
        assert ManualTaskLogStatus.retrying == "retrying"
        assert ManualTaskLogStatus.paused == "paused"
        assert ManualTaskLogStatus.awaiting_input == "awaiting_input"
        # Test invalid value
        with pytest.raises(ValueError):
            ManualTaskLogStatus("invalid_status")


class TestManualTaskLogCreate:
    """Tests for ManualTaskLogCreate schema."""

    def test_create_log_minimal(self):
        """Test creating a log with minimal required fields."""
        log = ManualTaskLogCreate(
            task_id="test-task",
            status=ManualTaskLogStatus.created,
        )
        assert log.task_id == "test-task"
        assert log.status == ManualTaskLogStatus.created
        assert log.message is None
        assert log.details is None
        assert log.config_id is None
        assert log.instance_id is None

    def test_create_log_full(self):
        """Test creating a log with all fields."""
        log = ManualTaskLogCreate(
            task_id="test-task",
            status=ManualTaskLogStatus.complete,
            message="Test message",
            details={"key": "value"},
            config_id="test-config",
            instance_id="test-instance",
        )
        assert log.task_id == "test-task"
        assert log.status == ManualTaskLogStatus.complete
        assert log.message == "Test message"
        assert log.details == {"key": "value"}
        assert log.config_id == "test-config"
        assert log.instance_id == "test-instance"

    def test_create_log_invalid_status(self):
        """Test creating a log with invalid status."""
        with pytest.raises(ValidationError) as exc_info:
            ManualTaskLogCreate(
                task_id="test-task",
                status="invalid_status",
            )
        assert "status" in str(exc_info.value)

    def test_create_log_extra_fields(self):
        """Test that extra fields are forbidden."""
        with pytest.raises(ValidationError) as exc_info:
            ManualTaskLogCreate(
                task_id="test-task",
                status=ManualTaskLogStatus.created,
                extra_field="should fail",
            )
        assert "extra_field" in str(exc_info.value)


class TestManualTaskLogResponse:
    """Tests for ManualTaskLogResponse schema."""

    def test_log_response_minimal(self):
        """Test creating a response with minimal required fields."""
        now = datetime.now(timezone.utc)
        log = ManualTaskLogResponse(
            id="test-id",
            task_id="test-task",
            status=ManualTaskLogStatus.created,
            created_at=now,
            updated_at=now,
        )
        assert log.id == "test-id"
        assert log.task_id == "test-task"
        assert log.status == ManualTaskLogStatus.created
        assert log.message is None
        assert log.details is None
        assert log.config_id is None
        assert log.instance_id is None
        assert log.created_at == now
        assert log.updated_at == now

    def test_log_response_full(self):
        """Test creating a response with all fields."""
        now = datetime.now(timezone.utc)
        log = ManualTaskLogResponse(
            id="test-id",
            task_id="test-task",
            status=ManualTaskLogStatus.complete,
            message="Test message",
            details={"key": "value"},
            config_id="test-config",
            instance_id="test-instance",
            created_at=now,
            updated_at=now,
        )
        assert log.id == "test-id"
        assert log.task_id == "test-task"
        assert log.status == ManualTaskLogStatus.complete
        assert log.message == "Test message"
        assert log.details == {"key": "value"}
        assert log.config_id == "test-config"
        assert log.instance_id == "test-instance"
        assert log.created_at == now
        assert log.updated_at == now

    def test_log_response_invalid_status(self):
        """Test creating a response with invalid status."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError) as exc_info:
            ManualTaskLogResponse(
                id="test-id",
                task_id="test-task",
                status="invalid_status",
                created_at=now,
                updated_at=now,
            )
        assert "status" in str(exc_info.value)

    def test_log_response_extra_fields(self):
        """Test that extra fields are forbidden."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError) as exc_info:
            ManualTaskLogResponse(
                id="test-id",
                task_id="test-task",
                status=ManualTaskLogStatus.created,
                created_at=now,
                updated_at=now,
                extra_field="should fail",
            )
        assert "extra_field" in str(exc_info.value)

    def test_log_response_missing_required_fields(self):
        """Test that required fields cannot be missing."""
        with pytest.raises(ValidationError) as exc_info:
            ManualTaskLogResponse(
                id="test-id",
                task_id="test-task",
                status=ManualTaskLogStatus.created,
                # Missing created_at and updated_at
            )
        assert "created_at" in str(exc_info.value)
        assert "updated_at" in str(exc_info.value)
