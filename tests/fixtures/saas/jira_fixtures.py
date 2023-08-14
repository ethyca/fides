from time import sleep
from typing import Any, Dict, Generator

import pydash
import pytest
import requests
from requests.auth import HTTPBasicAuth
from sqlalchemy.orm import Session

from fides.api.cryptography import cryptographic_util
from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.sql_models import Dataset as CtlDataset
from fides.api.util.saas_util import (
    load_config_with_replacement,
    load_dataset_with_replacement,
)
from tests.ops.test_helpers.saas_test_utils import poll_for_existence
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("jira")


@pytest.fixture(scope="session")
def jira_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "jira.domain") or secrets["domain"],
        "username": pydash.get(saas_config, "jira.username") or secrets["username"],
        "api_key": pydash.get(saas_config, "jira.api_key") or secrets["api_key"],
    }


@pytest.fixture(scope="session")
def jira_identity_email(saas_config):
    return pydash.get(saas_config, "jira.identity_email") or secrets["identity_email"]


@pytest.fixture(scope="session")
def jira_identity_phone_number(saas_config):
    return (
        pydash.get(saas_config, "jira.identity_phone_number")
        or secrets["identity_phone_number"]
    )


@pytest.fixture(scope="function")
def jira_erasure_identity_email() -> str:
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture
def jira_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/jira_config.yml",
        "<instance_fides_key>",
        "jira_instance",
    )


@pytest.fixture
def jira_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/jira_dataset.yml",
        "<instance_fides_key>",
        "jira_instance",
    )[0]


@pytest.fixture(scope="function")
def jira_connection_config(db: Session, jira_config, jira_secrets) -> Generator:
    fides_key = jira_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": jira_secrets,
            "saas_config": jira_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def jira_dataset_config(
    db: Session,
    jira_connection_config: ConnectionConfig,
    jira_dataset: Dict[str, Any],
) -> Generator:
    fides_key = jira_dataset["fides_key"]
    jira_connection_config.name = fides_key
    jira_connection_config.key = fides_key
    jira_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, jira_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": jira_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture(scope="function")
def jira_create_erasure_data(
    jira_connection_config: ConnectionConfig, jira_erasure_identity_email: str
) -> None:
    jira_secrets = jira_connection_config.secrets
    base_url = f"https://{jira_secrets['domain']}"

    # user
    body = {
        "name": "Ethyca Test Erasure",
        "emailAddress": jira_erasure_identity_email,
    }

    users_response = requests.post(
        url=f"{base_url}/rest/api/3/user",
        json=body,
        auth=(jira_secrets["username"], jira_secrets["api_key"]),
    )
    user = users_response.json()

    sleep(30)

    yield user
