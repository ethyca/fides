from typing import Any, Dict, Generator

import pydash
import pytest

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("twilio_sms")


@pytest.fixture(scope="session")
def twilio_sms_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "twilio_sms.domain") or secrets["domain"],
        "twilio_account_sid": pydash.get(saas_config, "twilio_sms.twilio_account_sid") or secrets["twilio_account_sid"],
        "twilio_auth_token": pydash.get(saas_config, "twilio_sms.twilio_auth_token")
        or secrets["twilio_auth_token"],
    }


@pytest.fixture(scope="session")
def twilio_sms_identity_phone_number(saas_config) -> str:
    return (
        pydash.get(saas_config, "twilio_sms.identity_phone_number") or secrets["identity_phone_number"]
    )


@pytest.fixture
def twilio_sms_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def twilio_sms_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def twilio_sms_erasure_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def twilio_sms_erasure_data(
    twilio_sms_erasure_identity_email: str,
) -> Generator:
    # create the data needed for erasure tests here
    yield {}


@pytest.fixture
def twilio_sms_runner(
    db,
    cache,
    twilio_sms_secrets,
    twilio_sms_external_references,
    twilio_sms_erasure_external_references,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "twilio_sms",
        twilio_sms_secrets,
        external_references=twilio_sms_external_references,
        erasure_external_references=twilio_sms_erasure_external_references,
    )
