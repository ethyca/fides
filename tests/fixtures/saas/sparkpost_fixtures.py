from typing import Any, Dict, Generator

import uuid
import pydash
import pytest
import requests

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.saas_test_utils import poll_for_existence
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("sparkpost")


@pytest.fixture(scope="session")
def sparkpost_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "sparkpost.domain") or secrets["domain"],
        "api_key": pydash.get(saas_config, "sparkpost.api_key") or secrets["api_key"],
    }


@pytest.fixture(scope="session")
def sparkpost_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "sparkpost.identity_email") or secrets["identity_email"]
    )


@pytest.fixture(scope="function")
def sparkpost_erasure_recipient_id():
    return f"{uuid.uuid4().hex}"

@pytest.fixture
def sparkpost_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def sparkpost_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def sparkpost_erasure_external_references() -> Dict[str, Any]:
    return {}


class sparkpostClient:
    headers: object = {}
    base_url: str = ""

    def __init__(self, secrets: Dict[str, Any]):
        self.base_url = f"https://{secrets['domain']}"
        self.headers = {
            "Authorization": f"Basic {secrets['api_key']}",
        }

    def get_recipient(self, recipient_id: str, email: str) -> requests.Response:
        body = {
            "filterGroups": [
                {
                    "filters": [
                        {
                            "value": email,
                            "propertyName": "address.email",
                            "operator": "EQ",
                        }
                    ]
                }
            ]
        }
        recipient_response: requests.Response = requests.post(
            url=f"{self.base_url}/api/v1/recipient-lists/{recipient_id}?show_recipients=true",
            json=body,
            headers=self.headers,
        )
        assert recipient_response.ok
        return recipient_response.json()

    def create_recipient(self, email, uuid):
        return requests.post(
            url=f"{self.base_url}/api/v1/recipient-lists?num_rcpt_errors=1",
            headers=self.headers,
            json={
                "id": uuid,
                "name": "Ethyca test",
                "description": "An email list of employees at UMBC",
                "attributes": {
                    "internal_id": 113,
                    "list_group_id": 12322
                },
                "recipients": [
                    {
                        "address": {
                            "email": email,
                            "name": "test"
                        },
                        "tags": [
                            "reading"
                        ],
                        "metadata": {
                            "age": "31",
                            "place": "Test location"
                        },
                        "substitution_data": {
                            "favorite_color": "SparkPost Orange",
                            "job": "Software Engineer"
                        }
                    }
                ]
            },
        )

@pytest.fixture
def sparkpost_client(sparkpost_secrets) -> Generator:
    yield sparkpostClient(sparkpost_secrets)


@pytest.fixture
def sparkpost_erasure_data(
    sparkpost_client: sparkpostClient,
    sparkpost_erasure_identity_email: str,
    sparkpost_erasure_recipient_id: str
) -> Generator:
    
    response = sparkpost_client.create_recipient(sparkpost_erasure_identity_email, sparkpost_erasure_recipient_id)
    recipient = response.json()["results"]
    recipient_id = recipient["id"]

    # error_message = f"customer with email {sparkpost_erasure_identity_email} could not be created in Recharge"
    # poll_for_existence(
    #     sparkpost_client.get_recipient,
    #     (sparkpost_erasure_identity_email,recipient_id),
    #     error_message=error_message,
    # )

    yield recipient_id


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