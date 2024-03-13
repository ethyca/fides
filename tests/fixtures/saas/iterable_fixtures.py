from typing import Any, Dict, Generator

import pydash
import pytest

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("iterable")


@pytest.fixture(scope="session")
def iterable_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "iterable.domain")
        or secrets["domain"],
        "Api-Key": pydash.get(saas_config, "iterable.Api-Key") or  secrets["Api-Key"],
        "email": pydash.get(saas_config, "iterable.email") or  secrets["email"],
        # add the rest of your secrets here
    }


@pytest.fixture(scope="session")
def iterable_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "iterable.identity_email") or secrets["identity_email"]
    )


@pytest.fixture
def iterable_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def iterable_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def iterable_erasure_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def iterable_erasure_data(
    iterable_erasure_identity_email: str,
) -> Generator:
    # create the data needed for erasure tests here
    yield {}


@pytest.fixture
def iterable_runner(
    db,
    cache,
    iterable_secrets,
    iterable_external_references,
    iterable_erasure_external_references,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "iterable",
        iterable_secrets,
        external_references=iterable_external_references,
        erasure_external_references=iterable_erasure_external_references,
    )