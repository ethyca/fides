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
        "survey_id": pydash.get(saas_config, "surveymonkey.survey_id")
        or secrets["survey_id"],
        "collector_id": pydash.get(saas_config, "surveymonkey.collector_id")
        or secrets["collector_id"],
        "admin_email": pydash.get(saas_config, "surveymonkey.admin_email")
        or secrets["admin_email"],
        "page_id": pydash.get(saas_config, "surveymonkey.page_id")
        or secrets["page_id"],
        "question_id": pydash.get(saas_config, "surveymonkey.question_id")
        or secrets["question_id"],
        "choice_id": pydash.get(saas_config, "surveymonkey.choice_id")
        or secrets["choice_id"],
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


class SurveyMonkeyClient:
    def __init__(self, secrets: Dict[str, Any]):
        self.secrets = secrets
        self.survey_id = secrets["survey_id"]
        self.collector_id = secrets["collector_id"]
        self.base_url = f"https://{secrets['domain']}"
        self.headers = {
            "Authorization": f"Bearer {secrets['api_token']}",
        }

    def create_contact(self, email):
        return requests.post(
            url=f"{self.base_url}/v3/contacts",
            headers=self.headers,
            json={"email": email},
        )

    def create_collector_message(self):
        return requests.post(
            url=f"{self.base_url}/v3/surveys/{self.survey_id}/collectors/{self.collector_id}/messages",
            headers=self.headers,
            json={"type": "invite"},
        )

    def create_recipient(self, message_id: str, email: str):
        return requests.post(
            url=f"{self.base_url}/v3/surveys/{self.survey_id}/collectors/{self.collector_id}/messages/{message_id}/recipients",
            headers=self.headers,
            json={"email": email},
        )

    def create_survey_response(self, recipient_id: str):
        return requests.post(
            url=f"{self.base_url}/v3/collectors/{self.collector_id}/responses",
            headers=self.headers,
            json={
                "recipient_id": recipient_id,
                "pages": [
                    {
                        "id": self.secrets["page_id"],
                        "questions": [
                            {
                                "id": self.secrets["question_id"],
                                "answers": [{"choice_id": self.secrets["choice_id"]}],
                            }
                        ],
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
    # contact
    contacts_response = surveymonkey_client.create_contact(
        surveymonkey_erasure_identity_email
    )
    assert contacts_response.ok

    # collector message
    message_response = surveymonkey_client.create_collector_message()
    assert message_response.ok
    message_id = message_response.json()["id"]

    # recipient
    recipient_response = surveymonkey_client.create_recipient(
        message_id, surveymonkey_erasure_identity_email
    )
    assert recipient_response.ok
    recipient_id = recipient_response.json()["id"]

    # survey response
    survey_response = surveymonkey_client.create_survey_response(recipient_id)
    assert survey_response.ok

    yield


@pytest.fixture
def surveymonkey_runner(db, cache, surveymonkey_secrets) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "surveymonkey",
        surveymonkey_secrets,
    )
