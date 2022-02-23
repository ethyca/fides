import pytest
import os
from fidesops.schemas.saas.saas_config import SaaSConfig
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
from tests.fixtures.application_fixtures import load_dataset


saas_config = load_toml("saas_config.toml")

saas_secrets_dict = {
    "mailchimp": {
        "domain": pydash.get(saas_config, "mailchimp.domain")
        or os.environ.get("MAILCHIMP_DOMAIN"),
        "username": pydash.get(saas_config, "mailchimp.username")
        or os.environ.get("MAILCHIMP_USERNAME"),
        "api_key": pydash.get(saas_config, "mailchimp.api_key")
        or os.environ.get("MAILCHIMP_API_KEY"),
    }
}

def load_config(filename: str) -> Dict:
    yaml_file = load_file(filename)
    with open(yaml_file, "r") as file:
        return yaml.safe_load(file).get("saas_config", [])


@pytest.fixture
def example_saas_configs() -> Dict[str, Dict]:
    example_saas_configs = {}
    example_saas_configs["mailchimp"] = load_config(
        "data/saas/config/mailchimp_config.yml"
    )[0]
    return example_saas_configs


@pytest.fixture
def example_saas_datasets() -> Dict[str, Dict]:
    example_saas_datasets = {}
    example_saas_datasets["mailchimp"] = load_dataset(
        "data/saas/dataset/mailchimp_dataset.yml"
    )[0]
    return example_saas_datasets


@pytest.fixture
def dataset_config_saas(
    db: Session,
    connection_config_saas: ConnectionConfig,
    example_saas_datasets: Dict[str, Dict],
) -> Generator:
    saas_dataset = example_saas_datasets["mailchimp"]
    fides_key = saas_dataset["fides_key"]
    connection_config_saas.name = fides_key
    connection_config_saas.key = fides_key
    connection_config_saas.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config_saas.id,
            "fides_key": fides_key,
            "dataset": saas_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)


@pytest.fixture(scope="function")
def connection_config_saas(
    db: Session,
    example_saas_configs: Dict[str, Dict],
) -> Generator:
    saas_config = SaaSConfig(**example_saas_configs["mailchimp"])
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": saas_config.fides_key,
            "name": saas_config.fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.read,
            "secrets": saas_secrets_dict["mailchimp"],
            "saas_config": example_saas_configs["mailchimp"],
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def saas_secrets():
    return saas_secrets_dict["mailchimp"]


@pytest.fixture(scope="function")
def mailchimp_account_email():
    return pydash.get(saas_config, "mailchimp.account_email") or os.environ.get(
        "MAILCHIMP_ACCOUNT_EMAIL"
    )
