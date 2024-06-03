from typing import Any, Dict, Generator

import pydash
import pytest

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("greenhouse_harvest")


@pytest.fixture(scope="session")
def greenhouse_harvest_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "greenhouse_harvest.domain")
        or secrets["domain"],
        "api_key": pydash.get(saas_config, "greenhouse_harvest.api_key")
        or secrets["api_key"],
        "greenhouse_user_id": pydash.get(saas_config, "greenhouse_harvest.greenhouse_user_id")
        or secrets["greenhouse_user_id"],
        ## remove below
        "user_id": pydash.get(saas_config, "greenhouse_harvest.user_id")
        or secrets["user_id"]
    }


@pytest.fixture(scope="session")
def greenhouse_harvest_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "greenhouse_harvest.identity_email") or secrets["identity_email"]
    )


@pytest.fixture
def greenhouse_harvest_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def greenhouse_harvest_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def greenhouse_harvest_erasure_external_references() -> Dict[str, Any]:
    return {"greenhouse_user_id":"4054939008"}


@pytest.fixture
def greenhouse_harvest_erasure_data(
    greenhouse_harvest_erasure_identity_email: str,
) -> Generator:
    # create the data needed for erasure tests here
    yield {}


@pytest.fixture
def greenhouse_harvest_runner(
    db,
    cache,
    greenhouse_harvest_secrets,
    greenhouse_harvest_external_references,
    greenhouse_harvest_erasure_external_references,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "greenhouse_harvest",
        greenhouse_harvest_secrets,
        external_references=greenhouse_harvest_external_references,
        erasure_external_references=greenhouse_harvest_erasure_external_references,
    )
