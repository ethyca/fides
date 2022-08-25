from typing import Any, Dict, Generator

import pydash
import pytest
import requests
from fideslib.cryptography import cryptographic_util
from sqlalchemy.orm import Session

from fidesops.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fidesops.ops.models.datasetconfig import DatasetConfig
from fidesops.ops.util.saas_util import (
    load_config_with_replacement,
    load_dataset_with_replacement,
)
from tests.ops.test_helpers.saas_test_utils import poll_for_existence
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("hubspot")


@pytest.fixture(scope="session")
def hubspot_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "hubspot.domain") or secrets["domain"],
        "private_app_token": pydash.get(saas_config, "hubspot.private_app_token")
        or secrets["private_app_token"],
    }


@pytest.fixture(scope="function")
def hubspot_identity_email(saas_config):
    return (
        pydash.get(saas_config, "hubspot.identity_email") or secrets["identity_email"]
    )


@pytest.fixture(scope="session")
def hubspot_erasure_identity_email():
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture
def hubspot_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/hubspot_config.yml",
        "<instance_fides_key>",
        "hubspot_instance",
    )


@pytest.fixture
def hubspot_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/hubspot_dataset.yml",
        "<instance_fides_key>",
        "hubspot_instance",
    )[0]


@pytest.fixture(scope="function")
def connection_config_hubspot(
    db: Session,
    hubspot_config,
    hubspot_secrets,
) -> Generator:
    fides_key = hubspot_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": hubspot_secrets,
            "saas_config": hubspot_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def dataset_config_hubspot(
    db: Session,
    connection_config_hubspot: ConnectionConfig,
    hubspot_dataset,
    hubspot_config,
) -> Generator:
    fides_key = hubspot_config["fides_key"]
    connection_config_hubspot.name = fides_key
    connection_config_hubspot.key = fides_key
    connection_config_hubspot.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config_hubspot.id,
            "fides_key": fides_key,
            "dataset": hubspot_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)


class HubspotTestClient:

    headers: object = {}
    base_url: str = ""

    def __init__(self, connection_config_hubspot: ConnectionConfig):
        hubspot_secrets = connection_config_hubspot.secrets
        self.headers = {
            "Authorization": f"Bearer {hubspot_secrets['private_app_token']}",
        }
        self.base_url = f"https://{hubspot_secrets['domain']}"

    def get_user(self, user_id: str) -> requests.Response:
        user_response: requests.Response = requests.get(
            url=f"{self.base_url}/settings/v3/users/{user_id}", headers=self.headers
        )
        return user_response

    def get_contact(self, contact_id: str) -> requests.Response:
        contact_response: requests.Response = requests.get(
            url=f"{self.base_url}/crm/v3/objects/contacts/{contact_id}",
            headers=self.headers,
        )
        return contact_response

    def get_contact_by_email(self, email: str) -> requests.Response:
        body = {
            "filterGroups": [
                {
                    "filters": [
                        {
                            "value": email,
                            "propertyName": "email",
                            "operator": "EQ",
                        }
                    ]
                }
            ]
        }
        contact_search_response: requests.Response = requests.post(
            url=f"{self.base_url}/crm/v3/objects/contacts/search",
            json=body,
            headers=self.headers,
        )
        return contact_search_response

    def create_contact(self, email: str) -> requests.Response:
        contacts_request_body = {
            "properties": {
                "company": "test company",
                "email": email,
                "firstname": "SomeoneFirstname",
                "lastname": "SomeoneLastname",
                "phone": "(123) 123-1234",
                "website": "someone.net",
            }
        }
        contact_response: requests.Response = requests.post(
            url=f"{self.base_url}/crm/v3/objects/contacts",
            headers=self.headers,
            json=contacts_request_body,
        )
        return contact_response

    def create_user(self, email: str) -> requests.Response:
        users_request_body = {
            "email": email,
        }
        user_response: requests.Response = requests.post(
            url=f"{self.base_url}/settings/v3/users/",
            headers=self.headers,
            json=users_request_body,
        )
        return user_response

    def delete_contact(self, contact_id: str) -> requests.Response:
        contact_response: requests.Response = requests.delete(
            url=f"{self.base_url}/crm/v3/objects/contacts/{contact_id}",
            headers=self.headers,
        )
        return contact_response

    def get_email_subscriptions(self, email: str) -> requests.Response:
        email_subscriptions: requests.Response = requests.get(
            url=f"{self.base_url}/communication-preferences/v3/status/email/{email}",
            headers=self.headers,
        )
        return email_subscriptions


@pytest.fixture(scope="function")
def hubspot_test_client(
    connection_config_hubspot: HubspotTestClient,
) -> Generator:
    test_client = HubspotTestClient(connection_config_hubspot=connection_config_hubspot)
    yield test_client


def _contact_exists(
    contact_id: str, email: str, hubspot_test_client: HubspotTestClient
) -> Any:
    """
    Confirm whether contact exists. We check the crm search endpoint as this is
    what our connectors use.
    """
    contact_response = hubspot_test_client.get_contact(contact_id=contact_id)
    contact_search_response = hubspot_test_client.get_contact_by_email(email=email)

    if (
        not contact_response.status_code == 404
        and contact_search_response.json()["results"]
    ):
        contact_body = contact_response.json()
        return contact_body


def user_exists(user_id: str, hubspot_test_client: HubspotTestClient) -> Any:
    """
    Confirm whether user exists
    """
    user_response: requests.Response = hubspot_test_client.get_user(user_id=user_id)
    if not user_response.status_code == 404:
        user_body = user_response.json()
        return user_body


@pytest.fixture(scope="function")
def hubspot_erasure_data(
    hubspot_test_client: HubspotTestClient,
    hubspot_erasure_identity_email: str,
) -> Generator:
    """
    Gets the current value of the resource and restores it after the test is complete.
    Used for erasure tests.
    """
    # create contact
    contacts_response = hubspot_test_client.create_contact(
        email=hubspot_erasure_identity_email
    )
    contacts_body = contacts_response.json()
    contact_id = contacts_body["id"]

    # create user
    users_response = hubspot_test_client.create_user(
        email=hubspot_erasure_identity_email
    )
    users_body = users_response.json()
    user_id = users_body["id"]

    # no need to subscribe contact, since creating a contact auto-subscribes them
    # Allows contact to be propagated in Hubspot before calling access / erasure requests
    error_message = (
        f"Contact with contact id {contact_id} could not be added to Hubspot"
    )
    poll_for_existence(
        _contact_exists,
        (contact_id, hubspot_erasure_identity_email, hubspot_test_client),
        error_message=error_message,
    )

    error_message = f"User with user id {user_id} could not be added to Hubspot"
    poll_for_existence(
        user_exists,
        (user_id, hubspot_test_client),
        error_message=error_message,
    )

    yield contact_id, user_id

    # delete contact
    hubspot_test_client.delete_contact(contact_id=contact_id)

    # verify contact is deleted
    error_message = (
        f"Contact with contact id {contact_id} could not be deleted from Hubspot"
    )
    poll_for_existence(
        _contact_exists,
        (contact_id, hubspot_erasure_identity_email, hubspot_test_client),
        error_message=error_message,
        existence_desired=False,
    )
