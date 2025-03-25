from typing import Dict, Generator, List
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.policy import ActionType
from fides.api.models.privacy_request import ExecutionLog, PrivacyRequest
from fides.api.models.sql_models import Dataset as CtlDataset
from fides.api.schemas.privacy_request import ExecutionLogStatus

from .application_fixtures import integration_secrets


@pytest.fixture(scope="function")
def mongo_example_secrets():
    return integration_secrets["mongo_example"]


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


@pytest.fixture
def mongo_dataset_config(
    mongo_connection_config: ConnectionConfig,
    db: Session,
    example_datasets: List[Dict],
) -> Generator:
    mongo_dataset = example_datasets[1]
    fides_key = mongo_dataset["fides_key"]
    mongo_connection_config.name = fides_key
    mongo_connection_config.key = fides_key
    mongo_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, mongo_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": mongo_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


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
