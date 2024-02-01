from typing import Any, Dict, Generator

import pydash
import pytest

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("talkable")


@pytest.fixture(scope="session")
def talkable_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "talkable.domain")
        or secrets["domain"]
        # add the rest of your secrets here
    }


@pytest.fixture(scope="session")
def talkable_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "talkable.identity_email") or secrets["identity_email"]
    )


@pytest.fixture
def talkable_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def talkable_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def talkable_erasure_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def talkable_erasure_data(
    talkable_erasure_identity_email: str,
) -> Generator:
    # create the data needed for erasure tests here
    yield {}


@pytest.fixture
def talkable_runner(
    db,
    cache,
    talkable_secrets,
    talkable_external_references,
    talkable_erasure_external_references,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "talkable",
        talkable_secrets,
        external_references=talkable_external_references,
        erasure_external_references=talkable_erasure_external_references,
    )