from typing import Dict, Generator, List, Tuple
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from fides.api.ctl.sql_models import Dataset as CtlDataset
from fides.api.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.ops.models.datasetconfig import DatasetConfig
from fides.api.ops.service.connectors import FidesConnector

from .application_fixtures import integration_secrets


@pytest.fixture(scope="function")
def fides_connector_example_secrets():
    return integration_secrets["fides_example"]


@pytest.fixture(scope="function")
def fides_connector_polling_overrides():
    return (1000, 5)


@pytest.fixture(scope="function")
def fides_connector_connection_config(
    db: Session, fides_connector_example_secrets: Dict[str, str]
) -> Generator:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": str(uuid4()),
            "key": "fides_connector_connection_1",
            "connection_type": ConnectionType.fides,
            "access": AccessLevel.write,
            "secrets": fides_connector_example_secrets,
            "disabled": False,
            "description": "Mock fides connector connection",
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def test_fides_connector(
    fides_connector_connection_config: Dict[str, str],
) -> FidesConnector:
    return FidesConnector(configuration=fides_connector_connection_config)


@pytest.fixture(scope="function")
def test_fides_connector_overridden_polling(
    fides_connector_connection_config: Dict[str, str],
    fides_connector_polling_overrides: Tuple[int, int],
) -> FidesConnector:
    fides_connector_connection_config.secrets[
        "polling_timeout"
    ] = fides_connector_polling_overrides[0]
    fides_connector_connection_config.secrets[
        "polling_interval"
    ] = fides_connector_polling_overrides[1]
    return FidesConnector(configuration=fides_connector_connection_config)


@pytest.fixture(scope="function")
def fides_connector_example_test_dataset_config(
    fides_connector_connection_config: ConnectionConfig,
    db: Session,
    example_datasets: List[Dict],
) -> Generator:
    fides_connector_dataset = example_datasets[10]
    fides_key = fides_connector_dataset["fides_key"]
    fides_connector_connection_config.name = fides_key
    fides_connector_connection_config.key = fides_key
    fides_connector_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, fides_connector_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": fides_connector_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)
