from typing import Any, Dict, Generator

import pydash
import pytest

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("onesignal")


@pytest.fixture(scope="session")
def onesignal_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "onesignal.domain")
        or secrets["domain"],
        "api_key": pydash.get(saas_config, "onesignal.api_key") or secrets["api_key"],
        "app_id": pydash.get(saas_config, "onesignal.app_id") or secrets["app_id"],
        "player_id": pydash.get(saas_config, "onesignal.player_id")
        or secrets["player_id"],
    }


@pytest.fixture(scope="session")
def onesignal_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "onesignal.identity_email") or secrets["identity_email"]
    )


@pytest.fixture
def onesignal_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def onesignal_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def onesignal_erasure_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def onesignal_erasure_data(
    onesignal_erasure_identity_email: str,
) -> Generator:
    # create the data needed for erasure tests here
    yield {}


@pytest.fixture
def onesignal_runner(
    db,
    cache,
    onesignal_secrets,
    onesignal_external_references,
    onesignal_erasure_external_references,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "onesignal",
        onesignal_secrets,
        external_references=onesignal_external_references,
        erasure_external_references=onesignal_erasure_external_references,
    )