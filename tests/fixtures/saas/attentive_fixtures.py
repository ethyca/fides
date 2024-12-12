from typing import Any, Dict

import pydash
import pytest

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
    generate_random_phone_number,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("attentive")


@pytest.fixture(scope="session")
def attentive_secrets(saas_config) -> Dict[str, Any]:
    return {
        "api_key": pydash.get(saas_config, "attentive.api_key") or secrets["api_key"],
    }


@pytest.fixture
def attentive_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def attentive_erasure_identity_phone_number() -> str:
    return generate_random_phone_number()


@pytest.fixture
def attentive_runner(
    db,
    cache,
    attentive_secrets,
) -> ConnectorRunner:
    return ConnectorRunner(db, cache, "attentive", attentive_secrets)
