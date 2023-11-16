from typing import Any, Dict, Generator

import pydash
import pytest

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("statsig")


@pytest.fixture(scope="session")
def statsig_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "statsig.domain") or secrets["domain"],
        # add the rest of your secrets here
        "email": pydash.get(saas_config, "statsig.email") or secrets["email"],
        "user_id": pydash.get(saas_config, "statsig.user_id") or secrets["user_id"],
        "STATSIG-CONSOLE-API-KEY": pydash.get(
            saas_config, "statsig.STATSIG-CONSOLE-API-KEY"
        )
        or secrets["STATSIG-CONSOLE-API-KEY"],
        "STATSIG-SERVER-API-KEY": pydash.get(
            saas_config, "statsig.STATSIG-SERVER-API-KEY"
        )
        or secrets["STATSIG-SERVER-API-KEY"],
    }


@pytest.fixture(scope="session")
def statsig_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "statsig.identity_email") or secrets["identity_email"]
    )


@pytest.fixture
def statsig_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def statsig_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def statsig_erasure_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def statsig_erasure_data(
    statsig_erasure_identity_email: str,
) -> Generator:
    # create the data needed for erasure tests here
    yield {}


@pytest.fixture
def statsig_runner(
    db,
    cache,
    statsig_secrets,
    statsig_external_references,
    statsig_erasure_external_references,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "statsig",
        statsig_secrets,
        external_references=statsig_external_references,
        erasure_external_references=statsig_erasure_external_references,
    )
