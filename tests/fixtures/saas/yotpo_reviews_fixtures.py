from time import sleep
from typing import Any, Dict, Generator
from uuid import uuid4

import pydash
import pytest
import requests
from faker import Faker
from requests import Response
from sqlalchemy.orm import Session
from sqlalchemy_utils.functions import create_database, database_exists, drop_database

from fides.api.ctl.sql_models import Dataset as CtlDataset
from fides.api.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.ops.models.datasetconfig import DatasetConfig
from fides.api.ops.util.saas_util import (
    load_config_with_replacement,
    load_dataset_with_replacement,
)
from fides.lib.cryptography import cryptographic_util
from tests.ops.test_helpers.db_utils import seed_postgres_data
from tests.ops.test_helpers.saas_test_utils import poll_for_existence
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("yotpo_reviews")


@pytest.fixture(scope="session")
def yotpo_reviews_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "yotpo_reviews.domain") or secrets["domain"],
        "store_id": pydash.get(saas_config, "yotpo_reviews.store_id")
        or secrets["store_id"],
        "secret_key": pydash.get(saas_config, "yotpo_reviews.secret_key")
        or secrets["secret_key"],
        "yotpo_external_id": {
            "dataset": "yotpo_reviews_postgres",
            "field": "yotpo_customer.external_id",
            "direction": "from",
        },
    }


@pytest.fixture(scope="session")
def yotpo_reviews_identity_email(saas_config):
    return (
        pydash.get(saas_config, "yotpo_reviews.identity_email")
        or secrets["identity_email"]
    )


@pytest.fixture(scope="function")
def yotpo_reviews_erasure_identity_email() -> str:
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture(scope="session")
def yotpo_reviews_erasure_yotpo_external_id() -> str:
    return f"ext-{uuid4()}"


@pytest.fixture
def yotpo_reviews_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/yotpo_reviews_config.yml",
        "<instance_fides_key>",
        "yotpo_reviews_instance",
    )


@pytest.fixture
def yotpo_reviews_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/yotpo_reviews_dataset.yml",
        "<instance_fides_key>",
        "yotpo_reviews_instance",
    )[0]


@pytest.fixture(scope="function")
def yotpo_reviews_connection_config(
    db: Session, yotpo_reviews_config, yotpo_reviews_secrets
) -> Generator:
    fides_key = yotpo_reviews_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": yotpo_reviews_secrets,
            "saas_config": yotpo_reviews_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def yotpo_reviews_dataset_config(
    db: Session,
    yotpo_reviews_connection_config: ConnectionConfig,
    yotpo_reviews_dataset: Dict[str, Any],
) -> Generator:
    fides_key = yotpo_reviews_dataset["fides_key"]
    yotpo_reviews_connection_config.name = fides_key
    yotpo_reviews_connection_config.key = fides_key
    yotpo_reviews_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, yotpo_reviews_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": yotpo_reviews_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


class YotpoReviewsTestClient:
    def __init__(self, connection_config: ConnectionConfig):
        yotpo_reviews_secrets = connection_config.secrets
        self.domain = yotpo_reviews_secrets["domain"]
        self.store_id = yotpo_reviews_secrets["store_id"]
        response = requests.post(
            url=f"https://{self.domain}/core/v3/stores/{self.store_id}/access_tokens",
            json={
                "secret": f"{yotpo_reviews_secrets['secret_key']}",
            },
        )
        assert response.ok
        self.access_token = response.json()["access_token"]

    def create_customer(self, external_id: str, email: str) -> Response:
        faker = Faker()
        return requests.patch(
            url=f"https://{self.domain}/core/v3/stores/{self.store_id}/customers",
            headers={"X-Yotpo-Token": self.access_token},
            json={
                "customer": {
                    "external_id": external_id,
                    "email": email,
                    "first_name": faker.first_name(),
                    "last_name": faker.last_name(),
                    "gender": "M",
                    "account_created_at": "2020-09-08T08:43:27Z",
                    "account_status": "enabled",
                    "default_language": "en",
                    "default_currency": "USD",
                    "accepts_sms_marketing": True,
                    "accepts_email_marketing": True,
                    "tags": "vipgold,loyal",
                    "address": {
                        "address1": faker.street_address(),
                        "address2": "",
                        "city": faker.city(),
                        "company": "null",
                        "state": faker.state(),
                        "zip": faker.zipcode(),
                        "country_code": "US",
                    },
                }
            },
        )

    def get_customer(self, external_id: str) -> Response:
        return requests.get(
            url=f"https://{self.domain}/core/v3/stores/{self.store_id}/customers",
            headers={"X-Yotpo-Token": self.access_token},
            params={"external_ids": external_id},
        )


