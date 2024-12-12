from typing import Any, Dict

import pydash
import pytest

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("typeform")


@pytest.fixture(scope="session")
def typeform_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "typeform.domain") or secrets["domain"],
        "account_id": pydash.get(saas_config, "typeform.account_id")
        or secrets["account_id"],
        "api_key": pydash.get(saas_config, "typeform.api_key") or secrets["api_key"],
    }


@pytest.fixture(scope="session")
def typeform_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "typeform.identity_email") or secrets["identity_email"]
    )


@pytest.fixture
def typeform_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def typeform_runner(db, cache, typeform_secrets) -> ConnectorRunner:
    return ConnectorRunner(db, cache, "typeform", typeform_secrets)
