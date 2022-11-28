import logging
from typing import Dict, Generator, List, Tuple
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from fides.api.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.ops.models.datasetconfig import DatasetConfig
from fides.api.ops.service.connectors import FidesConnector
from fides.ctl.core.config import get_config

logger = logging.getLogger(__name__)

CONFIG = get_config()

from .application_fixtures import integration_secrets


@pytest.fixture(scope="function")
def fides_connector_example_secrets():
    return integration_secrets["fides_example"]


@pytest.fixture(scope="function")
def fides_connector_polling_overrides():
    return (200, 20)


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
def test_fides_connector_overriden_polling(
    fides_connector_connection_config: Dict[str, str],
    fides_connector_polling_overrides: Tuple[int, int],
) -> FidesConnector:
    fides_connector_connection_config.secrets[
        "polling_retries"
    ] = fides_connector_polling_overrides[0]
    fides_connector_connection_config.secrets[
        "polling_interval"
    ] = fides_connector_polling_overrides[1]
    return FidesConnector(configuration=fides_connector_connection_config)


@pytest.fixture
def fides_connector_example_test_dataset_config(
    connection_config: ConnectionConfig,
    db: Session,
    example_datasets: List[Dict],
) -> Generator:
    fides_connector_dataset = example_datasets[10]
    fides_key = fides_connector_dataset["fides_key"]
    connection_config.name = fides_key
    connection_config.key = fides_key
    connection_config.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": fides_key,
            "dataset": fides_connector_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)
