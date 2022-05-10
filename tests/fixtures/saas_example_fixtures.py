import pytest
import pydash
import yaml

from sqlalchemy.orm import Session
from typing import Any, Dict, Generator

from fidesops.core.config import load_file, load_toml
from fidesops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fidesops.models.datasetconfig import DatasetConfig
from tests.fixtures.application_fixtures import load_dataset


def load_config(filename: str) -> Dict:
    yaml_file = load_file(filename)
    with open(yaml_file, "r") as file:
        return yaml.safe_load(file).get("saas_config", [])


saas_config = load_toml("saas_config.toml")


@pytest.fixture(scope="function")
def saas_example_secrets():
    return {
        "domain": pydash.get(saas_config, "saas_example.domain"),
        "username": pydash.get(saas_config, "saas_example.username"),
        "api_key": pydash.get(saas_config, "saas_example.api_key"),
        "api_version": pydash.get(saas_config, "saas_example.api_version"),
        "page_limit": pydash.get(saas_config, "saas_example.page_limit"),
    }


@pytest.fixture
def saas_example_config() -> Dict:
    return load_config("data/saas/config/saas_example_config.yml")


@pytest.fixture
def saas_example_dataset() -> Dict:
    return load_dataset("data/saas/dataset/saas_example_dataset.yml")[0]


@pytest.fixture(scope="function")
def saas_example_connection_config(
    db: Session,
    saas_example_config: Dict[str, Any],
    saas_example_secrets: Dict[str, Any],
) -> Generator:
    fides_key = saas_example_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": saas_example_secrets,
            "saas_config": saas_example_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def saas_example_dataset_config(
    db: Session,
    saas_example_connection_config: ConnectionConfig,
    saas_example_dataset: Dict,
) -> Generator:
    fides_key = saas_example_dataset["fides_key"]
    saas_example_connection_config.name = fides_key
    saas_example_connection_config.key = fides_key
    saas_example_connection_config.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": saas_example_connection_config.id,
            "fides_key": fides_key,
            "dataset": saas_example_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)


@pytest.fixture(scope="function")
def saas_example_connection_config_without_saas_config(
    db: Session, saas_example_secrets
) -> Generator:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": "connection_config_without_saas_config",
            "name": "connection_config_without_saas_config",
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.read,
            "secrets": saas_example_secrets,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def saas_example_connection_config_with_invalid_saas_config(
    db: Session,
    saas_example_config: Dict[str, Any],
    saas_example_secrets: Dict[str, Any],
) -> Generator:
    invalid_saas_config = saas_example_config.copy()
    invalid_saas_config["endpoints"][0]["requests"]["read"]["param_values"].pop()
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": "connection_config_with_invalid_saas_config",
            "name": "connection_config_with_invalid_saas_config",
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.read,
            "secrets": saas_example_secrets,
            "saas_config": invalid_saas_config,
        },
    )
    yield connection_config
    connection_config.delete(db)
