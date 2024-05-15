from typing import Any, Dict, Generator

import pydash
import pytest
import requests
import base64

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("recurly")


@pytest.fixture(scope="session")
def recurly_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "recurly.domain") or secrets["domain"],
        "username": pydash.get(saas_config, "recurly.username") or secrets["username"],
    }


@pytest.fixture(scope="session")
def recurly_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "recurly.identity_email") or secrets["identity_email"]
    )

@pytest.fixture
def recurly_erasure_identity_email() -> str:
    return generate_random_email()

@pytest.fixture
def recurly_erasure_data(
    recurly_erasure_identity_email: str,
    recurly_secrets,
) -> Generator:
    api_key = recurly_secrets['username']
    api_key_string = api_key
    api_key_bytes = api_key_string.encode("ascii")
    base64_bytes = base64.b64encode(api_key_bytes)
    auth_username = base64_bytes.decode("ascii")
    print(auth_username)

    base_url = f"https://{recurly_secrets['domain']}"
    headers = {

    }
    # create the data needed for erasure tests here
    # can do anything here =) e.g. write python directly
    # I'll need 3 here, one for account, shipping addresses and billing info

    import pdb; pdb.set_trace()

    # yield {}

@pytest.fixture
def recurly_runner(db, cache, recurly_secrets) -> ConnectorRunner:
    return ConnectorRunner(db, cache, "recurly", recurly_secrets)
