from fidesops.core.config import load_toml
from fidesops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fidesops.models.datasetconfig import DatasetConfig
import pytest
import pydash
import os
from typing import Any, Dict, Generator
from tests.fixtures.application_fixtures import load_dataset
from tests.fixtures.saas_example_fixtures import load_config
from sqlalchemy.orm import Session


saas_config = load_toml("saas_config.toml")


@pytest.fixture(scope="function")
def hubspot_secrets():
    return {
        "domain": pydash.get(saas_config, "hubspot.domain")
                  or os.environ.get("HUBSPOT_DOMAIN"),
        "hapikey": pydash.get(saas_config, "hubspot.hapikey")
                   or os.environ.get("HUBSPOT_HAPIKEY"),
    }


@pytest.fixture(scope="function")
def hubspot_identity_email():
    return pydash.get(saas_config, "hubspot.identity_email") or os.environ.get(
        "HUBSPOT_IDENTITY_EMAIL"
    )


@pytest.fixture
def hubspot_config() -> Dict[str, Any]:
    return load_config("data/saas/config/hubspot_config.yml")


@pytest.fixture
def hubspot_dataset() -> Dict[str, Any]:
    return load_dataset("data/saas/dataset/hubspot_dataset.yml")[0]


@pytest.fixture(scope="function")
def connection_config_hubspot(
        db: Session, hubspot_config, hubspot_secrets,
) -> Generator:
    fides_key = hubspot_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": hubspot_secrets,
            "saas_config": hubspot_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def dataset_config_hubspot(
        db: Session,
        connection_config_hubspot: ConnectionConfig,
        hubspot_dataset,
        hubspot_config,
) -> Generator:
    fides_key = hubspot_config["fides_key"]
    connection_config_hubspot.name = fides_key
    connection_config_hubspot.key = fides_key
    connection_config_hubspot.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config_hubspot.id,
            "fides_key": fides_key,
            "dataset": hubspot_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)
