from typing import Any, Dict, Generator
from uuid import uuid4

import pydash
import pytest
import requests

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
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


@pytest.fixture
def sparkpost_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def sparkpost_erasure_data(
    sparkpost_erasure_identity_email: str, sparkpost_secrets
) -> Generator:  # make recipients here
    payload = {
        "id": str(uuid4()),
        "name": "graduate_students",
        "description": "An email list of graduate students at UMBC",
        "attributes": {"internal_id": 112, "list_group_id": 12321},
        "recipients": [
            {
                "address": {
                    "email": sparkpost_erasure_identity_email,
                    "name": "Ethyca Test",
                },
                "tags": ["greeting", "prehistoric", "fred", "flintstone"],
                "metadata": {"age": "24", "place": "Bedrock"},
                "substitution_data": {
                    "favorite_color": "SparkPost Orange",
                    "job": "Software Engineer",
                },
            },
        ],
    }
    base_url = f"https://{sparkpost_secrets['domain']}"
    auth = sparkpost_secrets["api_key"], None

    response = requests.post(
        url=f"{base_url}/api/v1/recipient-lists",
        auth=auth,
        json=payload,
    )
    recipient_list_id = response.json()["results"]["id"]

    yield

    # delete the recipient list after the test since the data_protection_request doesn't delete the lists just the recipients
    requests.delete(
        url=f"{base_url}/api/v1/recipient-lists/{recipient_list_id}",
        auth=auth,
    )


@pytest.fixture
def sparkpost_runner(db, cache, sparkpost_secrets) -> ConnectorRunner:
    return ConnectorRunner(db, cache, "sparkpost", sparkpost_secrets)
