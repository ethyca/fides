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
        "domain": pydash.get(saas_config, "snap.domain")
        or secrets["domain"],
        "snap_client_id": pydash.get(saas_config, "snap.snap_client_id")
        or secrets["snap_client_id"],
        "snap_client_secret_key": pydash.get(saas_config, "snap.snap_client_secret_key")
        or secrets["snap_client_secret_key"],
        "ad_account_id": pydash.get(saas_config, "snap.ad_account_id")
        or secrets["ad_account_id"],
        "access_token": pydash.get(saas_config, "snap.access_token")
        or secrets["access_token"],
    }


@pytest.fixture(scope="session")
def snap_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "snap.identity_email") or secrets["identity_email"]
    )


@pytest.fixture
def snap_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def snap_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def snap_erasure_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def snap_erasure_data(
    snap_erasure_identity_email: str,
) -> Generator:
    # create the data needed for erasure tests here
    yield {}


@pytest.fixture
def snap_runner(
    db,
    cache,
    snap_secrets,
    snap_external_references,
    snap_erasure_external_references,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "snap",
        snap_secrets,
        external_references=snap_external_references,
        erasure_external_references=snap_erasure_external_references,
    )
