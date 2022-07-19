from typing import Any, Dict, Generator

import pydash
import pytest
import requests
from fideslib.core.config import load_toml
from fideslib.cryptography import cryptographic_util
from fideslib.db import session
from sqlalchemy.orm import Session
from starlette.status import HTTP_202_ACCEPTED

from fidesops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fidesops.models.datasetconfig import DatasetConfig
from tests.fixtures.application_fixtures import load_dataset
from tests.fixtures.saas_example_fixtures import load_config
from tests.test_helpers.saas_test_utils import poll_for_existence
from tests.test_helpers.vault_client import get_secrets

saas_config = load_toml(["saas_config.toml"])
secrets = get_secrets("sendgrid")

SENDGRID_ERASURE_FIRSTNAME = "Erasurefirstname"


@pytest.fixture(scope="session")
def sendgrid_erasure_identity_email():
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture(scope="function")
def sendgrid_secrets():
    return {
        "domain": pydash.get(saas_config, "sendgrid.domain") or secrets["domain"],
        "api_key": pydash.get(saas_config, "sendgrid.api_key") or secrets["api_key"],
    }


@pytest.fixture(scope="function")
def sendgrid_identity_email():
    return (
        pydash.get(saas_config, "sendgrid.identity_email") or secrets["identity_email"]
    )


@pytest.fixture
def sendgrid_config() -> Dict[str, Any]:
    return load_config("data/saas/config/sendgrid_config.yml")


@pytest.fixture
def sendgrid_dataset() -> Dict[str, Any]:
    return load_dataset("data/saas/dataset/sendgrid_dataset.yml")[0]


@pytest.fixture(scope="function")
def sendgrid_connection_config(
    db: session, sendgrid_config, sendgrid_secrets
) -> Generator:
    fides_key = sendgrid_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": sendgrid_secrets,
            "saas_config": sendgrid_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def sendgrid_dataset_config(
    db: Session,
    sendgrid_connection_config: ConnectionConfig,
    sendgrid_dataset: Dict[str, Any],
) -> Generator:
    fides_key = sendgrid_dataset["fides_key"]
    sendgrid_connection_config.name = fides_key
    sendgrid_connection_config.key = fides_key
    sendgrid_connection_config.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": sendgrid_connection_config.id,
            "fides_key": fides_key,
            "dataset": sendgrid_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)


@pytest.fixture(scope="function")
def sendgrid_erasure_data(
    sendgrid_connection_config, sendgrid_erasure_identity_email, sendgrid_secrets
) -> Generator:
    """
    Creates a dynamic test data record for erasure tests.
    Yields contact ID as this may be useful to have in test scenarios
    """

    base_url = f"https://{sendgrid_secrets['domain']}"
    # Create contact
    body = {
        "list_ids": ["62d20902-1cdd-42e7-8d5d-0fbb2a8be13e"],
        "contacts": [
            {
                "address_line_1": "address_line_1",
                "address_line_2": "address_line_2",
                "city": "CITY (optional)",
                "country": "country (optional)",
                "email": sendgrid_erasure_identity_email,
                "first_name": SENDGRID_ERASURE_FIRSTNAME,
                "last_name": "Testcontact",
                "postal_code": "postal_code (optional)",
                "state_province_region": "state (optional)",
                "custom_fields": {},
            }
        ],
    }
    headers = {"Authorization": f"Bearer {sendgrid_secrets['api_key']}"}
    contacts_response = requests.put(
        url=f"{base_url}/v3/marketing/contacts", json=body, headers=headers
    )
    assert HTTP_202_ACCEPTED == contacts_response.status_code
    error_message = f"Contact with email {sendgrid_erasure_identity_email} could not be added to Sendgrid"
    contact = poll_for_existence(
        contact_exists,
        (sendgrid_erasure_identity_email, sendgrid_secrets),
        error_message=error_message,
    )
    yield contact


def contact_exists(sendgrid_erasure_identity_email: str, sendgrid_secrets):
    """
    Confirm whether contact exists by calling contact search by email api and comparing resulting firstname str.
    Returns contact ID if it exists, returns None if it does not.
    """
    base_url = f"https://{sendgrid_secrets['domain']}"
    body = {"emails": [sendgrid_erasure_identity_email]}
    headers = {
        "Authorization": f"Bearer {sendgrid_secrets['api_key']}",
    }

    contact_response = requests.post(
        url=f"{base_url}/v3/marketing/contacts/search/emails",
        headers=headers,
        json=body,
    )
    # we expect 404 if contact doesn't exist
    if 404 == contact_response.status_code:
        return None

    return contact_response.json()["result"][sendgrid_erasure_identity_email]["contact"]
