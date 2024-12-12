from base64 import b64encode
from typing import Any, Dict, Generator

import pydash
import pytest
import requests

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("greenhouse")


@pytest.fixture(scope="session")
def greenhouse_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "greenhouse.domain") or secrets["domain"],
        "api_key": pydash.get(saas_config, "greenhouse.api_key") or secrets["api_key"],
        "greenhouse_user_id": pydash.get(saas_config, "greenhouse.greenhouse_user_id")
        or secrets["greenhouse_user_id"],
    }


@pytest.fixture(scope="session")
def greenhouse_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "greenhouse.identity_email")
        or secrets["identity_email"]
    )


@pytest.fixture
def greenhouse_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def greenhouse_erasure_data(
    greenhouse_secrets,
    greenhouse_erasure_identity_email: str,
) -> Generator:
    base_url = f"https://{greenhouse_secrets['domain']}/v1/candidates"
    headers = {
        "On-Behalf-Of": f"{greenhouse_secrets['greenhouse_user_id']}",
    }
    # details of the test user - note that the job_id value below is from our instance and the sample job. This id is required for this call to work.
    body = {
        "first_name": "Test",
        "last_name": "Ethyca",
        "company": "Ethyca",
        "title": "Customer Success Representative",
        "is_private": "false",
        "phone_numbers": [{"value": "555-1212", "type": "mobile"}],
        "addresses": [{"value": "123 Fake St.", "type": "home"}],
        "email_addresses": [
            {"value": greenhouse_erasure_identity_email, "type": "work"},
            {"value": "testpersonal@example.com", "type": "personal"},
        ],
        "website_addresses": [{"value": "ethyca.example.com", "type": "personal"}],
        "social_media_addresses": [
            {"value": "linkedin.example.com/ethyca"},
            {"value": "@ethyca"},
        ],
        "educations": [
            {
                "start_date": "2001-09-15T00:00:00.000Z",
                "end_date": "2004-05-15T00:00:00.000Z",
            }
        ],
        "employments": [
            {
                "company_name": "Greenhouse",
                "title": "Engineer",
                "start_date": "2017-08-15T00:00:00.000Z",
                "end_date": "2018-05-15T00:00:00.000Z",
            }
        ],
        "tags": ["Walkabout", "Orientation"],
        "applications": [{"job_id": 4020768008}],
    }
    response = requests.post(
        base_url, auth=(greenhouse_secrets["api_key"], ""), headers=headers, json=body
    )
    assert response.ok
    json_response = response.json()
    user_id = json_response["id"]
    assert json_response["id"] > 1
    yield {user_id}


@pytest.fixture
def greenhouse_runner(
    db,
    cache,
    greenhouse_secrets,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "greenhouse",
        greenhouse_secrets,
    )
