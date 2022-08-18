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
from starlette.status import HTTP_204_NO_CONTENT

from tests.ops.fixtures.application_fixtures import load_dataset
from tests.ops.fixtures.saas_example_fixtures import load_config
from tests.ops.test_helpers.saas_test_utils import poll_for_existence
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("auth0")


@pytest.fixture(scope="function")
def auth0_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "auth0.domain") or secrets["domain"],
        "access_token": pydash.get(saas_config, "auth0.access_token")
        or secrets["access_token"],
    }


@pytest.fixture(scope="function")
def auth0_identity_email(saas_config):
    return pydash.get(saas_config, "auth0.identity_email") or secrets["identity_email"]


@pytest.fixture(scope="session")
def auth0_erasure_identity_email():
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture
def auth0_config() -> Dict[str, Any]:
    return load_config("data/saas/config/auth0_config.yml")


@pytest.fixture
def auth0_dataset() -> Dict[str, Any]:
    return load_dataset("data/saas/dataset/auth0_dataset.yml")[0]


@pytest.fixture(scope="function")
def auth0_connection_config(db: session, auth0_config, auth0_secrets) -> Generator:
    fides_key = auth0_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": auth0_secrets,
            "saas_config": auth0_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def auth0_dataset_config(
    db: Session,
    auth0_connection_config: ConnectionConfig,
    auth0_dataset: Dict[str, Any],
) -> Generator:
    fides_key = auth0_dataset["fides_key"]
    auth0_connection_config.name = fides_key
    auth0_connection_config.key = fides_key
    auth0_connection_config.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": auth0_connection_config.id,
            "fides_key": fides_key,
            "dataset": auth0_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)


@pytest.fixture(scope="function")
def auth0_access_data(
    auth0_connection_config, auth0_identity_email, auth0_secrets
) -> Generator:
    """
    Updates user password to have some data in user_logs
    """

    base_url = f"https://{auth0_secrets['domain']}"

    headers = {"Authorization": f"Bearer {auth0_secrets['access_token']}"}
    user_response = requests.get(
        url=f"{base_url}/api/v2/users-by-email?email={auth0_identity_email}",
        headers=headers,
    )
    assert user_response.ok
    user = user_response.json()
    user_id = user[0]["user_id"]

    body = {
        "connection": "Username-Password-Authentication",
        "password": f"pass+{cryptographic_util.generate_secure_random_string(8)}+test",
    }
    users_response = requests.patch(
        url=f"{base_url}/api/v2/users/{user_id}", json=body, headers=headers
    )
    assert users_response.ok

    yield user


@pytest.fixture(scope="function")
def auth0_erasure_data(
    auth0_connection_config, auth0_erasure_identity_email, auth0_secrets
) -> Generator:
    """
    Creates a dynamic test data record for erasure tests.
    Yields user ID as this may be useful to have in test scenarios
    """

    base_url = f"https://{auth0_secrets['domain']}"
    # Create user
    body = {
        "email": auth0_erasure_identity_email,
        "blocked": False,
        "email_verified": False,
        "app_metadata": {},
        "given_name": "John",
        "family_name": "Doe",
        "name": "John Doe",
        "nickname": "Johnny",
        "picture": "https://secure.gravatar.com/avatar/15626c5e0c749cb912f9d1ad48dba440?s=480&r=pg&d=https%3A%2F%2Fssl.gstatic.com%2Fs2%2Fprofiles%2Fimages%2Fsilhouette80.png",
        "connection": "Username-Password-Authentication",
        "password": "P@ssword123",
        "verify_email": False,
    }
    headers = {"Authorization": f"Bearer {auth0_secrets['access_token']}"}
    users_response = requests.post(
        url=f"{base_url}/api/v2/users", json=body, headers=headers
    )
    user = users_response.json()
    assert users_response.ok
    error_message = (
        f"User with email {auth0_erasure_identity_email} could not be added to auth0"
    )
    poll_for_existence(
        _user_exists,
        (auth0_erasure_identity_email, auth0_secrets),
        error_message=error_message,
    )
    yield user

    user_id = user["user_id"]
    # Deleting user after verifying update request
    user_delete_response = requests.delete(
        url=f"{base_url}/api/v2/users/{user_id}",
        headers=headers,
    )
    # we expect 204 if user doesn't exist
    assert user_delete_response.status_code == HTTP_204_NO_CONTENT


def _user_exists(auth0_erasure_identity_email: str, auth0_secrets):
    """
    Confirm whether user exists by calling user search by email api and comparing resulting firstname str.
    Returns user ID if it exists, returns None if it does not.
    """
    base_url = f"https://{auth0_secrets['domain']}"
    headers = {
        "Authorization": f"Bearer {auth0_secrets['access_token']}",
    }

    user_response = requests.get(
        url=f"{base_url}/api/v2/users-by-email?email={auth0_erasure_identity_email}",
        headers=headers,
    )

    # we expect 404 if user doesn't exist
    if 404 == user_response.status_code:
        return None

    return user_response.json()
