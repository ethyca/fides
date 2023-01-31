from time import sleep
from typing import Any, Dict, Generator

import pydash
import pytest
import requests
from sqlalchemy.orm import Session

from fides.api.ctl.sql_models import Dataset as CtlDataset
from fides.api.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.ops.models.datasetconfig import DatasetConfig
from fides.api.ops.util.saas_util import (
    load_config_with_replacement,
    load_dataset_with_replacement,
)
from fides.lib.cryptography import cryptographic_util
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("delighted")


@pytest.fixture(scope="session")
def delighted_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "delighted.domain") or secrets["domain"],
        "username": pydash.get(saas_config, "delighted.username") or secrets["username"],
        "api_key": pydash.get(saas_config, "delighted.api_key") or secrets["api_key"],
    }


@pytest.fixture(scope="session")
def delighted_identity_email(saas_config):
    return (
        pydash.get(saas_config, "delighted.identity_email") or secrets["identity_email"]
    )


@pytest.fixture(scope="function")
def delighted_erasure_identity_email() -> str:
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture
def delighted_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/delighted_config.yml",
        "<instance_fides_key>",
        "delighted_instance",
    )


@pytest.fixture
def delighted_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/delighted_dataset.yml",
        "<instance_fides_key>",
        "delighted_instance",
    )[0]


@pytest.fixture(scope="function")
def delighted_connection_config(
    db: Session, delighted_config, delighted_secrets
) -> Generator:
    fides_key = delighted_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": delighted_secrets,
            "saas_config": delighted_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def delighted_dataset_config(
    db: Session,
    delighted_connection_config: ConnectionConfig,
    delighted_dataset: Dict[str, Any],
) -> Generator:
    fides_key = delighted_dataset["fides_key"]
    delighted_connection_config.name = fides_key
    delighted_connection_config.key = fides_key
    delighted_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, delighted_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": delighted_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture(scope="function")
def delighted_create_erasure_data(
    delighted_connection_config: ConnectionConfig, delighted_erasure_identity_email: str
) -> None:

    delighted_secrets = delighted_connection_config.secrets
    auth = delighted_secrets["username"], delighted_secrets["api_key"]
    base_url = f"https://{delighted_secrets['domain']}"

    # people
    body = {
        "name": "ethyca test erasure",
        "email": delighted_erasure_identity_email,
        "send": "false"
    }

    peoples_response = requests.post(url=f"{base_url}/v1/people", auth=auth, json=body)
    people = peoples_response.json()
    people_id = people["id"]

    # survey_response
    survey_response_data = {
        "person": people_id,
        "score": "3"
    }
    #need to add person info to body
    response = requests.post(
        url=f"{base_url}/v1/survey_responses.json", auth=auth, json=survey_response_data
    )

    sleep(60)

    survey_response = response.json()
    yield survey_response, peoples_response
