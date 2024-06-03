from typing import Any, Dict, Generator

import pydash
import pytest
import requests


from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("greenhouse_harvest")


@pytest.fixture(scope="session")
def greenhouse_harvest_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "greenhouse_harvest.domain")
        or secrets["domain"],
        "api_key": pydash.get(saas_config, "greenhouse_harvest.api_key")
        or secrets["api_key"],
        "greenhouse_user_id": pydash.get(saas_config, "greenhouse_harvest.greenhouse_user_id")
        or secrets["greenhouse_user_id"],
    }


@pytest.fixture(scope="session")
def greenhouse_harvest_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "greenhouse_harvest.identity_email") or secrets["identity_email"]
    )


@pytest.fixture
def greenhouse_harvest_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def greenhouse_harvest_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def greenhouse_harvest_erasure_external_references() -> Dict[str, Any]:
    return {"greenhouse_user_id":"4052733008"}


@pytest.fixture
def greenhouse_harvest_erasure_data(
    greenhouse_harvest_secrets,
    greenhouse_harvest_erasure_external_references,
    greenhouse_harvest_erasure_identity_email: str,
) -> Generator:
    # create the data needed for erasure tests here
    base_url = f"https://{greenhouse_harvest_secrets['domain']}/v1/candidates"
    headers = {
        "Authorization": f"{greenhouse_harvest_secrets['api_key']}",
        "On-Behalf-Of": f"{greenhouse_harvest_erasure_external_references['greenhouse_user_id']}"
    }
    # details of the user
    body = {
        "first_name": "Test",
        "last_name": "Ethyca",
        "company": "Ethyca",
        "title": "Customer Success Representative",
        "is_private": "false",
        "phone_numbers": [
            {
            "value": "555-1212",
            "type": "mobile"
            }
        ],
        "addresses": [
            {
            "value": "123 Fake St.",
            "type": "home"
            }
        ],
        "email_addresses": [
            {
            "value": greenhouse_harvest_erasure_identity_email,
            "type": "work"
            },
            {
            "value": "testpersonal@example.com",
            "type": "personal"
            }
        ],
        "website_addresses": [
            {
            "value": "ethyca.example.com",
            "type": "personal"
            }
        ],
        "social_media_addresses": [
            {
            "value": "linkedin.example.com/ethyca"
            },
            {
            "value": "@ethyca"
            }
        ],
        "educations": [
            {
            "start_date": "2001-09-15T00:00:00.000Z",
            "end_date": "2004-05-15T00:00:00.000Z"
            }
        ],
        "employments": [
            {
                "company_name": "Greenhouse",
                "title": "Engineer",
                "start_date": "2017-08-15T00:00:00.000Z",
                "end_date": "2018-05-15T00:00:00.000Z"
            }
        ],
        "tags": [
            "Walkabout",
            "Orientation"
        ],
        "applications": [
            {
            "job_id": 4020768008
            }
        ]
    }

    response = requests.post(
        base_url, headers=headers, json=body
    )
#    import pdb; pdb.set_trace()
    assert response.ok
    json_response = response.json()
    user_id_res = json_response["id"]

    yield {user_id_res}


@pytest.fixture
def greenhouse_harvest_runner(
    db,
    cache,
    greenhouse_harvest_secrets,
    greenhouse_harvest_external_references,
    greenhouse_harvest_erasure_external_references,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "greenhouse_harvest",
        greenhouse_harvest_secrets,
        external_references=greenhouse_harvest_external_references,
        erasure_external_references=greenhouse_harvest_erasure_external_references,
    )
