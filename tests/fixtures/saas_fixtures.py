import json
import pytest
import os
import pydash
import yaml

from sqlalchemy.orm import Session
from typing import Dict, Generator

from fidesops.core.config import load_file, load_toml
from fidesops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fidesops.models.datasetconfig import DatasetConfig
from fidesops.schemas.saas.saas_config import SaaSConfig
from fidesops.schemas.saas.shared_schemas import HTTPMethod, SaaSRequestParams
from fidesops.service.connectors.saas_connector import SaaSConnector
from tests.fixtures.application_fixtures import load_dataset


saas_config = load_toml("saas_config.toml")

saas_secrets_dict = {
    "saas_example": {
        "domain": pydash.get(saas_config, "saas_example.domain"),
        "username": pydash.get(saas_config, "saas_example.username"),
        "api_key": pydash.get(saas_config, "saas_example.api_key"),
        "api_version": pydash.get(saas_config, "saas_example.api_version"),
        "page_limit": pydash.get(saas_config, "saas_example.page_limit")
    },
    "mailchimp": {
        "domain": pydash.get(saas_config, "mailchimp.domain")
        or os.environ.get("MAILCHIMP_DOMAIN"),
        "username": pydash.get(saas_config, "mailchimp.username")
        or os.environ.get("MAILCHIMP_USERNAME"),
        "api_key": pydash.get(saas_config, "mailchimp.api_key")
        or os.environ.get("MAILCHIMP_API_KEY"),
    },
}


def load_config(filename: str) -> Dict:
    yaml_file = load_file(filename)
    with open(yaml_file, "r") as file:
        return yaml.safe_load(file).get("saas_config", [])


@pytest.fixture
def saas_configs() -> Dict[str, Dict]:
    saas_configs = {}
    saas_configs["saas_example"] = load_config(
        "data/saas/config/saas_example_config.yml"
    )
    saas_configs["mailchimp"] = load_config("data/saas/config/mailchimp_config.yml")
    return saas_configs


@pytest.fixture
def saas_datasets() -> Dict[str, Dict]:
    saas_datasets = {}
    saas_datasets["saas_example"] = load_dataset(
        "data/saas/dataset/saas_example_dataset.yml"
    )[0]
    saas_datasets["mailchimp"] = load_dataset(
        "data/saas/dataset/mailchimp_dataset.yml"
    )[0]
    return saas_datasets


@pytest.fixture(scope="function")
def connection_config_saas_example(
    db: Session,
    saas_configs: Dict[str, Dict],
) -> Generator:
    saas_config = SaaSConfig(**saas_configs["saas_example"])
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": saas_config.fides_key,
            "name": saas_config.fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": saas_secrets_dict["saas_example"],
            "saas_config": saas_configs["saas_example"],
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def dataset_config_saas_example(
    db: Session,
    connection_config_saas_example: ConnectionConfig,
    saas_datasets: Dict[str, Dict],
) -> Generator:
    saas_dataset = saas_datasets["saas_example"]
    fides_key = saas_dataset["fides_key"]
    connection_config_saas_example.name = fides_key
    connection_config_saas_example.key = fides_key
    connection_config_saas_example.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config_saas_example.id,
            "fides_key": fides_key,
            "dataset": saas_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)


@pytest.fixture(scope="function")
def connection_config_mailchimp(
    db: Session, saas_configs: Dict[str, Dict]
) -> Generator:
    saas_config = SaaSConfig(**saas_configs["mailchimp"])
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": saas_config.fides_key,
            "name": saas_config.fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": saas_secrets_dict["mailchimp"],
            "saas_config": saas_configs["mailchimp"],
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def dataset_config_mailchimp(
    db: Session,
    connection_config_mailchimp: ConnectionConfig,
    saas_datasets: Dict[str, Dict]
) -> Generator:
    saas_dataset = saas_datasets["mailchimp"]
    fides_key = saas_dataset["fides_key"]
    connection_config_mailchimp.name = fides_key
    connection_config_mailchimp.key = fides_key
    connection_config_mailchimp.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config_mailchimp.id,
            "fides_key": fides_key,
            "dataset": saas_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)


@pytest.fixture(scope="function")
def connection_config_saas_example_without_saas_config(
    db: Session,
) -> Generator:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": "connection_config_without_saas_config",
            "name": "connection_config_without_saas_config",
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.read,
            "secrets": saas_secrets_dict["saas_example"],
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def connection_config_saas_example_with_invalid_saas_config(
    db: Session, saas_configs: Dict[str, Dict]
) -> Generator:
    invalid_saas_config = saas_configs["saas_example"].copy()
    invalid_saas_config["endpoints"][0]["requests"]["read"]["param_values"].pop()
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": "connection_config_without_saas_config",
            "name": "connection_config_without_saas_config",
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.read,
            "secrets": saas_secrets_dict["saas_example"],
            "saas_config": invalid_saas_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def saas_secrets():
    return saas_secrets_dict


@pytest.fixture(scope="function")
def mailchimp_identity_email():
    return pydash.get(saas_config, "mailchimp.identity_email") or os.environ.get(
        "MAILCHIMP_IDENTITY_EMAIL"
    )


@pytest.fixture(scope="function")
def reset_mailchimp_data(
    connection_config_mailchimp, mailchimp_identity_email
) -> Generator:
    """
    Gets the current value of the resource and restores it after the test is complete.
    Used for erasure tests.
    """
    connector = SaaSConnector(connection_config_mailchimp)
    request: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.GET, path="/3.0/search-members", query_params={"query": mailchimp_identity_email}, body=None
    )
    response = connector.create_client().send(request)
    body = response.json()
    member = body["exact_matches"]["members"][0]
    yield member
    request: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.PUT,
        path=f'/3.0/lists/{member["list_id"]}/members/{member["id"]}',
        query_params={},
        body=json.dumps(member)
    )
    connector.create_client().send(request)
