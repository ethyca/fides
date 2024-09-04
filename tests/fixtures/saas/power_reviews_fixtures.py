from typing import Any, Dict

import pydash
import pytest

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("power_reviews")


@pytest.fixture(scope="session")
def power_reviews_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "power_reviews.domain") or secrets["domain"],
        "client_id": pydash.get(saas_config, "power_reviews.client_id")
        or secrets["client_id"],
        "client_secret": pydash.get(saas_config, "power_reviews.client_secret")
        or secrets["client_secret"],
        "merchant_id": pydash.get(saas_config, "power_reviews.merchant_id")
        or secrets["merchant_id"],
        "merchant_group_id": pydash.get(saas_config, "power_reviews.merchant_group_id")
        or secrets["merchant_group_id"],
    }


@pytest.fixture
def power_reviews_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def power_reviews_runner(
    db,
    cache,
    power_reviews_secrets,
) -> ConnectorRunner:
    return ConnectorRunner(db, cache, "power_reviews", power_reviews_secrets)
