from typing import Any, Dict, Generator

import pydash
import pytest

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("adyen")


@pytest.fixture(scope="session")
def adyen_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain_management": pydash.get(saas_config, "adyen.domain_management")
        or secrets["domain_management"],
        "domain_ca": pydash.get(saas_config, "adyen.domain_ca") or secrets["domain_ca"],
        "api_key": pydash.get(saas_config, "adyen.api_key") or secrets["adyen.api_key"],
        "merchant_account": pydash.get(saas_config, "adyen.merchant_account")
        or secrets["adyen.merchant_account"],
        "psp_reference": pydash.get(saas_config, "adyen.psp_reference")
        or secrets["adyen.pspReference"],
        "adyen_user_id": pydash.get(saas_config, "adyen.user_id")
        or secrets["adyen.user_id"],
        # add the rest of your secrets here
    }


### In this case, we aren't passing an identity email as Adyen's data protection endpoint requires a different value, the pspReference value which will be provided to us by our customer.
# @pytest.fixture(scope="session")
# def adyen_identity_email(saas_config) -> str:
#     return pydash.get(saas_config, "adyen.identity_email") or secrets["identity_email"]


@pytest.fixture
def adyen_erasure_identity_email() -> str:
    return generate_random_email()


### note -- not sure why we were able to remove this in statsig - it could be that we don't really need a full item to delete, will comment out for now.
## This fixture needs to have naming to match that in the config.yml
@pytest.fixture
def adyen_external_references() -> Dict[str, Any]:
    return {"adyen_user_id": "852617375522786K"}


### I think the pspReference could be random as we will get a 200 back even if the pspReference doesn't exist
## This also needs to reference the names used in the config.yml
@pytest.fixture
def adyen_erasure_external_references() -> Dict[str, Any]:
    return {"adyen_user_id": "852617375522786K"}


### Given how the erasure works, it isn't required that we have data in the system to test the deletion as we're just looking for the response to be a 200
# @pytest.fixture
# def adyen_erasure_data(
#     adyen_erasure_identity_email: str,
# ) -> Generator:
#     # create the data needed for erasure tests here
#     yield {}


@pytest.fixture
def adyen_runner(
    db,
    cache,
    adyen_secrets,
    adyen_external_references,
    adyen_erasure_external_references,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "adyen",
        adyen_secrets,
        external_references=adyen_external_references,
        erasure_external_references=adyen_erasure_external_references,
    )
