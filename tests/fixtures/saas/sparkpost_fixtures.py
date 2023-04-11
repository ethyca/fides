from typing import Any, Dict, Generator

import pydash
import pytest
import requests

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets
from fides.lib.cryptography import cryptographic_util

secrets = get_secrets("sparkpost")


@pytest.fixture(scope="session")
def sparkpost_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "sparkpost.domain")
        or secrets["domain"],
        "api_key": pydash.get(saas_config, "sparkpost.api_key") or secrets["api_key"],
        # add the rest of your secrets here
    }


@pytest.fixture(scope="session")
def sparkpost_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "sparkpost.identity_email") or secrets["identity_email"]
    )


@pytest.fixture
def sparkpost_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def sparkpost_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def sparkpost_erasure_external_references() -> Dict[str, Any]:
    return {}

class SparkpostClient:
    def __init__(self, secrets: Dict[str, Any]):
        self.base_url = f"https://{secrets['domain']}"
        self.auth = secrets["api_key"],''

    def create_user(self, email,uid):
        return requests.post(
            url=f"{self.base_url}/api/v1/recipient-lists?num_rcpt_errors=3",
            auth=self.auth,
            json={
                "id": uid,
                "name": "test erasure",
                "description": "An email list of employees",
                "attributes": {
                    "internal_id": 112,
                    "list_group_id": 12321
                },
                "recipients": [
                    {
                    "address": {
                        "email": email,
                        "name": "testing"
                    },
                    "tags": [
                        "greeting",
                        "prehistoric",
                        "fred",
                        "flintstone"
                    ],
                    "metadata": {
                        "age": "24",
                        "place": "Bedrock"
                    },
                    "substitution_data": {
                        "favorite_color": "SparkPost Orange",
                        "job": "Software Engineer"
                    }
                    }
                ]
                },
        )
    
    def get_receipient(self, id):
        return requests.get(
            url=f"{self.base_url}/api/v1/recipient-lists/{id}?show_recipients=true",
            auth=self.auth,
            params={},
        )
    
@pytest.fixture
def sparkpost_client(sparkpost_secrets) -> Generator:
    yield SparkpostClient(sparkpost_secrets)


@pytest.fixture
def sparkpost_erasure_data(
    sparkpost_client: SparkpostClient,
    sparkpost_erasure_identity_email: str,
) -> Generator:
    # receipient
    uid = cryptographic_util.generate_secure_random_string(10)
    response = sparkpost_client.create_user(sparkpost_erasure_identity_email,uid)
    assert response.ok
    user = response.json()["results"]
    yield user


@pytest.fixture
def sparkpost_runner(
    db,
    cache,
    sparkpost_secrets,
    sparkpost_external_references,
    sparkpost_erasure_external_references,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "sparkpost",
        sparkpost_secrets,
        external_references=sparkpost_external_references,
        erasure_external_references=sparkpost_erasure_external_references,
    )