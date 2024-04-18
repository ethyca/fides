from typing import Any, Dict, Generator

import pydash
import pytest

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("marigold")


@pytest.fixture(scope="session")
def marigold_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "marigold.domain")
        or secrets["domain"]
        # add the rest of your secrets here
    }


@pytest.fixture(scope="session")
def marigold_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "marigold.identity_email") or secrets["identity_email"]
    )


@pytest.fixture
def marigold_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def marigold_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def marigold_erasure_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def marigold_erasure_data(
    marigold_erasure_identity_email: str,
) -> Generator:
    # create the data needed for erasure tests here
    yield {}


@pytest.fixture
def marigold_runner(
    db,
    cache,
    marigold_secrets,
    marigold_external_references,
    marigold_erasure_external_references,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "marigold",
        marigold_secrets,
        external_references=marigold_external_references,
        erasure_external_references=marigold_erasure_external_references,
    )