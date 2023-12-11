from typing import Any, Dict

import pydash
import pytest

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("iterate")


@pytest.fixture(scope="session")
def iterate_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "iterate.domain") or secrets["domain"],
        "access_token": pydash.get(saas_config, "iterate.access_token")
        or secrets["access_token"],
        "survey_id": pydash.get(saas_config, "iterate.survey_id")
        or secrets["survey_id"],
    }


@pytest.fixture(scope="session")
def iterate_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "iterate.identity_email") or secrets["identity_email"]
    )


@pytest.fixture
def iterate_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def iterate_runner(db, cache, iterate_secrets) -> ConnectorRunner:
    return ConnectorRunner(db, cache, "iterate", iterate_secrets)
