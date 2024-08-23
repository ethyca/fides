from typing import Any, Dict, Generator

import pydash
import pytest

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("snap")


@pytest.fixture(scope="session")
def snap_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "snap.domain") or secrets["domain"],
        "client_id": pydash.get(saas_config, "snap.client_id")
        or secrets["snap_client_id"],
        "client_secret": pydash.get(saas_config, "snap.client_secret")
        or secrets["snap_client_secret"],
        "redirect_uri": pydash.get(saas_config, "snap.redirect_uri")
        or secrets["redirect_uri"],
        "access_token": pydash.get(saas_config, "snap.access_token")
        or secrets["access_token"],
    }


@pytest.fixture(scope="session")
def snap_identity_email(saas_config) -> str:
    return pydash.get(saas_config, "snap.identity_email") or secrets["identity_email"]


@pytest.fixture
def snap_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def snap_runner(db, cache, snap_secrets) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "snap",
        snap_secrets,
    )
