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
        "api_token": pydash.get(saas_config, "surveymonkey.api_token") or secrets["api_token"],
        "survey_id": pydash.get(saas_config, "surveymonkey.survey_id") or secrets["survey_id"],
        "collector_id": pydash.get(saas_config, "surveymonkey.collector_id") or secrets["collector_id"],
        "admin_email": pydash.get(saas_config, "surveymonkey.admin_email") or secrets["admin_email"],
        "page_id": pydash.get(saas_config, "surveymonkey.page_id") or secrets["page_id"],
        "ques_id": pydash.get(saas_config, "surveymonkey.ques_id") or secrets["ques_id"],
        "choice_id": pydash.get(saas_config, "surveymonkey.choice_id") or secrets["choice_id"],
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

    def create_contacts(self, email):
        return requests.post(
            url=f"{self.base_url}/v3/contacts",
            headers=self.headers,
            json={
                "email": email
            },
        )
    
    def create_collectors(self, secrets: Dict[str, Any]):
        return requests.post(
            url=f"{self.base_url}/v3/surveys/{secrets['survey_id']}/collectors",
            headers=self.headers,
            json={
            "type": "email",
            "name": "Erasure Test Collector"
            },
        )

    def get_collectors(self, survey_secrets):
        return requests.get(
            url=f"{self.base_url}/v3/surveys/{survey_secrets['survey_id']}/collectors",
            headers=self.headers,
        )

    def create_survey_response(self, survey_secrets):
        return requests.post(
            url=f"{self.base_url}/v3/collectors/{survey_secrets['collector_id']}/responses",
            headers=self.headers,
            json={
                "pages": [
                    {
                        "id": survey_secrets['page_id'],
                        "questions": [
                            {
                                "id": survey_secrets['ques_id'],
                                "answers": [
                                    {
                                        "choice_id": survey_secrets['choice_id']
                                    }
                                ]
                            }
                        ]
                    }
                ]
            },
        )


@pytest.fixture
def surveymonkey_client(surveymonkey_secrets) -> Generator:
    yield SurveyMonkeyClient(surveymonkey_secrets)


@pytest.fixture
def surveymonkey_erasure_data(
    surveymonkey_client: SurveyMonkeyClient,
    surveymonkey_erasure_identity_email: str,
    surveymonkey_secrets
) -> Generator:
    # contacts
    contacts_response = surveymonkey_client.create_contacts(surveymonkey_erasure_identity_email)
    assert contacts_response.ok
    contacts = contacts_response.json()

    # collectors
    # response = surveymonkey_client.create_collectors(surveymonkey_secrets)
    # assert response.ok
    # collectors = response.json()["id"]

    # survey_response
    sur_response = surveymonkey_client.create_survey_response(surveymonkey_secrets)
    assert sur_response.ok

    # error_message = f"customer with email {surveymonkey_erasure_identity_email} could not be created in Recharge"
    # poll_for_existence(
    #     surveymonkey_client.get_recipient,
    #     (surveymonkey_erasure_identity_email,recipient_id),
    #     error_message=error_message,
    # )

    yield sur_response, collectors, contacts


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
