import pytest
from pytest import param
from sqlalchemy.exc import DataError, IntegrityError

from fides.api.models.privacy_request.execution_log import (
    COMPLETED_EXECUTION_LOG_STATUSES,
    EXITED_EXECUTION_LOG_STATUSES,
    ExecutionLog,
    can_run_checkpoint,
)
from fides.api.schemas.policy import ActionType, CurrentStep
from fides.api.schemas.privacy_request import ExecutionLogStatus


@pytest.fixture
def execution_log_data():
    return {
        "connection_key": "some_key",
        "dataset_name": "some_name",
        "collection_name": "some_collection",
        "fields_affected": ["field1", "field2"],
        "message": "test_message",
        "action_type": ActionType.access,
        "status": "complete",
        "privacy_request_id": "test_id",
    }


@pytest.mark.parametrize(
    "request_checkpoint,from_checkpoint,expected",
    [
        param(None, None, True, id="both_checkpoints_are_none"),
        param(CurrentStep.pre_webhooks, None, True, id="from_checkpoint_is_none"),
        param(
            CurrentStep.pre_webhooks,
            CurrentStep.pre_webhooks,
            True,
            id="from_checkpoint_is_same",
        ),
        param(
            CurrentStep.pre_webhooks,
            CurrentStep.access,
            False,
            id="from_checkpoint_is_before",
        ),
        param(
            CurrentStep.access,
            CurrentStep.pre_webhooks,
            True,
            id="from_checkpoint_is_after",
        ),
    ],
)
def test_can_run_checkpoint(request_checkpoint, from_checkpoint, expected):
    assert can_run_checkpoint(request_checkpoint, from_checkpoint) == expected


def test_create_execution_log(db, execution_log_data):
    execution_log = ExecutionLog.create(db, data=execution_log_data)

    retrieved_execution_log = (
        db.query(ExecutionLog).filter_by(privacy_request_id="test_id").first()
    )
    assert retrieved_execution_log is not None
    assert retrieved_execution_log.action_type == ActionType.access
    assert retrieved_execution_log.status == ExecutionLogStatus.complete
    assert retrieved_execution_log.connection_key == "some_key"
    assert retrieved_execution_log.dataset_name == "some_name"
    assert retrieved_execution_log.collection_name == "some_collection"
    assert retrieved_execution_log.fields_affected == ["field1", "field2"]
    assert retrieved_execution_log.message == "test_message"
    assert retrieved_execution_log.privacy_request_id == "test_id"
    assert retrieved_execution_log.created_at is not None
    assert retrieved_execution_log.updated_at is not None
    execution_log.delete(db)


def test_execution_log_missing_required_fields_errors(db):
    data = {
        "connection_key": "some_key",
        # Missing required fields like "privacy_request_id" and "action_type"
    }

    with pytest.raises(IntegrityError):
        ExecutionLog.create(db, data=data)


def test_execution_log_invalid_action_type_errors(db, execution_log_data):
    data = execution_log_data
    data["action_type"] = "invalid_action_type"  # Invalid action type

    with pytest.raises(DataError):
        ExecutionLog.create(db, data=data)


def test_execution_log_empty_optional_fields(db, execution_log_data):
    data = execution_log_data
    data["fields_affected"] = None
    data["message"] = None

    execution_log = ExecutionLog.create(db, data=data)

    retrieved_execution_log = (
        db.query(ExecutionLog).filter_by(privacy_request_id="test_id").first()
    )
    assert retrieved_execution_log is not None
    assert retrieved_execution_log.fields_affected is None
    assert retrieved_execution_log.message is None
    execution_log.delete(db)


def test_execution_log_large_data(db, execution_log_data):
    large_message = "a" * 10000  # Large string
    large_fields_affected = ["field" + str(i) for i in range(1000)]  # Large list

    data = execution_log_data
    data["fields_affected"] = large_fields_affected
    data["message"] = large_message

    execution_log = ExecutionLog.create(db, data=data)

    retrieved_execution_log = (
        db.query(ExecutionLog).filter_by(privacy_request_id="test_id").first()
    )
    assert retrieved_execution_log is not None
    assert retrieved_execution_log.message == large_message
    assert retrieved_execution_log.fields_affected == large_fields_affected
    execution_log.delete(db)
