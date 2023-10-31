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
        # add the rest of your secrets here
        "data_export_key": pydash.get(saas_config, "ada_chatbot.data_export_key")
        or secrets["data_export_key"],
        "data_compliance_key": pydash.get(
            saas_config, "ada_chatbot.data_compliance_key"
        )
        or secrets["data_compliance_key"],
        "identity_email": pydash.get(saas_config, "ada_chatbot.identity_email")
        or secrets["identity_email"],
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
def ada_chatbot_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def ada_chatbot_erasure_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def ada_chatbot_erasure_data(
    ada_chatbot_erasure_identity_email: str,
) -> Generator:
    # create the data needed for erasure tests here
    yield {}


@pytest.fixture
def ada_chatbot_runner(
    db,
    cache,
    ada_chatbot_secrets,
    ada_chatbot_external_references,
    ada_chatbot_erasure_external_references,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "ada_chatbot",
        ada_chatbot_secrets,
        external_references=ada_chatbot_external_references,
        erasure_external_references=ada_chatbot_erasure_external_references,
    )
