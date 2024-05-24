from typing import Any, Dict, Generator

import pydash
import pytest

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("alchemer")


@pytest.fixture(scope="session")
def alchemer_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "alchemer.domain")
        or secrets["domain"]
        # add the rest of your secrets here
    }


@pytest.fixture(scope="session")
def alchemer_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "alchemer.identity_email") or secrets["identity_email"]
    )


@pytest.fixture
def alchemer_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def alchemer_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def alchemer_erasure_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def alchemer_erasure_data(
    alchemer_erasure_identity_email: str,
) -> Generator:
    # create the data needed for erasure tests here
    yield {}


@pytest.fixture
def alchemer_runner(
    db,
    cache,
    alchemer_secrets,
    alchemer_external_references,
    alchemer_erasure_external_references,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "alchemer",
        alchemer_secrets,
        external_references=alchemer_external_references,
        erasure_external_references=alchemer_erasure_external_references,
    )