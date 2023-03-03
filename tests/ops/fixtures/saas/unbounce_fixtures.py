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

secrets = get_secrets("unbounce")


@pytest.fixture(scope="session")
def unbounce_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "unbounce.domain") or secrets["domain"],
        "lead_id": pydash.get(saas_config, "unbounce.lead_id") or secrets["lead_id"],
        "api_key": pydash.get(saas_config, "unbounce.api_key") or secrets["api_key"],
    }


@pytest.fixture(scope="session")
def unbounce_identity_email(saas_config):
    return (
        pydash.get(saas_config, "unbounce.identity_email") or secrets["identity_email"]
    )


@pytest.fixture(scope="function")
def unbounce_erasure_identity_email() -> str:
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture
def unbounce_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/unbounce_config.yml",
        "<instance_fides_key>",
        "unbounce_instance",
    )


@pytest.fixture
def unbounce_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/unbounce_dataset.yml",
        "<instance_fides_key>",
        "unbounce_instance",
    )[0]


@pytest.fixture(scope="function")
def unbounce_connection_config(
    db: Session, unbounce_config, unbounce_secrets
) -> Generator:
    fides_key = unbounce_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": unbounce_secrets,
            "saas_config": unbounce_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def unbounce_dataset_config(
    db: Session,
    unbounce_connection_config: ConnectionConfig,
    unbounce_dataset: Dict[str, Any],
) -> Generator:
    fides_key = unbounce_dataset["fides_key"]
    unbounce_connection_config.name = fides_key
    unbounce_connection_config.key = fides_key
    unbounce_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, unbounce_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": unbounce_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture(scope="function")
def unbounce_create_erasure_data(
    unbounce_connection_config: ConnectionConfig, unbounce_erasure_identity_email: str
) -> None:

    sleep(60)

    unbounce_secrets = unbounce_connection_config.secrets
    auth = unbounce_secrets["username"], unbounce_secrets["api_key"]
    base_url = f"https://{unbounce_secrets['domain']}"

    # user
    body = {
        "user": {
            "name": "Ethyca Test Erasure",
            "email": unbounce_erasure_identity_email,
            "verified": "true",
        }
    }

    users_response = requests.post(url=f"{base_url}/api/v2/users", auth=auth, json=body)
    user = users_response.json()["user"]
    user_id = user["id"]

    # ticket
    ticket_data = {
        "ticket": {
            "comment": {"body": "Test Comment"},
            "priority": "urgent",
            "subject": "Test Ticket",
            "requester_id": user_id,
            "submitter_id": user_id,
            "description": "Test Description",
        }
    }
    response = requests.post(
        url=f"{base_url}/api/v2/tickets", auth=auth, json=ticket_data
    )
    ticket = response.json()["ticket"]
    ticket_id = ticket["id"]
    yield ticket, user
