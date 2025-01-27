from time import sleep
from typing import Any, Dict, Generator

import pydash
import pytest
import requests

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
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


@pytest.fixture
def hubspot_identity_email():
    return generate_random_email()


class HubspotTestClient:
    headers: object = {}
    base_url: str = ""

    def __init__(self, hubspot_secrets: Dict[str, str]):
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

    def delete_user(self, user_id: str) -> requests.Response:
        user_response: requests.Response = requests.delete(
            url=f"{self.base_url}/settings/v3/users/{user_id}",
            headers=self.headers,
        )
        return user_response

    def opt_in_subscription_preferences(
        self, email: str, subscription_id: str
    ) -> requests.Response:
        body = {
            "emailAddress": f"{email}",
            "subscriptionId": f"{subscription_id}",
            "statusState": "SUBSCRIBED",
            "channel": "EMAIL",
            "legalBasis": "LEGITIMATE_INTEREST_CLIENT",
            "legalBasisExplanation": "At users request, we opted them in",
        }
        subscription_response: requests.Response = requests.post(
            url=f"{self.base_url}/communication-preferences/v4/statuses/{email}",
            headers=self.headers,
            json=body,
        )
        assert subscription_response.ok
        return subscription_response.json()

    def get_email_subscriptions(self, email: str) -> requests.Response:
        email_subscriptions: requests.Response = requests.get(
            url=f"{self.base_url}/communication-preferences/v4/statuses/{email}?channel=EMAIL",
            headers=self.headers,
        )
        return email_subscriptions

    def get_all_subscriptions(self) -> requests.Response:
        subscriptions_responses: requests.Response = requests.get(
            url=f"{self.base_url}/communication-preferences/v4/definitions",
            headers=self.headers,
        )
        return subscriptions_responses.json()


@pytest.fixture
def hubspot_test_client(
    hubspot_secrets,
) -> Generator:
    test_client = HubspotTestClient(hubspot_secrets)
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


def create_hubspot_data(test_client: HubspotTestClient, email):
    # create contact
    contacts_response = test_client.create_contact(email=email)
    contacts_body = contacts_response.json()
    contact_id = contacts_body["id"]

    # create user
    users_response = test_client.create_user(email=email)
    users_body = users_response.json()
    user_id = users_body["id"]

    # no need to subscribe contact, since creating a contact auto-subscribes them
    # Allows contact to be propagated in Hubspot before calling access / erasure requests
    error_message = (
        f"Contact with contact id {contact_id} could not be added to Hubspot"
    )
    poll_for_existence(
        _contact_exists,
        (contact_id, email, test_client),
        error_message=error_message,
        interval=60,
    )

    error_message = f"User with user id {user_id} could not be added to Hubspot"
    poll_for_existence(
        user_exists,
        (user_id, test_client),
        error_message=error_message,
    )
    subscriptions = test_client.get_all_subscriptions()
    for subscription in subscriptions["results"]:
        test_client.opt_in_subscription_preferences(
            email=email, subscription_id=subscription["id"]
        )
    sleep(3)
    return contact_id, user_id


@pytest.fixture
def hubspot_data(
    hubspot_test_client: HubspotTestClient,
    hubspot_identity_email: str,
) -> Generator:

    contact_id, user_id = create_hubspot_data(
        hubspot_test_client, email=hubspot_identity_email
    )
    random_email = generate_random_email()
    random_contact_id, random_user_id = create_hubspot_data(
        hubspot_test_client, email=random_email
    )

    yield contact_id, user_id

    # delete contact
    hubspot_test_client.delete_contact(contact_id=contact_id)
    hubspot_test_client.delete_user(user_id=user_id)

    # verify contact is deleted
    error_message = (
        f"Contact with contact id {contact_id} could not be deleted from Hubspot"
    )
    poll_for_existence(
        _contact_exists,
        (contact_id, hubspot_identity_email, hubspot_test_client),
        error_message=error_message,
        existence_desired=False,
    )

    # delete random contact
    hubspot_test_client.delete_contact(contact_id=random_contact_id)
    hubspot_test_client.delete_user(user_id=random_user_id)

    # verify random contact is deleted
    error_message = (
        f"Contact with contact id {random_contact_id} could not be deleted from Hubspot"
    )
    poll_for_existence(
        _contact_exists,
        (random_contact_id, random_email, hubspot_test_client),
        error_message=error_message,
        existence_desired=False,
    )


@pytest.fixture
def hubspot_runner(
    db,
    cache,
    hubspot_secrets,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "hubspot",
        hubspot_secrets,
    )
