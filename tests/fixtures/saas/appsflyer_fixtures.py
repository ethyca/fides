### Marc you are not done yet. Remove this comment only when you're DONE with this fixtures
### Do you have any extraneous fixtures?

from typing import Any, Dict, Generator

import pydash
import pytest

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("appsflyer")


@pytest.fixture(scope="session")
def appsflyer_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "appsflyer.domain") or secrets["domain"],
        "email": pydash.get(saas_config, "appsflyer.email") or secrets["email"],
        "identity_value": pydash.get(saas_config, "appsflyer.email")
        or secrets["identity_value"],
        "token": pydash.get(saas_config, "appsflyer.token") or secrets["token"],
    }


@pytest.fixture(scope="session")
def appsflyer_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "appsflyer.identity_email") or secrets["identity_email"]
    )


@pytest.fixture
def appsflyer_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def appsflyer_external_references() -> Dict[str, Any]:
    return {"appsflyer_user_id": "<uuid>"}


@pytest.fixture
def appsflyer_erasure_external_references() -> Dict[str, Any]:
    return {"appsflyer_user_id": "<uuid>"}


@pytest.fixture
def appsflyer_erasure_data(
    appsflyer_erasure_identity_email: str,
) -> Generator:
    # create the data needed for erasure tests here - create user steps go here if we have them
    yield {}


@pytest.fixture
def appsflyer_runner(
    db,
    cache,
    appsflyer_secrets,
    appsflyer_external_references,
    appsflyer_erasure_external_references,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "appsflyer",
        appsflyer_secrets,
        external_references=appsflyer_external_references,
        erasure_external_references=appsflyer_erasure_external_references,
    )
