from typing import Any, Dict, Generator

import pydash
import pytest
import requests
from fideslib.cryptography import cryptographic_util
from fideslib.db import session
from fidesops.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fidesops.ops.models.datasetconfig import DatasetConfig
from sqlalchemy.orm import Session
from starlette.status import HTTP_404_NOT_FOUND

from tests.ops.fixtures.application_fixtures import load_dataset
from tests.ops.fixtures.saas_example_fixtures import load_config
from tests.ops.test_helpers.saas_test_utils import poll_for_existence
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("logi_id")


@pytest.fixture(scope="session")
def logi_id_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "logi_id.domain") or secrets["domain"],
        "client_id": pydash.get(saas_config, "logi_id.client_id")
        or secrets["client_id"],
        "client_secret": pydash.get(saas_config, "logi_id.client_secret")
        or secrets["client_secret"],
    }


@pytest.fixture(scope="session")
def logi_id_identity_email(saas_config):
    return (
        pydash.get(saas_config, "logi_id.identity_email") or secrets["identity_email"]
    )


@pytest.fixture(scope="session")
def logi_id_erasure_identity_email():
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture
def logi_id_config() -> Dict[str, Any]:
    return load_config("data/saas/config/logi_id_config.yml")


@pytest.fixture
def logi_id_dataset() -> Dict[str, Any]:
    return load_dataset("data/saas/dataset/logi_id_dataset.yml")[0]


@pytest.fixture(scope="function")
def logi_id_connection_config(
    db: session,
    logi_id_config,
    logi_id_secrets,
) -> Generator:
    fides_key = logi_id_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": logi_id_secrets,
            "saas_config": logi_id_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def logi_id_dataset_config(
    db: Session,
    logi_id_connection_config: ConnectionConfig,
    logi_id_dataset: Dict[str, Any],
) -> Generator:

    fides_key = logi_id_dataset["fides_key"]
    logi_id_connection_config.name = fides_key
    logi_id_connection_config.key = fides_key
    logi_id_connection_config.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": logi_id_connection_config.id,
            "fides_key": fides_key,
            "dataset": logi_id_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)


@pytest.fixture(scope="function")
def logi_id_erasure_data(
    logi_id_connection_config: ConnectionConfig, logi_id_erasure_identity_email: str
) -> Generator:
    """
    Creates a dynamic test data record for erasure tests.
    Yields User ID as this may be useful to have in test scenarios
    """
    logi_id_secrets = logi_id_connection_config.secrets
    base_url = f"https://{logi_id_secrets['domain']}"
    body = {
        "email": logi_id_erasure_identity_email,
        "password": "k1UhfAg8hBu",
        "email_verified": True,
        "name": "Test",
        "client_id": logi_id_secrets["client_id"],
        "given_name": "First Name",
        "family_name": "Last Name",
    }
    users_response = requests.post(
        url=f"{base_url}/websso/signup?response_type=code&redirect_uri={base_url}/version",
        json=body,
    )
    user = users_response.json()
    assert users_response.ok
    error_message = f"User with email {logi_id_erasure_identity_email} could not be added to Logi ID"
    user = poll_for_existence(
        user_exists,
        (logi_id_erasure_identity_email, logi_id_secrets),
        error_message=error_message,
    )
    yield user


def user_exists(logi_id_erasure_identity_email: str, logi_id_secrets):
    """
    Confirm whether user exists by calling user search by email api
    Returns user ID if it exists, returns None if it does not.
    """
    base_url = f"https://{logi_id_secrets['domain']}"
    auth = logi_id_secrets["client_id"], logi_id_secrets["client_secret"]

    user_response = requests.get(
        url=f"{base_url}/identity/search?email={logi_id_erasure_identity_email}",
        auth=auth,
    )
    # we expect 404 if user doesn't exist
    if HTTP_404_NOT_FOUND == user_response.status_code:
        return None
    return user_response.json()
