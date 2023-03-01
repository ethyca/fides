from time import sleep
from typing import Any, Dict, Generator

import pydash
import pytest
import requests

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


@pytest.fixture
def zendesk_erasure_data(
    zendesk_erasure_identity_email: str,
) -> Generator:

    sleep(60)

    auth = secrets["username"], secrets["api_key"]
    base_url = f"https://{secrets['domain']}"

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
    yield ticket, user


@pytest.fixture
def zendesk_runner(
    db,
    zendesk_secrets,
) -> ConnectorRunner:
    return ConnectorRunner(db, zendesk_secrets, "zendesk")
