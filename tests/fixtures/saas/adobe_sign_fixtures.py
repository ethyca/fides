from typing import Any, Dict

import pydash
import pytest

from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("adobe_sign")


@pytest.fixture(scope="session")
def adobe_sign_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "adobe_sign.domain") or secrets["domain"],
        "client_id": pydash.get(saas_config, "adobe_sign.client_id")
        or secrets["client_id"],
        "client_secret": pydash.get(saas_config, "adobe_sign.client_secret")
        or secrets["client_secret"],
        "redirect_uri": pydash.get(saas_config, "adobe_sign.redirect_uri")
        or secrets["redirect_uri"],
    }


@pytest.fixture(scope="session")
def adobe_sign_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "adobe_sign.identity_email")
        or secrets["identity_email"]
    )


@pytest.fixture
def adobe_sign_runner(
    db,
    cache,
    adobe_sign_secrets,
) -> ConnectorRunner:
    return ConnectorRunner(db, cache, "adobe_sign", adobe_sign_secrets)
