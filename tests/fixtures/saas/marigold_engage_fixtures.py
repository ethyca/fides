from typing import Any, Dict

import pydash
import pytest
import requests

from fides.api.service.saas_request.override_implementations.marigold_engage_request_overrides import (
    signed_payload,
)
from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("marigold_engage")


@pytest.fixture(scope="session")
def marigold_engage_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "marigold_engage.domain")
        or secrets["domain"],
        "api_key": pydash.get(saas_config, "marigold_engage.api_key")
        or secrets["api_key"],
        "secret": pydash.get(saas_config, "marigold_engage.secret")
        or secrets["secret"],
    }


@pytest.fixture(scope="session")
def marigold_engage_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "marigold_engage.identity_email")
        or secrets["identity_email"]
    )


@pytest.fixture
def marigold_engage_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def marigold_engage_erasure_data(
    marigold_engage_secrets,
    marigold_engage_erasure_identity_email: str,
) -> None:
    base_url = f'https://{marigold_engage_secrets["domain"]}/user'
    response = requests.request(
        "POST",
        base_url,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=signed_payload(
            marigold_engage_secrets, {"id": marigold_engage_erasure_identity_email}
        ),
    )
    assert response.ok


@pytest.fixture
def marigold_engage_runner(
    db,
    cache,
    marigold_engage_secrets,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "marigold_engage",
        marigold_engage_secrets,
    )
