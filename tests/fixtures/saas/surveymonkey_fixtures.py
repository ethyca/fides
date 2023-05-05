from typing import Any, Dict, Generator

import pydash
import pytest
import requests

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("surveymonkey")


@pytest.fixture(scope="session")
def surveymonkey_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "surveymonkey.domain") or secrets["domain"],
        "api_token": pydash.get(saas_config, "surveymonkey.api_token")
        or secrets["api_token"],
        # add the rest of your secrets here
    }


@pytest.fixture(scope="session")
def surveymonkey_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "surveymonkey.identity_email")
        or secrets["identity_email"]
    )


@pytest.fixture
def surveymonkey_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def surveymonkey_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def surveymonkey_erasure_external_references() -> Dict[str, Any]:
    return {}


class SurveyMonkeyClient:
    headers: object = {}
    base_url: str = ""

    def __init__(self, secrets: Dict[str, Any]):
        self.base_url = f"https://{secrets['domain']}"
        self.headers = {
            "Authorization": f"Bearer {secrets['api_token']}",
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

    def create_survey_response(self, email):
        return requests.post(
            url=f"{self.base_url}/api/v1/recipient-lists?num_rcpt_errors=1",
            headers=self.headers,
            json={
                "name": "Ethyca test",
                "description": "An email list of employees at UMBC",
                "attributes": {"internal_id": 113, "list_group_id": 12322},
                "recipients": [
                    {
                        "address": {"email": email, "name": "test"},
                        "tags": ["reading"],
                        "metadata": {"age": "31", "place": "Test location"},
                        "substitution_data": {
                            "favorite_color": "surveymonkey Orange",
                            "job": "Software Engineer",
                        },
                    }
                ],
            },
        )


@pytest.fixture
def surveymonkey_client(surveymonkey_secrets) -> Generator:
    yield SurveyMonkeyClient(surveymonkey_secrets)


@pytest.fixture
def surveymonkey_erasure_data(
    surveymonkey_client: SurveyMonkeyClient,
    surveymonkey_erasure_identity_email: str,
) -> Generator:
    response = surveymonkey_client.create_survey_response(
        surveymonkey_erasure_identity_email
    )
    recipient = response.json()["results"]
    recipient_id = recipient["id"]

    # error_message = f"customer with email {surveymonkey_erasure_identity_email} could not be created in Recharge"
    # poll_for_existence(
    #     surveymonkey_client.get_recipient,
    #     (surveymonkey_erasure_identity_email,recipient_id),
    #     error_message=error_message,
    # )

    yield recipient_id


@pytest.fixture
def surveymonkey_runner(
    db,
    cache,
    surveymonkey_secrets,
    surveymonkey_external_references,
    surveymonkey_erasure_external_references,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "surveymonkey",
        surveymonkey_secrets,
    )
