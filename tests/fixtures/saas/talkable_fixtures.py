from typing import Any, Dict, Generator

import pydash
import pytest
import requests

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("talkable")


@pytest.fixture(scope="session")
def talkable_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "talkable.domain") or secrets["domain"],
        "site_slug": pydash.get(saas_config, "talkable.site_slug")
        or secrets["site_slug"],
        "api_key": pydash.get(saas_config, "talkable.api_key") or secrets["api_key"],
    }


@pytest.fixture(scope="session")
def talkable_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "talkable.identity_email") or secrets["identity_email"]
    )


@pytest.fixture(scope="function")
def talkable_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture(scope="function")
def talkable_erasure_data(
    talkable_erasure_identity_email: str,
    talkable_secrets,
) -> Generator:
    # create the data needed for erasure tests here
    base_url = f"https://{talkable_secrets['domain']}"
    headers = {
        "Authorization": f"Bearer {talkable_secrets['api_key']}",
    }

    # person
    body = {
        "site_slug": talkable_secrets["site_slug"],
        "data": {
            "first_name": "Ethyca",
            "last_name": "RTF",
            "email": talkable_erasure_identity_email,
            "phone_number": "+19515551234",
            "username": "ethycatrtf",
            "gated_param_subscribed": False,
            "unsubscribed": False,
        },
    }

    people_response = requests.put(
        url=f"{base_url}/api/v2/people/{talkable_erasure_identity_email}",
        headers=headers,
        json=body,
    )
    person = people_response.json()["result"]["person"]

    yield person


@pytest.fixture
def talkable_runner(
    db,
    cache,
    talkable_secrets,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "talkable",
        talkable_secrets,
    )
