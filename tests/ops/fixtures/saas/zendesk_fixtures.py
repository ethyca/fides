from typing import Any, Dict, Generator

import pydash
import pytest
import requests
from fideslib.cryptography import cryptographic_util
from fidesops.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fidesops.ops.models.datasetconfig import DatasetConfig
from fidesops.ops.util.saas_util import load_config
from sqlalchemy.orm import Session

from tests.ops.fixtures.application_fixtures import load_dataset
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("zendesk")


@pytest.fixture(scope="session")
def zendesk_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "zendesk.domain") or secrets["domain"],
        "username": pydash.get(saas_config, "zendesk.username") or secrets["username"],
        "api_key": pydash.get(saas_config, "zendesk.api_key") or secrets["api_key"],
    }


@pytest.fixture(scope="session")
def zendesk_identity_email(saas_config):
    return (
        pydash.get(saas_config, "zendesk.identity_email") or secrets["identity_email"]
    )


@pytest.fixture(scope="function")
def zendesk_erasure_identity_email() -> str:
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture
def zendesk_config() -> Dict[str, Any]:
    return load_config("data/saas/config/zendesk_config.yml")


@pytest.fixture
def zendesk_dataset() -> Dict[str, Any]:
    return load_dataset("data/saas/dataset/zendesk_dataset.yml")[0]


@pytest.fixture(scope="function")
def zendesk_connection_config(
    db: Session, zendesk_config, zendesk_secrets
) -> Generator:
    fides_key = zendesk_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": zendesk_secrets,
            "saas_config": zendesk_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def zendesk_dataset_config(
    db: Session,
    zendesk_connection_config: ConnectionConfig,
    zendesk_dataset: Dict[str, Any],
) -> Generator:
    fides_key = zendesk_dataset["fides_key"]
    zendesk_connection_config.name = fides_key
    zendesk_connection_config.key = fides_key
    zendesk_connection_config.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": zendesk_connection_config.id,
            "fides_key": fides_key,
            "dataset": zendesk_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)


@pytest.fixture(scope="function")
def zendesk_create_erasure_data(
    zendesk_connection_config: ConnectionConfig, zendesk_erasure_identity_email: str
) -> None:

    zendesk_secrets = zendesk_connection_config.secrets
    auth = zendesk_secrets["username"], zendesk_secrets["api_key"]
    base_url = f"https://{zendesk_secrets['domain']}"

    # user
    body = {
        "user": {
            "name": "Ethyca Test Erasure",
            "email": zendesk_erasure_identity_email,
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
