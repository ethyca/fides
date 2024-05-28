from typing import Any, Dict, Generator

import pydash
import pytest
import random
import string
import requests

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("alchemer")


@pytest.fixture(scope="session")
def alchemer_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "alchemer.domain")
        or secrets["domain"],
        "api_token": pydash.get(saas_config, "alchemer.api_token")
        or secrets["api_token"],
        "api_token_secret": pydash.get(saas_config, "alchemer.api_token_secret")
        or secrets["api_token_secret"],
    }


@pytest.fixture(scope="session")
def alchemer_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "alchemer.identity_email") or secrets["identity_email"]
    )


@pytest.fixture
def alchemer_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def alchemer_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def alchemer_erasure_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def alchemer_erasure_data(
    alchemer_erasure_identity_email: str,
    alchemer_secrets,
) -> Generator:
    gen_string = string.ascii_lowercase
    test_contactlist = ''.join(random.choice(gen_string) for i in range(10))
    x_contactlist_name = f"Ethyca Test {test_contactlist}"

    base_url = f"https://{alchemer_secrets['domain']}/v5"
    params = {
        "api_token": alchemer_secrets['api_token'],
        "api_token_secret": alchemer_secrets['api_token_secret'],
        "list_name": x_contactlist_name,
    }
    contactlist_url = f"{base_url}/contactlist/"
    response = requests.put(contactlist_url, params=params)
    assert response.ok

    contactlist_id = response.json()["data"]["id"]
    contactlistcontact_url = f"{contactlist_url}{contactlist_id}/contactlistcontact"
    params = {
        "api_token": alchemer_secrets['api_token'],
        "api_token_secret": alchemer_secrets['api_token_secret'],
        "email_address": alchemer_erasure_identity_email,
    }
    # import pdb; pdb.set_trace()
    response = requests.put(contactlistcontact_url, params=params)
    assert response.ok
    # import pdb; pdb.set_trace()
    # yield {}


@pytest.fixture
def alchemer_runner(
    db,
    cache,
    alchemer_secrets,
    alchemer_external_references,
    alchemer_erasure_external_references,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "alchemer",
        alchemer_secrets,
        external_references=alchemer_external_references,
        erasure_external_references=alchemer_erasure_external_references,
    )
