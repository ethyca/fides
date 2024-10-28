from typing import Any, Dict, Generator

import pydash
import pytest
import requests

from fides.api.models.connectionconfig import ConnectionConfig
from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("zendesk")


@pytest.fixture(scope="session")
def zendesk_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "zendesk.domain") or secrets["domain"],
        "username": pydash.get(saas_config, "zendesk.username") or secrets["username"],
        "api_key": pydash.get(saas_config, "zendesk.api_key") or secrets["api_key"],
        "page_size": pydash.get(saas_config, "zendesk.page_size")
        or secrets["page_size"],
    }


@pytest.fixture(scope="session")
def zendesk_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "zendesk.identity_email") or secrets["identity_email"]
    )


@pytest.fixture
def zendesk_erasure_identity_email() -> str:
    return generate_random_email()


class ZendeskClient:
    def __init__(self, secrets: Dict[str, Any]):
        self.base_url = f"https://{secrets['domain']}"
        self.auth = secrets["username"]+"/token", secrets["api_key"]

    def create_user(self, email):
        return requests.post(
            url=f"{self.base_url}/api/v2/users",
            auth=self.auth,
            json={
                "user": {
                    "name": "Ethyca Test Erasure",
                    "email": email,
                    "verified": "true",
                }
            },
        )

    def get_user(self, email):
        return requests.get(
            url=f"{self.base_url}/v2/users",
            auth=self.auth,
            params={"email": email},
        )

    def create_ticket(self, user_id: str, closed: bool):
        if(closed):
            json = {
                "ticket": {
                    "comment": {"body": "Test Comment"},
                    "priority": "urgent",
                    "subject": "Test Ticket",
                    "requester_id": user_id,
                    "submitter_id": user_id,
                    "description": "Test Description",
                    "status" : "closed"
                }
            }
        else:
            json = {
                "ticket": {
                    "comment": {"body": "Test Comment"},
                    "priority": "urgent",
                    "subject": "Test Ticket",
                    "requester_id": user_id,
                    "submitter_id": user_id,
                    "description": "Test Description"
                }
            }
        return requests.post(
            url=f"{self.base_url}/api/v2/tickets",
            auth=self.auth,
            json=json,
        )

    def get_ticket(self, ticket_id: str):
        return requests.get(
            url=f"{self.base_url}/v2/tickets/{ticket_id}.json",
            auth=self.auth,
        )


@pytest.fixture
def zendesk_client(zendesk_secrets) -> Generator:
    yield ZendeskClient(zendesk_secrets)


@pytest.fixture
def zendesk_erasure_data(
    zendesk_client: ZendeskClient,
    zendesk_erasure_identity_email: str,
) -> Generator:
    # customer
    response = zendesk_client.create_user(zendesk_erasure_identity_email)
    assert response.ok
    user = response.json()["user"]

    # ticket
    response = zendesk_client.create_ticket(user["id"], True)
    assert response.ok
    ticket = response.json()["ticket"]
    yield ticket, user

@pytest.fixture
def zendesk_erasure_data_with_open_comments(
    zendesk_client: ZendeskClient,
    zendesk_erasure_identity_email: str,
) -> Generator:
    # customer
    response = zendesk_client.create_user(zendesk_erasure_identity_email)
    assert response.ok
    user = response.json()["user"]

    # ticket
    response = zendesk_client.create_ticket(user["id"], False)
    assert response.ok
    ticket = response.json()["ticket"]
    yield ticket, user


@pytest.fixture
def zendesk_runner(
    db,
    cache,
    zendesk_secrets,
) -> ConnectorRunner:
    return ConnectorRunner(db, cache, "zendesk", zendesk_secrets)
