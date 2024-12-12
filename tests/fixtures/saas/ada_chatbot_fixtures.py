from typing import Any, Dict, Generator

import pydash
import pytest

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("ada_chatbot")


@pytest.fixture(scope="session")
def ada_chatbot_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "ada_chatbot.domain") or secrets["domain"],
        "compliance_access_token": pydash.get(
            saas_config, "ada_chatbot.compliance_access_token"
        )
        or secrets["compliance_access_token"],
    }


@pytest.fixture(scope="session")
def ada_chatbot_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "ada_chatbot.identity_email")
        or secrets["identity_email"]
    )


@pytest.fixture
def ada_chatbot_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def ada_chatbot_runner(db, cache, ada_chatbot_secrets) -> ConnectorRunner:
    return ConnectorRunner(db, cache, "ada_chatbot", ada_chatbot_secrets)
