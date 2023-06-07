from typing import Any, Dict, Generator

import uuid
import pydash
import pytest
import requests

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("gladly")


@pytest.fixture(scope="session")
def gladly_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "gladly.domain")
        or secrets["domain"],
        "username": pydash.get(saas_config, "gladly.username") or secrets["username"],
        "api_key": pydash.get(saas_config, "gladly.api_key") or secrets["api_key"],
    }


@pytest.fixture(scope="session")
def gladly_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "gladly.identity_email") or secrets["identity_email"]
    )

@pytest.fixture(scope="session")
def gladly_identity_phone_number(saas_config) -> str:
    return (
        pydash.get(saas_config, "gladly.identity_phone_number") or secrets["identity_phone_number"]
    )


@pytest.fixture
def gladly_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def gladly_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def gladly_erasure_external_references() -> Dict[str, Any]:
    return {}

class GladlyClient:
    def __init__(self, secrets: Dict[str, Any]):
        self.base_url = f"https://{secrets['domain']}"
        self.auth = secrets["username"], secrets["api_key"]

    def create_customer(self, email) -> str:
        user_id = uuid.uuid4().hex
        response = requests.post(
            url=f"{self.base_url}/api/v1/customer-profiles",
            auth=self.auth,
            json={
                "id":user_id,
                "name": "testing erasure",
                "emails": [
                {
                "original": email,
                }
                ]
            },
        )
        if response.ok:
            return user_id

    def get_customer(self, erasure_email: str):
        response = requests.get(
            url=f"{self.base_url}/api/v1/customer-profiles",
            auth=self.auth,
            params={"email": erasure_email},
        )
        if response.ok:
            return response


@pytest.fixture
def gladly_client(gladly_secrets) -> Generator:
    yield GladlyClient(gladly_secrets)


@pytest.fixture
def gladly_erasure_data(
    gladly_client: GladlyClient,
    gladly_erasure_identity_email: str,
) -> Generator:
    # create the customer data
    customer_id = gladly_client.create_customer(gladly_erasure_identity_email)
    yield customer_id


@pytest.fixture
def gladly_runner(
    db,
    cache,
    gladly_secrets,
    gladly_external_references,
    gladly_erasure_external_references,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "gladly",
        gladly_secrets,
        external_references=gladly_external_references,
        erasure_external_references=gladly_erasure_external_references,
    )