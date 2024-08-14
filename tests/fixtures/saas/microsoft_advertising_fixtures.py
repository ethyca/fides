from typing import Any, Dict

import pydash
import pytest

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("microsoft_advertising")


@pytest.fixture(scope="session")
def microsoft_advertising_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "microsoft_advertising.domain")
        or secrets["domain"]
        # add the rest of your secrets here
    }


@pytest.fixture
def microsoft_advertising_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def microsoft_advertising_runner(
    db,
    cache,
    microsoft_advertising_secrets,
) -> ConnectorRunner:
    return ConnectorRunner(
        db, cache, "microsoft_advertising", microsoft_advertising_secrets
    )
