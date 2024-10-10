import time
from typing import Any, Dict

import pydash
import pytest
import requests
from requests.auth import HTTPBasicAuth

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
    generate_random_phone_number,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("gladly")


@pytest.fixture(scope="session")
def gladly_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "gladly.domain") or secrets["domain"],
        "account_email": pydash.get(saas_config, "gladly.account_email")
        or secrets["account_email"],
        "api_key": pydash.get(saas_config, "gladly.api_key") or secrets["api_key"],
    }


@pytest.fixture(scope="session")
def gladly_identity_email(saas_config) -> str:
    return pydash.get(saas_config, "gladly.identity_email") or secrets["identity_email"]


##Should we use a pre-determined identity email or generate a random one?
@pytest.fixture
def gladly_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def gladly_erasure_data(
    gladly_secrets,
    gladly_erasure_identity_email: str,
) -> Dict[str, Any]:
    create_customer_url = f"https://{gladly_secrets['domain']}/api/v1/customer-profiles"
    auth = HTTPBasicAuth(gladly_secrets["account_email"], gladly_secrets["api_key"])

    body = {
        "name": "First Last",
        "address": "4303 Spring Forest Ln, Westlake Village, CA 91362-5605",
        "emails": [{"original": gladly_erasure_identity_email}],
        "phones": [{"original": generate_random_phone_number(), "type": "HOME"}],
    }

    response = requests.post(create_customer_url, json=body, auth=auth)
    assert response.ok
    time.sleep(10)  # required wait for the candidate to be created
    return


@pytest.fixture
def gladly_runner(
    db,
    cache,
    gladly_secrets,
) -> ConnectorRunner:
    return ConnectorRunner(db, cache, "gladly", gladly_secrets)
