from typing import Generator
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from fidesops.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fidesops.ops.models.policy import ActionType
from fidesops.ops.models.privacy_request import (
    ExecutionLog,
    ExecutionLogStatus,
    PrivacyRequest,
)

from .application_fixtures import integration_secrets


@pytest.fixture(scope="function")
def mongo_connection_config(db: Session) -> Generator:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": str(uuid4()),
            "key": "my_mongo_db_1",
            "connection_type": ConnectionType.mongodb,
            "access": AccessLevel.write,
            "secrets": integration_secrets["mongo_example"],
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def mongo_execution_log(
    db: Session,
    privacy_request: PrivacyRequest,
) -> ExecutionLog:
    el = ExecutionLog.create(
        db=db,
        data={
            "dataset_name": "my-mongo-db",
            "collection_name": "orders",
            "fields_affected": [
                {
                    "path": "my-mongo-db:orders:name",
                    "field_name": "name",
                    "data_categories": ["user.contact.name"],
                }
            ],
            "action_type": ActionType.access,
            "status": ExecutionLogStatus.in_processing,
            "privacy_request_id": privacy_request.id,
        },
    )
    yield el
    el.delete(db)
