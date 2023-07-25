from typing import Any, Dict, Generator

import pydash
import pytest

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets
from tests.ops.test_helpers.saas_test_utils import poll_for_existence

secrets = get_secrets("recurly")


@pytest.fixture(scope="session")
def recurly_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "recurly.domain")
        or secrets["domain"],
        "username": pydash.get(saas_config, "recurly.username") or secrets["username"],
        "accept_header": pydash.get(saas_config, "recurly.accept_header") or secrets["accept_header"],        
    }


@pytest.fixture(scope="session")
def recurly_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "recurly.identity_email") or secrets["identity_email"]
    )


@pytest.fixture
def recurly_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def recurly_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def recurly_erasure_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def recurly_erasure_data(
    recurly_erasure_identity_email: str,
) -> Generator:
    
    yield {}


@pytest.fixture
def recurly_runner(
    db,
    cache,
    recurly_secrets,
    recurly_external_references,
    recurly_erasure_external_references,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "recurly",
        recurly_secrets,
        external_references=recurly_external_references,
        erasure_external_references=recurly_erasure_external_references,
    )