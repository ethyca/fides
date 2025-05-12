import time

import pytest
from sqlalchemy.orm import Session

from fides.api.models.privacy_request import ExecutionLog
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import ExecutionLogStatus


def test_execution_log_timestamps(db: Session):
    """
    Most models use the timestamp from when the session was opened.
    We need to use the timestamp from when the models were created.
    """

    delay = 5

    first_log = ExecutionLog.create(
        db=db,
        data={
            "connection_key": "my-postgres-db-key",
            "dataset_name": "my-postgres-db",
            "collection_name": "test_collection_1",
            "fields_affected": [],
            "action_type": ActionType.access,
            "status": ExecutionLogStatus.in_processing,
            "privacy_request_id": "123",
        },
    )

    time.sleep(delay)

    second_log = ExecutionLog.create(
        db=db,
        data={
            "connection_key": "my-postgres-db-key",
            "dataset_name": "my-postgres-db",
            "collection_name": "test_collection_2",
            "fields_affected": [],
            "action_type": ActionType.access,
            "status": ExecutionLogStatus.complete,
            "privacy_request_id": "123",
        },
    )

    assert (
        second_log.created_at - first_log.created_at
    ).total_seconds() == pytest.approx(delay, abs=0.1)
