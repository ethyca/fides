import uuid
from typing import Any, Dict

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
        "api_token": pydash.get(saas_config, "appsflyer.api_token")
        or secrets["api_token"],
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
    return {"appsflyer_user_id": uuid.uuid4()}


@pytest.fixture
def appsflyer_erasure_external_references() -> Dict[str, Any]:
    return {"appsflyer_user_id": uuid.uuid4()}


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
