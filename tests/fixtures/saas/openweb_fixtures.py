import random
import string
from typing import Any, Dict, Generator

import pydash
import pytest
import requests

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("openweb")


@pytest.fixture(scope="session")
def openweb_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "openweb.domain") or secrets["domain"],
        "api_key": pydash.get(saas_config, "openweb.api_key") or secrets["api_key"],
        "x_spot_id": pydash.get(saas_config, "openweb.x_spot_id")
        or secrets["x_spot_id"],
    }


@pytest.fixture
def openweb_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def openweb_erasure_external_references() -> Dict[str, Any]:
    random_pkv = "".join(
        random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits)
        for _ in range(10)
    )
    return {"primary_key": random_pkv}


@pytest.fixture
def openweb_create_erasure_data(
    openweb_erasure_external_references, openweb_secrets
) -> Generator:
    """Notes on the data generated here for the erasure request
    In this case we need to ensure that a user exists that can be deleted. We also need to ensure we reference the user we used here for the delete request as well. We made a little helper up there in the openweb_erasure_external_references to create a string we can use to create a user so our erasure test will pass when it has something to delete. We put in a check to ensure we get a pass on a check to ensure the user got made.
    """
    primary_key_val = openweb_erasure_external_references["primary_key"]
    params = {
        "primary_key": primary_key_val,
        "spot_id": openweb_secrets["x_spot_id"],
        "user_name": primary_key_val,
    }

    add_user_url = f'https://{openweb_secrets["domain"]}/api/sso/v1/user'

    check_user_url = (
        f'https://{openweb_secrets["domain"]}/api/sso/v1/user/{primary_key_val}'
    )
    payload = {}
    headers = {"x-spotim-sso-access-token": openweb_secrets["api_key"]}
    response = requests.request(
        "POST", add_user_url, headers=headers, data=payload, params=params
    )
    assert response.ok
    response = requests.request("GET", check_user_url, headers=headers)
    assert response.ok


@pytest.fixture
def openweb_runner(
    db,
    cache,
    openweb_secrets,
    openweb_erasure_external_references,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "openweb",
        openweb_secrets,
        erasure_external_references=openweb_erasure_external_references,
    )
