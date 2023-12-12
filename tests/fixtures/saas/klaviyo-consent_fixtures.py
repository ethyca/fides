from typing import Any, Dict, Generator

import pydash
import pytest

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("klaviyo-consent")


@pytest.fixture(scope="session")
def klaviyo-consent_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "klaviyo-consent.domain")
        or secrets["domain"]
        # add the rest of your secrets here
    }


@pytest.fixture(scope="session")
def klaviyo-consent_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "klaviyo-consent.identity_email") or secrets["identity_email"]
    )


@pytest.fixture
def klaviyo-consent_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def klaviyo-consent_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def klaviyo-consent_erasure_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def klaviyo-consent_erasure_data(
    klaviyo-consent_erasure_identity_email: str,
) -> Generator:
    # create the data needed for erasure tests here
    yield {}


@pytest.fixture
def klaviyo-consent_runner(
    db,
    cache,
    klaviyo-consent_secrets,
    klaviyo-consent_external_references,
    klaviyo-consent_erasure_external_references,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "klaviyo-consent",
        klaviyo-consent_secrets,
        external_references=klaviyo-consent_external_references,
        erasure_external_references=klaviyo-consent_erasure_external_references,
    )