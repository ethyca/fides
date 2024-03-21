from typing import Any, Dict, Generator

import pydash
import pytest

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("adyen")


@pytest.fixture(scope="session")
def adyen_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "adyen.domain")
        or secrets["domain"]
        # add the rest of your secrets here
    }


@pytest.fixture(scope="session")
def adyen_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "adyen.identity_email") or secrets["identity_email"]
    )


@pytest.fixture
def adyen_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def adyen_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def adyen_erasure_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def adyen_erasure_data(
    adyen_erasure_identity_email: str,
) -> Generator:
    # create the data needed for erasure tests here
    yield {}


@pytest.fixture
def adyen_runner(
    db,
    cache,
    adyen_secrets,
    adyen_external_references,
    adyen_erasure_external_references,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "adyen",
        adyen_secrets,
        external_references=adyen_external_references,
        erasure_external_references=adyen_erasure_external_references,
    )