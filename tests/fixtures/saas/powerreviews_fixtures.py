from typing import Any, Dict

import pydash
import pytest

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("powerreviews")


@pytest.fixture(scope="session")
def powerreviews_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "powerreviews.domain") or secrets["domain"],
        "client_id": pydash.get(saas_config, "powerreviews.client_id")
        or secrets["client_id"],
        "client_secret": pydash.get(saas_config, "powerreviews.client_secret")
        or secrets["client_secret"],
    }


@pytest.fixture
def powerreviews_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def powerreviews_runner(
    db,
    cache,
    powerreviews_secrets,
) -> ConnectorRunner:
    return ConnectorRunner(db, cache, "powerreviews", powerreviews_secrets)