@pytest.fixture(scope="function")
def yotpo_reviews_test_client(
    yotpo_reviews_connection_config: ConnectionConfig,
) -> Generator:
    test_client = YotpoReviewsTestClient(yotpo_reviews_connection_config)
    yield test_client


@pytest.fixture(scope="function")
def yotpo_reviews_erasure_data(
    yotpo_reviews_test_client: YotpoReviewsTestClient,
    yotpo_reviews_erasure_yotpo_external_id,
    yotpo_reviews_erasure_identity_email,
) -> None:
    # create customer
    response = yotpo_reviews_test_client.create_customer(
        yotpo_reviews_erasure_yotpo_external_id, yotpo_reviews_erasure_identity_email
    )
    assert response.ok

    # takes a while for this data to propagate, success from poll_for_existence doesn't
    # guarantee the data will be available for the actual test
    sleep(180)


@pytest.fixture()
def yotpo_reviews_postgres_dataset() -> Dict[str, Any]:
    return {
        "fides_key": "yotpo_reviews_postgres",
        "name": "Yotpo Reviews Postgres",
        "description": "Lookup for Yotpo Reviews external IDs",
        "collections": [
            {
                "name": "yotpo_customer",
                "fields": [
                    {
                        "name": "email",
                        "data_categories": ["user.contact.email"],
                        "fidesops_meta": {"data_type": "string", "identity": "email"},
                    },
                    {
                        "name": "external_id",
                        "fidesops_meta": {"data_type": "string"},
                    },
                ],
            }
        ],
    }


@pytest.fixture
def yotpo_reviews_postgres_dataset_config(
    connection_config: ConnectionConfig,
    yotpo_reviews_postgres_dataset: Dict[str, Any],
    db: Session,
) -> Generator:
    fides_key = yotpo_reviews_postgres_dataset["fides_key"]
    connection_config.name = fides_key
    connection_config.key = fides_key
    connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(
        db, yotpo_reviews_postgres_dataset
    )

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
    ctl_dataset.delete(db)


@pytest.fixture(scope="function")
def yotpo_reviews_postgres_db(postgres_integration_session):
    postgres_integration_session = seed_postgres_data(
        postgres_integration_session,
        "./tests/fixtures/saas/external_datasets/yotpo_reviews.sql",
    )
    yield postgres_integration_session
    drop_database(postgres_integration_session.bind.url)


@pytest.fixture(scope="function")
def yotpo_reviews_postgres_erasure_db(
    postgres_integration_session,
    yotpo_reviews_erasure_identity_email,
    yotpo_reviews_erasure_yotpo_external_id,
):
    if database_exists(postgres_integration_session.bind.url):
        # Postgres cannot drop databases from within a transaction block, so
        # we should drop the DB this way instead
        drop_database(postgres_integration_session.bind.url)
    create_database(postgres_integration_session.bind.url)

    create_table_query = "CREATE TABLE public.yotpo_customer (email CHARACTER VARYING(100) PRIMARY KEY, external_id CHARACTER VARYING(100));"
    postgres_integration_session.execute(create_table_query)
    insert_query = (
        "INSERT INTO public.yotpo_customer VALUES('"
        + yotpo_reviews_erasure_identity_email
        + "', '"
        + yotpo_reviews_erasure_yotpo_external_id
        + "')"
    )
    postgres_integration_session.execute(insert_query)

    yield postgres_integration_session
    drop_database(postgres_integration_session.bind.url)
