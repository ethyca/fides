from typing import Any, Dict, Generator

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
        "domain": pydash.get(saas_config, "gong.domain")
        or secrets["domain"]
        # add the rest of your secrets here
    }


@pytest.fixture(scope="session")
def gong_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "gong.identity_email") or secrets["identity_email"]
    )


@pytest.fixture
def gong_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def gong_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def gong_erasure_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def gong_erasure_data(
    gong_erasure_identity_email: str,
) -> Generator:
    # create the data needed for erasure tests here
    yield {}


@pytest.fixture
def gong_runner(
    db,
    cache,
    gong_secrets,
    gong_external_references,
    gong_erasure_external_references,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "gong",
        gong_secrets,
        external_references=gong_external_references,
        erasure_external_references=gong_erasure_external_references,
    )