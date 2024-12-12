"""Notes on the particulars for this Adyen integration
In this case, we aren't passing an identity email as Adyen's data protection endpoint requires a different value, the pspReference value which will be provided to us by our customer. 
The pspReference value itself will be provided by the customer
For reference this is the name of the value in the Adyen API data erasure endpoint
While we have hardcoded a value in this instance, it should be fairly straight-forward to make that a random value.
Naming considerations
adyen_external_references() & adyen_erasure_external_references()
both will need to use naming consistent with that in the config.yml 
"""

from typing import Any, Dict

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
        "api_key": pydash.get(saas_config, "adyen.api_key") or secrets["api_key"],
        "merchant_account": pydash.get(saas_config, "adyen.merchant_account")
        or secrets["merchant_account"],
        "psp_reference": pydash.get(saas_config, "adyen.psp_reference")
        or secrets["psp_reference"],
        "adyen_user_id": pydash.get(saas_config, "adyen.user_id") or secrets["user_id"],
    }


@pytest.fixture
def adyen_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def adyen_external_references() -> Dict[str, Any]:
    return {"adyen_user_id": "852617375522786K"}


@pytest.fixture
def adyen_erasure_external_references() -> Dict[str, Any]:
    return {"adyen_user_id": "852617375522786K"}


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
