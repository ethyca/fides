from typing import Any, Dict

import pydash
import pytest

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("shipstation")


@pytest.fixture(scope="session")
def shipstation_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "shipstation.domain") or secrets["domain"],
        "api_key": pydash.get(saas_config, "shipstation.api_key") or secrets["api_key"],
        "api_secret": pydash.get(saas_config, "shipstation.api_secret")
        or secrets["api_secret"],
    }


@pytest.fixture(scope="session")
def shipstation_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "shipstation.identity_email")
        or secrets["identity_email"]
    )

@pytest.fixture
def shipstation_runner(
    db, cache, shipstation_secrets
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "shipstation",
        shipstation_secrets
    )
