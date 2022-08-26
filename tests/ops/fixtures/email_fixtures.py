from typing import Dict, Generator, List
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from fidesops.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fidesops.ops.models.datasetconfig import DatasetConfig


@pytest.fixture(scope="function")
def email_connection_config(db: Session) -> Generator:
    name = str(uuid4())
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": name,
            "key": "my_email_connection_config",
            "connection_type": ConnectionType.email,
            "access": AccessLevel.read,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def email_dataset_config(
    email_connection_config: ConnectionConfig,
    db: Session,
    example_datasets: List[Dict],
) -> Generator:
    email_dataset = example_datasets[9]
    fides_key = email_dataset["fides_key"]
    email_connection_config.name = fides_key
    email_connection_config.key = fides_key
    email_connection_config.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": email_connection_config.id,
            "fides_key": fides_key,
            "dataset": email_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)
