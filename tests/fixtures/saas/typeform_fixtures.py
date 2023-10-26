from typing import Any, Dict, Generator

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
        # add the rest of your secrets here
        "email": pydash.get(saas_config, "typeform.email") or secrets["email"],
        "identity_email": pydash.get(saas_config, "typeform.identity_email")
        or secrets["identity_email"],
        "account_id": pydash.get(saas_config, "typeform.account_id")
        or secrets["account_id"],
        "bearer-token": pydash.get(saas_config, "typeform.bearer-token")
        or secrets["bearer-token"],
        "delemail": pydash.get(saas_config, "typeform.delemail") or secrets["delemail"],
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
def typeform_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def typeform_erasure_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def typeform_erasure_data(
    typeform_erasure_identity_email: str,
) -> Generator:
    # create the data needed for erasure tests here
    yield {}


@pytest.fixture
def typeform_runner(
    db,
    cache,
    typeform_secrets,
    typeform_external_references,
    typeform_erasure_external_references,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "typeform",
        typeform_secrets,
        external_references=typeform_external_references,
        erasure_external_references=typeform_erasure_external_references,
    )
