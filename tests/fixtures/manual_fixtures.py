from typing import Dict, Generator, List
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from fidesops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fidesops.models.datasetconfig import DatasetConfig


@pytest.fixture(scope="function")
def integration_manual_config(db) -> ConnectionConfig:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": str(uuid4()),
            "key": "manual_example",
            "connection_type": ConnectionType.manual,
            "access": AccessLevel.read,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def manual_dataset_config(
    integration_manual_config: ConnectionConfig,
    db: Session,
    example_datasets: List[Dict],
) -> Generator:
    manual_dataset = example_datasets[8]
    fides_key = manual_dataset["fides_key"]
    integration_manual_config.name = fides_key
    integration_manual_config.key = fides_key
    integration_manual_config.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": integration_manual_config.id,
            "fides_key": fides_key,
            "dataset": manual_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)
