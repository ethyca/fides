from typing import Any, Dict, Generator

import pydash
import pytest
import requests
from faker import Faker
from sqlalchemy.orm import Session
from sqlalchemy_utils.functions import create_database, database_exists, drop_database

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
from tests.ops.test_helpers.db_utils import seed_postgres_data
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("friendbuy")
faker = Faker()


@pytest.fixture(scope="function")
def friendbuy_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "friendbuy.domain") or secrets["domain"],
        "token": pydash.get(saas_config, "friendbuy.token") or secrets["token"],
        "friendbuy_user_id": {
            "dataset": "friendbuy_postgres",
            "field": "friendbuy_users.friendbuy_user_id",
            "direction": "from",
        },
    }


@pytest.fixture(scope="function")
def friendbuy_identity_email(saas_config):
    return (
        pydash.get(saas_config, "friendbuy.identity_email") or secrets["identity_email"]
    )


@pytest.fixture(scope="function")
def friendbuy_erasure_identity_id(friendbuy_erasure_data):
    return f"{friendbuy_erasure_data['customer']['id']}"


@pytest.fixture(scope="session")
def friendbuy_erasure_identity_email():
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture
def friendbuy_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/friendbuy_config.yml",
        "<instance_fides_key>",
        "friendbuy_instance",
    )


@pytest.fixture
def friendbuy_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/friendbuy_dataset.yml",
        "<instance_fides_key>",
        "friendbuy_instance",
    )[0]


@pytest.fixture(scope="function")
def friendbuy_connection_config(
    db: session, friendbuy_config, friendbuy_secrets
) -> Generator:
    fides_key = friendbuy_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": friendbuy_secrets,
            "saas_config": friendbuy_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def friendbuy_dataset_config(
    db: Session,
    friendbuy_connection_config: ConnectionConfig,
    friendbuy_dataset: Dict[str, Any],
) -> Generator:
    fides_key = friendbuy_dataset["fides_key"]
    friendbuy_connection_config.name = fides_key
    friendbuy_connection_config.key = fides_key
    friendbuy_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, friendbuy_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": friendbuy_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture()
def friendbuy_postgres_dataset() -> Dict[str, Any]:
    return {
        "fides_key": "friendbuy_postgres",
        "name": "Friendbuy Postgres",
        "description": "Lookup for Friendbuy User IDs",
        "collections": [
            {
                "name": "friendbuy_users",
                "fields": [
                    {
                        "name": "email",
                        "data_categories": ["user.contact.email"],
                        "fidesops_meta": {"data_type": "string", "identity": "email"},
                    },
                    {
                        "name": "friendbuy_user_id",
                        "fidesops_meta": {"data_type": "string"},
                    },
                ],
            }
        ],
    }


@pytest.fixture
def friendbuy_postgres_dataset_config(
    connection_config: ConnectionConfig,
    friendbuy_postgres_dataset: Dict[str, Any],
    db: Session,
) -> Generator:
    fides_key = friendbuy_postgres_dataset["fides_key"]
    connection_config.name = fides_key
    connection_config.key = fides_key
    connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, friendbuy_postgres_dataset)

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
def friendbuy_postgres_db(postgres_integration_session):
    postgres_integration_session = seed_postgres_data(
        postgres_integration_session,
        "./tests/fixtures/saas/external_datasets/friendbuy.sql",
    )
    yield postgres_integration_session
    drop_database(postgres_integration_session.bind.url)


@pytest.fixture(scope="function")
def friendbuy_postgres_erasure_db(
    postgres_integration_session,
    friendbuy_erasure_identity_email,
    friendbuy_erasure_identity_id,
):
    if database_exists(postgres_integration_session.bind.url):
        # Postgres cannot drop databases from within a transaction block, so
        # we should drop the DB this way instead
        drop_database(postgres_integration_session.bind.url)
    create_database(postgres_integration_session.bind.url)

    create_table_query = "CREATE TABLE public.friendbuy_users (email CHARACTER VARYING(100) PRIMARY KEY,friendbuy_user_id CHARACTER VARYING(100));"
    postgres_integration_session.execute(create_table_query)
    insert_query = (
        "INSERT INTO public.friendbuy_users VALUES('"
        + friendbuy_erasure_identity_email
        + "', '"
        + friendbuy_erasure_identity_id
        + "')"
    )
    postgres_integration_session.execute(insert_query)

    yield postgres_integration_session
    drop_database(postgres_integration_session.bind.url)


@pytest.fixture(scope="function")
def friendbuy_erasure_data(
    friendbuy_secrets,
    friendbuy_erasure_identity_email,
) -> Generator:
    """
    Creates a dynamic test data record for erasure tests.
    Yields customer ID as this may be useful to have in test scenarios
    """

    base_url = f"https://{friendbuy_secrets['domain']}"
    header = {"Authorization": "Bearer " + friendbuy_secrets["token"]}
    # Create customer
    customer_body = {
        "account_id": "1",
        "email_address": f"{friendbuy_erasure_identity_email}",
        "first_name": f"{faker.name()}",
        "last_name": f"{faker.name()}",
    }

    customers_response = requests.post(
        url=f"{base_url}/v2/customers", json=customer_body, headers=header
    )
    assert customers_response.ok
    customer = customers_response.json()
    yield customer
