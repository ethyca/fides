from typing import Any, Dict

import pydash
import pytest

from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("doordash")


@pytest.fixture(scope="function")
def doordash_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "doordash.domain") or secrets["domain"],
        "developer_id": pydash.get(saas_config, "doordash.developer_id")
        or secrets["developer_id"],
        "key_id": pydash.get(saas_config, "doordash.key_id") or secrets["key_id"],
        "signing_secret": pydash.get(saas_config, "doordash.signing_secret")
        or secrets["signing_secret"],
    }


@pytest.fixture(scope="function")
def doordash_identity_email(saas_config):
    return (
        pydash.get(saas_config, "doordash.identity_email") or secrets["identity_email"]
    )


@pytest.fixture
def doordash_external_references() -> Dict[str, Any]:
    return {"doordash_delivery_id": "D-12345"}


@pytest.fixture
def doordash_runner(
    db,
    cache,
    doordash_secrets,
    doordash_external_references,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "doordash",
        doordash_secrets,
        external_references=doordash_external_references,
    )
