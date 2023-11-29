from typing import Any, Dict

import pydash
import pytest

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("gong")


@pytest.fixture(scope="session")
def gong_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "gong.domain") or secrets["domain"],
        "access_key": pydash.get(saas_config, "gong.access_key")
        or secrets["access_key"],
        "access_key_secret": pydash.get(saas_config, "gong.access_key_secret")
        or secrets["access_key_secret"],
    }


@pytest.fixture(scope="session")
def gong_identity_email(saas_config) -> str:
    return pydash.get(saas_config, "gong.identity_email") or secrets["identity_email"]


@pytest.fixture(scope="session")
def gong_identity_name(saas_config) -> str:
    return pydash.get(saas_config, "gong.identity_name") or secrets["identity_name"]


@pytest.fixture
def gong_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def gong_runner(
    db,
    cache,
    gong_secrets,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "gong",
        gong_secrets,
    )
