from typing import Any, Dict, Generator

import pydash
import pytest
import requests
from sqlalchemy.orm import Session
from sqlalchemy_utils.functions import create_database, database_exists, drop_database

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
from tests.ops.test_helpers.db_utils import seed_postgres_data
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("fullstory")


@pytest.fixture(scope="function")
def fullstory_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "fullstory.domain") or secrets["domain"],
        "api_key": pydash.get(saas_config, "fullstory.api_key") or secrets["api_key"],
        "fullstory_user_id": {
            "dataset": "fullstory_postgres",
            "field": "fullstory_users.fullstory_user_id",
            "direction": "from",
        },
    }


@pytest.fixture(scope="function")
def fullstory_identity_email(saas_config):
    return (
        pydash.get(saas_config, "fullstory.identity_email") or secrets["identity_email"]
    )


@pytest.fixture(scope="session")
def fullstory_erasure_identity_email(saas_config):
    return (
        pydash.get(saas_config, "fullstory.erasure_identity_email")
        or secrets["erasure_identity_email"]
    )


@pytest.fixture(scope="session")
def fullstory_erasure_identity_id(saas_config):
    return (
        pydash.get(saas_config, "fullstory.erasure_identity_id")
        or secrets["erasure_identity_id"]
    )


@pytest.fixture
def fullstory_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/fullstory_config.yml",
        "<instance_fides_key>",
        "fullstory_instance",
    )


@pytest.fixture
def fullstory_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/fullstory_dataset.yml",
        "<instance_fides_key>",
        "fullstory_instance",
    )[0]


@pytest.fixture(scope="function")
def fullstory_connection_config(
    db: session, fullstory_config, fullstory_secrets
) -> Generator:
    fides_key = fullstory_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": fullstory_secrets,
            "saas_config": fullstory_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def fullstory_dataset_config(
    db: Session,
    fullstory_connection_config: ConnectionConfig,
    fullstory_dataset: Dict[str, Any],
) -> Generator:
    fides_key = fullstory_dataset["fides_key"]
    fullstory_connection_config.name = fides_key
    fullstory_connection_config.key = fides_key
    fullstory_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, fullstory_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": fullstory_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture()
def fullstory_postgres_dataset() -> Dict[str, Any]:
    return {
        "fides_key": "fullstory_postgres",
        "name": "Fullstory Postgres",
        "description": "Lookup for Fullstory User IDs",
        "collections": [
            {
                "name": "fullstory_users",
                "fields": [
                    {
                        "name": "email",
                        "data_categories": ["user.contact.email"],
                        "fidesops_meta": {"data_type": "string", "identity": "email"},
                    },
                    {
                        "name": "fullstory_user_id",
                        "fidesops_meta": {"data_type": "string"},
                    },
                ],
            }
        ],
    }


@pytest.fixture
def fullstory_postgres_dataset_config(
    connection_config: ConnectionConfig,
    fullstory_postgres_dataset: Dict[str, Any],
    db: Session,
) -> Generator:
    fides_key = fullstory_postgres_dataset["fides_key"]
    connection_config.name = fides_key
    connection_config.key = fides_key
    connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, fullstory_postgres_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture(scope="function")
def fullstory_postgres_db(postgres_integration_session):
    postgres_integration_session = seed_postgres_data(
        postgres_integration_session,
        "./tests/fixtures/saas/external_datasets/fullstory.sql",
    )
    yield postgres_integration_session
    drop_database(postgres_integration_session.bind.url)


class FullstoryTestClient:
    headers: object = {}
    base_url: str = ""

    def __init__(self, connection_config_fullstory: ConnectionConfig):
        fullstory_secrets = connection_config_fullstory.secrets
        self.headers = {
            "Authorization": f"Basic {fullstory_secrets['api_key']}",
        }
        self.base_url = f"https://{fullstory_secrets['domain']}"

    def get_user(self, user_id: str) -> requests.Response:
        user_response: requests.Response = requests.get(
            url=f"{self.base_url}/users/v1/individual/{user_id}", headers=self.headers
        )
        return user_response

    def update_user(self, user_id: str, user_data) -> requests.Response:
        user_response: requests.Response = requests.post(
            url=f"{self.base_url}/users/v1/individual/{user_id}/customvars",
            json=user_data,
            headers=self.headers,
        )
        return user_response


@pytest.fixture(scope="function")
def fullstory_postgres_erasure_db(
    postgres_integration_session,
    fullstory_erasure_identity_email,
    fullstory_erasure_identity_id,
):
    if database_exists(postgres_integration_session.bind.url):
        # Postgres cannot drop databases from within a transaction block, so
        # we should drop the DB this way instead
        drop_database(postgres_integration_session.bind.url)
    create_database(postgres_integration_session.bind.url)

    create_table_query = "CREATE TABLE public.fullstory_users (email CHARACTER VARYING(100) PRIMARY KEY,fullstory_user_id CHARACTER VARYING(100));"
    postgres_integration_session.execute(create_table_query)
    insert_query = (
        "INSERT INTO public.fullstory_users VALUES('"
        + fullstory_erasure_identity_email
        + "', '"
        + fullstory_erasure_identity_id
        + "')"
    )
    postgres_integration_session.execute(insert_query)

    yield postgres_integration_session
    drop_database(postgres_integration_session.bind.url)


@pytest.fixture(scope="function")
def fullstory_test_client(
    fullstory_connection_config: FullstoryTestClient,
) -> Generator:
    test_client = FullstoryTestClient(
        connection_config_fullstory=fullstory_connection_config
    )
    yield test_client


def user_updated(
    user_id: str, email: str, fullstory_test_client: FullstoryTestClient
) -> Any:
    """
    Confirm whether user is update successfully
    """
    user_response = fullstory_test_client.get_user(user_id=user_id)

    assert user_response.ok
    assert user_response.json()["displayName"] == "MASKED"
    return user_response.json()


@pytest.fixture(scope="function")
def fullstory_erasure_data(
    fullstory_secrets,
    fullstory_test_client: FullstoryTestClient,
    fullstory_erasure_identity_id,
) -> Generator:
    """
    Creates a dynamic test data record for erasure tests.
    Yields user ID as this may be useful to have in test scenarios
    """
    # Get user
    user_id = fullstory_erasure_identity_id
    user_response = fullstory_test_client.get_user(user_id)

    user = user_response.json()
    user_data = {"displayName": user["displayName"], "email": user["email"]}
    assert user_response.ok

    yield user

    # Update user to default values after test here

    user_response = fullstory_test_client.update_user(user_id, user_data)

    assert user_response.ok
