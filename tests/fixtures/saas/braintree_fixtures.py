from typing import Any, Dict, Generator

import pydash
import pytest
import requests
from faker import Faker
from requests.auth import HTTPBasicAuth
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

secrets = get_secrets("braintree")
faker = Faker()


@pytest.fixture(scope="function")
def braintree_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "braintree.domain") or secrets["domain"],
        "public_key": pydash.get(saas_config, "braintree.public_key")
        or secrets["public_key"],
        "private_key": pydash.get(saas_config, "braintree.private_key")
        or secrets["private_key"],
        "braintree_customer_id": {
            "dataset": "braintree_postgres",
            "field": "braintree_customers.braintree_customer_id",
            "direction": "from",
        },
    }


@pytest.fixture(scope="function")
def braintree_identity_email(saas_config):
    return (
        pydash.get(saas_config, "braintree.identity_email") or secrets["identity_email"]
    )


@pytest.fixture(scope="function")
def braintree_erasure_identity_id(saas_config):
    return (
        pydash.get(saas_config, "braintree.erasure_customer_id")
        or secrets["erasure_customer_id"]
    )


@pytest.fixture(scope="function")
def braintree_erasure_identity_email(saas_config):
    return (
        pydash.get(saas_config, "braintree.erasure_email") or secrets["erasure_email"]
    )


@pytest.fixture
def braintree_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/braintree_config.yml",
        "<instance_fides_key>",
        "braintree_instance",
    )


@pytest.fixture
def braintree_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/braintree_dataset.yml",
        "<instance_fides_key>",
        "braintree_instance",
    )[0]


@pytest.fixture(scope="function")
def braintree_connection_config(
    db: session, braintree_config, braintree_secrets
) -> Generator:
    fides_key = braintree_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": braintree_secrets,
            "saas_config": braintree_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def braintree_dataset_config(
    db: Session,
    braintree_connection_config: ConnectionConfig,
    braintree_dataset: Dict[str, Any],
) -> Generator:
    fides_key = braintree_dataset["fides_key"]
    braintree_connection_config.name = fides_key
    braintree_connection_config.key = fides_key
    braintree_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, braintree_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": braintree_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)


@pytest.fixture()
def braintree_postgres_dataset() -> Dict[str, Any]:
    return {
        "fides_key": "braintree_postgres",
        "name": "Braintree Postgres",
        "description": "Lookup for Braintree Customer IDs",
        "collections": [
            {
                "name": "braintree_customers",
                "fields": [
                    {
                        "name": "email",
                        "data_categories": ["user.contact.email"],
                        "fidesops_meta": {"data_type": "string", "identity": "email"},
                    },
                    {
                        "name": "braintree_customer_id",
                        "fidesops_meta": {"data_type": "string"},
                    },
                ],
            }
        ],
    }


@pytest.fixture
def braintree_postgres_dataset_config(
    connection_config: ConnectionConfig,
    braintree_postgres_dataset: Dict[str, Any],
    db: Session,
) -> Generator:
    fides_key = braintree_postgres_dataset["fides_key"]
    connection_config.name = fides_key
    connection_config.key = fides_key
    connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, braintree_postgres_dataset)

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


@pytest.fixture(scope="function")
def braintree_postgres_db(postgres_integration_session):
    postgres_integration_session = seed_postgres_data(
        postgres_integration_session,
        "./tests/fixtures/saas/external_datasets/braintree.sql",
    )
    yield postgres_integration_session
    drop_database(postgres_integration_session.bind.url)


@pytest.fixture(scope="function")
def braintree_postgres_erasure_db(
    postgres_integration_session,
    braintree_erasure_identity_email,
    braintree_erasure_identity_id,
):
    if database_exists(postgres_integration_session.bind.url):
        # Postgres cannot drop databases from within a transaction block, so
        # we should drop the DB this way instead
        drop_database(postgres_integration_session.bind.url)
    create_database(postgres_integration_session.bind.url)

    create_table_query = "CREATE TABLE public.braintree_customers (email CHARACTER VARYING(100) PRIMARY KEY,braintree_customer_id CHARACTER VARYING(100));"
    postgres_integration_session.execute(create_table_query)
    insert_query = (
        "INSERT INTO public.braintree_customers VALUES('"
        + braintree_erasure_identity_email
        + "', '"
        + braintree_erasure_identity_id
        + "')"
    )
    postgres_integration_session.execute(insert_query)

    yield postgres_integration_session
    drop_database(postgres_integration_session.bind.url)


@pytest.fixture(scope="function")
def braintree_erasure_data(
    braintree_secrets,
    braintree_erasure_identity_id,
) -> Generator:
    """
    Creates a dynamic test data record for erasure tests.
    Yields customer ID as this may be useful to have in test scenarios
    """

    # Get customer
    base_url = f"https://{braintree_secrets['domain']}"
    headers = {"Content-Type": "application/json", "Braintree-Version": "2019-01-01"}

    query = """
        query Search($criteria: CustomerSearchInput!) {
            search {
                customers(input: $criteria) {
                    edges {
                        node {
                            id
                            legacyId
                            firstName
                            lastName
                            company
                            createdAt
                        }
                    }
                }
            }
        }
    """

    variables = {"criteria": {"id": {"in": [f"{braintree_erasure_identity_id}"]}}}

    body = {"query": query, "variables": variables}
    customers_response = requests.post(
        url=f"{base_url}/graphql",
        json=body,
        headers=headers,
        auth=HTTPBasicAuth(
            f"{braintree_secrets['public_key']}", f"{braintree_secrets['private_key']}"
        ),
    )
    assert customers_response.ok

    customer = customers_response.json()["data"]["search"]["customers"]["edges"][0][
        "node"
    ]

    yield customer
    # Restoring original values

    update_customer_query = """
    mutation UpdateCustomer($input: UpdateCustomerInput!) {
        updateCustomer(input: $input) {
            customer {
                firstName
                lastName
                company
            }
        }
    }
    """

    update_customer_variables = {
        "input": {
            "customerId": "Y3VzdG9tZXJfNTEzOTc3OTIw",
            "customer": {
                "firstName": customer["firstName"],
                "lastName": customer["firstName"],
                "company": customer["company"],
            },
        }
    }

    body = {"query": update_customer_query, "variables": update_customer_variables}
    customers_update_response = requests.post(
        url=f"{base_url}/graphql",
        json=body,
        headers=headers,
        auth=HTTPBasicAuth(
            f"{braintree_secrets['public_key']}", f"{braintree_secrets['private_key']}"
        ),
    )

    assert customers_update_response.ok
