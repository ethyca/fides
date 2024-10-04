from typing import Any, Dict

import pydash
import pytest

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
        "domain" : pydash.get(saas_config, "gladly.domain") or secrets["domain"],
        "account_email" : pydash.get(saas_config, "gladly.account_email") or secrets["account_email"],
        "api_key": pydash.get(saas_config, "gladly.api_key") or secrets["api_key"],
    }

##Should we use a pre-determined identity email or generate a random one?
@pytest.fixture
def gladly_erasure_identity_email() -> str:
    return "test_ethyca@gmail.com"


@pytest.fixture
def gladly_erasure_identity_phone_number() -> str:
    return generate_random_phone_number()


@pytest.fixture
def gladly_runner(
    db,
    cache,
    gladly_secrets,
) -> ConnectorRunner:
    return ConnectorRunner(db, cache, "gladly", gladly_secrets)
