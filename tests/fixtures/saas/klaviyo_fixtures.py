import pydash
import pytest
import requests

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("klaviyo")


@pytest.fixture(scope="session")
def klaviyo_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "klaviyo.domain") or secrets["domain"],
        "api_key": pydash.get(saas_config, "klaviyo.api_key") or secrets["api_key"],
        "revision": pydash.get(saas_config, "klaviyo.revision") or secrets["revision"],
    }


@pytest.fixture(scope="session")
def klaviyo_identity_email(saas_config):
    return (
        pydash.get(saas_config, "klaviyo.identity_email") or secrets["identity_email"]
    )


@pytest.fixture(scope="function")
def klaviyo_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture(scope="function")
def klaviyo_erasure_data(klaviyo_secrets, klaviyo_erasure_identity_email) -> None:
    base_url = f"https://{klaviyo_secrets['domain']}"
    headers = {
        "Authorization": f"Klaviyo-API-Key {klaviyo_secrets['api_key']}",
        "revision": klaviyo_secrets["revision"],
    }
    # user
    body = {
        "data": {
            "type": "profile",
            "attributes": {"email": klaviyo_erasure_identity_email},
        }
    }

    users_response = requests.post(
        url=f"{base_url}/api/profiles/", headers=headers, json=body
    )
    user = users_response.json()

    yield user


@pytest.fixture
def klaviyo_runner(
    db,
    cache,
    klaviyo_secrets,
) -> ConnectorRunner:
    return ConnectorRunner(db, cache, "klaviyo", klaviyo_secrets)
