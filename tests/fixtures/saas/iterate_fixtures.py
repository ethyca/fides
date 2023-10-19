from typing import Any, Dict, Generator

import pydash
import pytest

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("iterate")


@pytest.fixture(scope="session")
def iterate_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "iterate.domain") or secrets["domain"],
        # add the rest of your secrets here
        "email": pydash.get(saas_config, "iterate.email") or secrets["email"],
        "access_token": pydash.get(saas_config, "iterate.access_token")
        or secrets["access_token"],
        "company_id": pydash.get(saas_config, "iterate.company_id")
        or secrets["company_id"],
    }


@pytest.fixture(scope="session")
def iterate_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "iterate.identity_email") or secrets["identity_email"]
    )


@pytest.fixture
def iterate_erasure_identity_email(saas_config) -> str:
    #    return generate_random_email()
    return (
        pydash.get(saas_config, "iterate.erasure_identity_email")
        or secrets["identity_email"]
    )


@pytest.fixture
def iterate_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def iterate_erasure_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def iterate_erasure_data(
    iterate_erasure_identity_email: str,
) -> Generator:
    # create the data needed for erasure tests here
    yield {}


@pytest.fixture
def iterate_runner(
    db,
    cache,
    iterate_secrets,
    iterate_external_references,
    iterate_erasure_external_references,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "iterate",
        iterate_secrets,
        external_references=iterate_external_references,
        erasure_external_references=iterate_erasure_external_references,
    )
