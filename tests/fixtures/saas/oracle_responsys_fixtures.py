from typing import Any, Dict, Generator

import pydash
import pytest

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("oracle_responsys")


@pytest.fixture(scope="session")
def oracle_responsys_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "oracle_responsys.domain")
        or secrets["domain"]
        # add the rest of your secrets here
    }


@pytest.fixture(scope="session")
def oracle_responsys_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "oracle_responsys.identity_email") or secrets["identity_email"]
    )


@pytest.fixture
def oracle_responsys_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def oracle_responsys_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def oracle_responsys_erasure_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def oracle_responsys_erasure_data(
    oracle_responsys_erasure_identity_email: str,
) -> Generator:
    # create the data needed for erasure tests here
    yield {}


@pytest.fixture
def oracle_responsys_runner(
    db,
    cache,
    oracle_responsys_secrets,
    oracle_responsys_external_references,
    oracle_responsys_erasure_external_references,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "oracle_responsys",
        oracle_responsys_secrets,
        external_references=oracle_responsys_external_references,
        erasure_external_references=oracle_responsys_erasure_external_references,
    )