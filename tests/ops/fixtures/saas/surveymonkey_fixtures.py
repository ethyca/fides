from typing import Any, Dict, Generator

import pydash
import pytest
import requests
from fideslib.cryptography import cryptographic_util
from fideslib.db import session
from requests import Response
from sqlalchemy.orm import Session
from faker import Faker

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
from tests.ops.test_helpers.saas_test_utils import poll_for_existence
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("surveymonkey")


@pytest.fixture(scope="function")
def surveymonkey_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "surveymonkey.domain") or secrets["domain"],
        "access_token": pydash.get(saas_config, "surveymonkey.access_token")
        or secrets["access_token"],
    }


@pytest.fixture(scope="function")
def surveymonkey_identity_email(saas_config):
    return (
        pydash.get(saas_config, "surveymonkey.identity_email")
        or secrets["identity_email"]
    )


@pytest.fixture(scope="session")
def surveymonkey_erasure_identity_email():
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture
def surveymonkey_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/surveymonkey_config.yml",
        "<instance_fides_key>",
        "surveymonkey_instance",
    )


@pytest.fixture
def surveymonkey_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/surveymonkey_dataset.yml",
        "<instance_fides_key>",
        "surveymonkey_instance",
    )[0]


@pytest.fixture(scope="function")
def surveymonkey_connection_config(
    db: session, surveymonkey_config, surveymonkey_secrets
) -> Generator:
    fides_key = surveymonkey_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": surveymonkey_secrets,
            "saas_config": surveymonkey_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def surveymonkey_dataset_config(
    db: Session,
    surveymonkey_connection_config: ConnectionConfig,
    surveymonkey_dataset: Dict[str, Any],
) -> Generator:
    fides_key = surveymonkey_dataset["fides_key"]
    surveymonkey_connection_config.name = fides_key
    surveymonkey_connection_config.key = fides_key
    surveymonkey_connection_config.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": surveymonkey_connection_config.id,
            "fides_key": fides_key,
            "dataset": surveymonkey_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)


class SurveymonkeyTestClient:
    """Helper to call various Surveymonkey data management requests"""

    def __init__(self, surveymonkey_connection_config: ConnectionConfig):
        self.surveymonkey_secrets = surveymonkey_connection_config.secrets
        auth_token = self.surveymonkey_secrets["access_token"]
        self.headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {auth_token}",
        }
        self.base_url = f"https://{self.surveymonkey_secrets['domain']}"

    def create_contact(self, email: str) -> Response:
        # create a new contact
        faker = Faker()
        body = {
            "first_name": faker.first_name(),
            "last_name": faker.last_name(),
            "email": email,
        }

        contact_response: Response = requests.post(
            url=f"{self.base_url}/v3/contacts", json=body, headers=self.headers
        )
        return contact_response

    def get_contact(self, contact_id: str) -> Response:
        # get contact created for erasure purposes
        url = f"{self.base_url}/v3/contacts/{contact_id}"
        contact_response: Response = requests.get(url=url, headers=self.headers)
        return contact_response

    def delete_contact(self, contact_id) -> Response:
        # delete contact created for erasure purposes
        url = f"{self.base_url}/v3/contacts/{contact_id}"
        contact_response: Response = requests.delete(url=url, headers=self.headers)
        return contact_response


@pytest.fixture(scope="function")
def surveymonkey_erasure_data(
    surveymonkey_test_client: SurveymonkeyTestClient,
    surveymonkey_erasure_identity_email: str,
) -> Generator:

    contact_response = surveymonkey_test_client.create_contact(
        email=surveymonkey_erasure_identity_email
    )
    contact = contact_response.json()

    contact_id = contact["id"]

    error_message = (
        f"Contact with contact id [{contact_id}] could not be added to SurveyMonkey"
    )
    poll_for_existence(
        _contact_exists,
        (contact_id, surveymonkey_test_client),
        error_message=error_message,
    )
    yield contact_id

    contact_response = surveymonkey_test_client.delete_contact(contact_id)
    # Returns a 200 response code when successful or error based on whether the Contact ID being valid.
    assert contact_response.ok


@pytest.fixture(scope="function")
def surveymonkey_test_client(
    surveymonkey_connection_config: SurveymonkeyTestClient,
) -> Generator:
    test_client = SurveymonkeyTestClient(
        surveymonkey_connection_config=surveymonkey_connection_config
    )
    yield test_client


def _contact_exists(
    contact_id: str, surveymonkey_test_client: SurveymonkeyTestClient
) -> Any:
    """check if the contact exists in the Surveymonkey"""
    contact_response = surveymonkey_test_client.get_contact(contact_id)
    contact = contact_response.json()
    # it return status 200 if contact exists with given id otherwise 400
    if contact_response.ok and contact:
        return contact
    return None
