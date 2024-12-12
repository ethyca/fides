from typing import Any, Dict

import pydash
import pytest

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("heap")


@pytest.fixture(scope="session")
def heap_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "heap.domain") or secrets["domain"],
        "app_id": pydash.get(saas_config, "heap.app_id") or secrets["app_id"],
        "api_key": pydash.get(saas_config, "heap.api_key") or secrets["api_key"],
    }


@pytest.fixture(scope="session")
def heap_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def heap_runner(
    db,
    cache,
    heap_secrets,
) -> ConnectorRunner:
    return ConnectorRunner(db, cache, "heap", heap_secrets)
