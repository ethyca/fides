from typing import Any, Dict, Generator

import pydash
import pytest

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("qualtrics")


@pytest.fixture(scope="session")
def qualtrics_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "qualtrics.domain") or secrets["domain"],
        # add the rest of your secrets here
        "api_key": pydash.get(saas_config, "qualtrics.api_key") or secrets["api_key"],
        "identity_email": pydash.get(saas_config, "qualtrics.identity_email")
        or secrets["identity_email"],
    }


@pytest.fixture(scope="session")
def qualtrics_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "qualtrics.identity_email") or secrets["identity_email"]
    )


@pytest.fixture
def qualtrics_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def qualtrics_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def qualtrics_erasure_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def qualtrics_erasure_data(
    qualtrics_erasure_identity_email: str,
) -> Generator:
    # create the data needed for erasure tests here
    yield {}


@pytest.fixture
def qualtrics_runner(
    db,
    cache,
    qualtrics_secrets,
    qualtrics_external_references,
    qualtrics_erasure_external_references,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "qualtrics",
        qualtrics_secrets,
        external_references=qualtrics_external_references,
        erasure_external_references=qualtrics_erasure_external_references,
    )
