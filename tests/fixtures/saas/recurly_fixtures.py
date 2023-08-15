from typing import Any, Dict

import pydash
import pytest

from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("recurly")


@pytest.fixture(scope="session")
def recurly_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "recurly.domain") or secrets["domain"],
        "username": pydash.get(saas_config, "recurly.username") or secrets["username"],
    }


@pytest.fixture(scope="session")
def recurly_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "recurly.identity_email") or secrets["identity_email"]
    )


@pytest.fixture
def recurly_runner(db, cache, recurly_secrets) -> ConnectorRunner:
    return ConnectorRunner(db, cache, "recurly", recurly_secrets)
