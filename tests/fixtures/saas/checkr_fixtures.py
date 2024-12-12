import time
from typing import Any, Dict, Generator

import pydash
import pytest
import requests
from requests.auth import HTTPBasicAuth

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("checkr")


@pytest.fixture(scope="session")
def checkr_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "checkr.domain") or secrets["domain"],
        "api_key_secret": pydash.get(saas_config, "checkr.api_key_secret")
        or secrets["api_key_secret"],
    }


@pytest.fixture(scope="session")
def checkr_identity_email(saas_config) -> str:
    return pydash.get(saas_config, "checkr.identity_email") or secrets["identity_email"]


@pytest.fixture
def checkr_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def checkr_erasure_data(
    checkr_secrets,
    checkr_erasure_identity_email: str,
) -> Generator:
    candidate_url = f"https://{checkr_secrets['domain']}/v1/candidates"
    auth = HTTPBasicAuth(checkr_secrets["api_key_secret"], "")
    body = {
        "first_name": "ethycafirst",
        "middle_name": "at",
        "no_middle_name": "false",
        "last_name": "ethycalast",
        "mother_maiden_name": "Smith",
        "email": checkr_erasure_identity_email,
        "phone": "5555555555",
        "zipcode": "90402",
        "dob": "1972-01-20",
        "driver_license_number": "F2101655",
        "driver_license_state": "CA",
        "previous_driver_license_number": "F1500739",
        "previous_driver_license_state": "MD",
        "copy_requested": "false",
        "custom_id": "HRIS-21",
        "metadata": {},
        "work_locations": [{"country": "US", "state": "CA", "city": "San Francisco"}],
    }
    response = requests.post(candidate_url, json=body, auth=auth)
    assert response.ok
    json_response = response.json()
    assert json_response["id"] is not None
    time.sleep(5)  # required wait for the candidate to be created
    return


@pytest.fixture
def checkr_runner(
    db,
    cache,
    checkr_secrets,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "checkr",
        checkr_secrets,
    )
