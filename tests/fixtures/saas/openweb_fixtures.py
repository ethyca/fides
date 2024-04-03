from typing import Any, Dict, Generator

import pydash
import pytest

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("openweb")


@pytest.fixture(scope="session")
def openweb_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "openweb.domain")
        or secrets["domain"],
        "api_key": pydash.get(saas_config, "openweb.api_key")
        or secrets["api_key"]
        # add the rest of your secrets here
    }


# @pytest.fixture(scope="session")
# def openweb_identity_email(saas_config) -> str:
#     return (
#         pydash.get(saas_config, "openweb.identity_email") or secrets["identity_email"]
#     )


@pytest.fixture
def openweb_erasure_identity_email() -> str:
    return generate_random_email()

# we do need a means of creating a random 'primay_key' and using that for the erasure request. THere is a difference in how the endpoint responds when sent an invalid (or already used) primary_key. A saved 
@pytest.fixture
def openweb_external_references() -> Dict[str, Any]:
    return {"openweb_user_id": "deletemetest"}


@pytest.fixture
def openweb_erasure_external_references() -> Dict[str, Any]:
    return {"openweb_user_id": "deletemetest"}


@pytest.fixture
def openweb_erasure_data(
    openweb_erasure_identity_email: str,
) -> Generator:
    '''
    # create the data needed for erasure tests here
    #### can we put the logic here to send out a request to the register user endpoint to create a random user to use? For the primary key value we need we can use any random string of alpha-numeric characters
    yield {}
    '''

@pytest.fixture
def openweb_runner(
    db,
    cache,
    openweb_secrets,
    openweb_external_references,
    openweb_erasure_external_references,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "openweb",
        openweb_secrets,
        external_references=openweb_external_references,
        erasure_external_references=openweb_erasure_external_references,
    )