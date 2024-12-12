from typing import Any, Dict

import pydash
import pytest

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("statsig_enterprise")


@pytest.fixture(scope="session")
def statsig_enterprise_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "statsig_enterprise.domain")
        or secrets["domain"],
        "server_secret_key": pydash.get(
            saas_config, "statsig_enterprise.server_secret_key"
        )
        or secrets["server_secret_key"],
    }


@pytest.fixture
def statsig_enterprise_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def statsig_enterprise_erasure_external_references() -> Dict[str, Any]:
    return {"statsig_user_id": "123"}


@pytest.fixture
def statsig_enterprise_runner(
    db,
    cache,
    statsig_enterprise_secrets,
    statsig_enterprise_erasure_external_references,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "statsig_enterprise",
        statsig_enterprise_secrets,
        erasure_external_references=statsig_enterprise_erasure_external_references,
    )
