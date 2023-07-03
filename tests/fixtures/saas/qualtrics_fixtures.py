from typing import Any, Dict, Generator
from time import sleep

import pydash
import pytest
import requests

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("qualtrics")


@pytest.fixture(scope="session")
def qualtrics_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "qualtrics.domain")
        or secrets["domain"],
        "api_key": pydash.get(saas_config, "qualtrics.api_key")
        or secrets["api_key"],
        "directory_id": pydash.get(saas_config, "qualtrics.directory_id")
        or secrets["directory_id"]
        # add the rest of your secrets here
    }


@pytest.fixture(scope="session")
def qualtrics_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "qualtrics.identity_email") or secrets["identity_email"]
    )


@pytest.fixture
def qualtrics_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def qualtrics_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def qualtrics_erasure_external_references() -> Dict[str, Any]:
    return {}


class QualtricsClient:
    def __init__(self, secrets: Dict[str, Any]):
        self.secrets = secrets
        self.base_url = f"https://{secrets['domain']}"
        self.headers = {
            "X-API-TOKEN": self.secrets['api_key'],
        }


    def create_directory_contact(self, email):
        return requests.post(
            url=f"{self.base_url}/API/v3/directories/{self.secrets['directory_id']}/contacts",
            headers=self.headers,
            json={
            "firstName": "Erasure test",
            "lastName": "test",
            "email": email,
            "phone": "111-111-1111",
            "extRef": "my_Internal_ID_12345",
            "embeddedData": {},
            "language": "",
            "unsubscribed": 'true'
        },
        )
    
    def get_directory_contacts(self, email: str):
        return requests.post(
            url=f"{self.base_url}/API/v3/directories/{self.secrets['directory_id']}/contacts/search",
            headers=self.headers,
            json={
                "filter": {"filterType": "email","comparison": "eq","value": email}
                },
        )


@pytest.fixture
def qualtrics_client(qualtrics_secrets) -> Generator:
    yield QualtricsClient(qualtrics_secrets)


@pytest.fixture
def qualtrics_erasure_data(
    qualtrics_client: QualtricsClient,
    qualtrics_erasure_identity_email: str, 
) -> Generator:

    # contact
    directory_contacts_response = qualtrics_client.create_directory_contact(
        qualtrics_erasure_identity_email
    )
    assert directory_contacts_response.ok
    contacts = directory_contacts_response.json()['result']
    contact_id = contacts["id"]
    sleep(60)
    yield contact_id


@pytest.fixture
def qualtrics_runner(
    db,
    cache,
    qualtrics_secrets,
    qualtrics_external_references,
    qualtrics_erasure_external_references,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "qualtrics",
        qualtrics_secrets,
        external_references=qualtrics_external_references,
        erasure_external_references=qualtrics_erasure_external_references,
    )