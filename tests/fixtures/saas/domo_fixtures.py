from typing import Any, Dict, Generator

import pydash
import pytest
import requests
from faker import Faker
from requests import Response
from sqlalchemy.orm import Session
from starlette.status import HTTP_204_NO_CONTENT

from fides.api.cryptography import cryptographic_util
from fides.api.db import session
from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.sql_models import Dataset as CtlDataset
from fides.api.util.saas_util import (
    load_config_with_replacement,
    load_dataset_with_replacement,
)
from tests.ops.test_helpers.saas_test_utils import poll_for_existence
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("domo")
faker = Faker()


@pytest.fixture(scope="session")
def domo_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "domo.domain") or secrets["domain"],
        "client_id": pydash.get(saas_config, "domo.client_id") or secrets["client_id"],
        "client_secret": pydash.get(saas_config, "domo.client_secret")
        or secrets["client_secret"],
    }


@pytest.fixture(scope="session")
def domo_identity_email(saas_config):
    return pydash.get(saas_config, "domo.identity_email") or secrets["identity_email"]


@pytest.fixture(scope="session")
def domo_erasure_identity_email():
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture(scope="session")
def domo_token(domo_secrets) -> str:
    body = {"grant_type": "client_credentials"}
    url = f"https://{domo_secrets['domain']}/oauth/token"
    response = requests.post(
        url, body, auth=(domo_secrets["client_id"], domo_secrets["client_secret"])
    )
    return response.json()["access_token"]


@pytest.fixture
def domo_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/domo_config.yml",
        "<instance_fides_key>",
        "domo_instance",
    )


@pytest.fixture
def domo_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/domo_dataset.yml",
        "<instance_fides_key>",
        "domo_instance",
    )[0]


@pytest.fixture(scope="function")
def domo_connection_config(
    db: session,
    domo_config,
    domo_secrets,
) -> Generator:
    fides_key = domo_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": domo_secrets,
            "saas_config": domo_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def domo_dataset_config(
    db: Session,
    domo_connection_config: ConnectionConfig,
    domo_dataset: Dict[str, Any],
) -> Generator:
    fides_key = domo_dataset["fides_key"]
    domo_connection_config.name = fides_key
    domo_connection_config.key = fides_key
    domo_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, domo_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": domo_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


class DomoTestClient:
    def __init__(self, domo_token, domo_connection_config: ConnectionConfig):
        self.domo_secrets = domo_connection_config.secrets
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {domo_token}",
        }
        self.base_url = f"https://{self.domo_secrets['domain']}/v1"

    def create_user(self, email_address: str) -> Response:
        # create a new user in Domo
        body = {
            "email": email_address,
            "alternateEmail": email_address,
            "name": f"test_connector_ethyca",
            "phone": faker.phone_number(),
            "title": "Software Engineer",
            "role": "Participant",  # (available roles are: 'Admin', 'Privileged', 'Participant')
        }
        url = f"{self.base_url}/users?sendInvite=false"
        user_response: Response = requests.post(
            url=url, json=body, headers=self.headers
        )
        return user_response

    def get_user(self, user_id: str) -> Response:
        # get user created for erasure purposes
        url = f"{self.base_url}/users/{user_id}"
        user_response: Response = requests.get(url=url, headers=self.headers)
        return user_response

    def delete_user(self, user_id) -> Response:
        # delete user created for erasure purposes
        url = f"{self.base_url}/users/{user_id}"
        user_response: Response = requests.delete(url=url, headers=self.headers)
        return user_response


@pytest.fixture(scope="function")
def domo_test_client(domo_connection_config: DomoTestClient, domo_token) -> Generator:
    test_client = DomoTestClient(
        domo_token, domo_connection_config=domo_connection_config
    )
    yield test_client


def _user_exists(user_id: str, domo_test_client: DomoTestClient) -> Any:
    """check if the user exists in the domo"""
    user_response = domo_test_client.get_user(user_id)
    user = user_response.json()
    # it return status 200 if user exists with given id otherwise 400
    if user_response.ok and user:
        return user


@pytest.fixture(scope="function")
def domo_create_erasure_data(
    domo_test_client: DomoTestClient,
    domo_erasure_identity_email: str,
) -> Generator:
    """
    Creates a dynamic test data record for erasure tests.
        1) create a new user
    """
    # 1) create a new user
    user_response = domo_test_client.create_user(domo_erasure_identity_email)
    user = user_response.json()
    user_id = user["id"]

    error_message = f"user with user id [{user_id}] could not be added to Domo"
    poll_for_existence(
        _user_exists,
        (user_id, domo_test_client),
        error_message=error_message,
    )
    yield user_id
    # delete the user
    user_response = domo_test_client.delete_user(user_id)
    # Returns a 204 response code when successful or error based on whether the user ID being valid.
    assert user_response.status_code == HTTP_204_NO_CONTENT
