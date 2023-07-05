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

secrets = get_secrets("ada_chatbot")


@pytest.fixture(scope="session")
def ada_chatbot_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "ada_chatbot.domain") or secrets["domain"],
        "export_access_token": pydash.get(saas_config, "ada_chatbot.export_access_token") or secrets["export_access_token"],
        "compliance_access_token": pydash.get(saas_config, "ada_chatbot.compliance_access_token") or secrets["compliance_access_token"],
        "identity_email": pydash.get(saas_config, "ada_chatbot.identity_email") or secrets["identity_email"],
        "chatter_id": pydash.get(saas_config, "ada_chatbot.chatter_id") or secrets["chatter_id"],
        # add the rest of your secrets here
    }


@pytest.fixture(scope="session")
def ada_chatbot_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "ada_chatbot.identity_email") or secrets["identity_email"]
    )


@pytest.fixture
def ada_chatbot_erasure_identity_email() -> str:
    return generate_random_email()


class AdaChatbotClient:
    def __init__(self, secrets: Dict[str, Any]):
        self.base_url = f"https://{secrets['domain']}"
        self.headers = {
        "Authorization": f"Bearer {secrets['compliance_access_token']}",
    }

    def get_conversation(self, chatterid):
        return requests.get(
            url=f"{self.base_url}/v2/users",
            headers=self.headers,
            params={"created_since": '2023-06-28T17:59:28.201000', "page_size": 100, "chatter_id": chatterid},
        )

    def delete_data(self, email):
        return requests.post(
            url=f"{self.base_url}/api/v1/data-subject-request",
            headers=self.headers,
            json={
            "type": "ERASURE",
            "email": email
            },
        )


@pytest.fixture
def ada_chatbot_client(ada_chatbot_secrets) -> Generator:
    yield AdaChatbotClient(ada_chatbot_secrets)



@pytest.fixture
def ada_chatbot_erasure_data(
    ada_chatbot_client: AdaChatbotClient,
    ada_chatbot_erasure_identity_email: str,
    ada_chatbot_secrets
) -> Generator:
    # customer
    response = ada_chatbot_client.delete_data(ada_chatbot_erasure_identity_email)
    assert response.ok
    user = response.json()["email"]

    yield user


@pytest.fixture
def ada_chatbot_runner(
    db,
    cache,
    ada_chatbot_secrets,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "ada_chatbot",
        ada_chatbot_secrets,
    )