import random
from time import sleep
from typing import Any, Dict, Generator
from uuid import uuid4

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

secrets = get_secrets("square")
faker = Faker()


@pytest.fixture(scope="session")
def square_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "square.domain") or secrets["domain"],
        "access_token": pydash.get(saas_config, "square.access_token")
        or secrets["access_token"],
    }


@pytest.fixture(scope="session")
def square_identity_email(saas_config):
    return pydash.get(saas_config, "square.identity_email") or secrets["identity_email"]


@pytest.fixture(scope="session")
def square_identity_phone_number(saas_config):
    return (
        pydash.get(saas_config, "square.identity_phone_number")
        or secrets["identity_phone_number"]
    )


@pytest.fixture(scope="function")
def square_erasure_identity_email() -> str:
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture
def square_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/square_config.yml",
        "<instance_fides_key>",
        "square_instance",
    )


@pytest.fixture
def square_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/square_dataset.yml",
        "<instance_fides_key>",
        "square_instance",
    )[0]


@pytest.fixture(scope="function")
def square_connection_config(db: session, square_config, square_secrets) -> Generator:
    fides_key = square_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": square_secrets,
            "saas_config": square_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def square_dataset_config(
    db: Session,
    square_connection_config: ConnectionConfig,
    square_dataset,
    square_config,
) -> Generator:
    fides_key = square_config["fides_key"]
    square_connection_config.name = fides_key
    square_connection_config.key = fides_key
    square_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, square_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": square_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


def square_idempotency_key():
    """
    Square supports idempotency by allowing API operations to provide an idempotency key (a unique string)
    to protect against accidental duplicate calls that can have negative consequences.
    https://developer.squareup.com/docs/build-basics/common-api-patterns/idempotency
    """
    # "idempotency_key": "4a1b1a54-a1e5-4691-88ca-2548ce09ee71",
    return str(uuid4())


class SquareTestClient:
    headers: object = {}
    base_url: str = ""
    square_secrets: object = {}

    def __init__(self, square_connection_config: ConnectionConfig):
        self.square_secrets = square_connection_config.secrets

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.square_secrets['access_token']}",
        }
        self.base_url = f"https://{self.square_secrets['domain']}/v2"

    def create_customer(self, email_address: str, idempotency_key: str) -> Response:
        # create a new customer in square
        random_num = random.randint(0, 999)
        body = {
            "idempotency_key": idempotency_key,
            "email_address": email_address,
            "company_name": f"test_connector_ethyca_{random_num}",
            "nickname": f"ethyca_{random_num}",
            "address": {
                "address_line_1": faker.street_address(),
                "address_line_2": faker.street_address(),
                "postal_code": faker.postcode(),
                "locality": faker.city(),
            },
            "birthday": str(faker.date_of_birth()),
            "family_name": faker.first_name(),
            "given_name": faker.last_name(),
        }
        customer_response: Response = requests.post(
            url=f"{self.base_url}/customers", json=body, headers=self.headers
        )
        return customer_response

    def get_customer(self, email: str) -> Response:
        # get a customer
        body = {"query": {"filter": {"email_address": {"exact": f"{email}"}}}}
        customer_response: Response = requests.post(
            url=f"{self.base_url}/customers/search",
            json=body,
            headers=self.headers,
        )
        return customer_response

    def delete_customer(self, customer_id) -> Response:
        # delete customer created for erasure purposes
        url = f"{self.base_url}/customers/{customer_id}"
        customer_response: Response = requests.delete(url=url, headers=self.headers)
        return customer_response

    def get_location(self) -> Response:
        # Provides details about all the seller's locations, including those with an inactive status.

        customer_response: Response = requests.get(
            url=f"{self.base_url}/locations",
            headers=self.headers,
        )
        return customer_response

    def create_order(
        self, location_id: str, customer_id: str, idempotency_key: str
    ) -> Response:
        # creates a new order
        body = {
            "idempotency_key": idempotency_key,
            "order": {"location_id": location_id, "customer_id": customer_id},
        }
        order_response: Response = requests.post(
            url=f"{self.base_url}/orders", json=body, headers=self.headers
        )
        return order_response

    def get_order(self, location_id: str, order_id) -> Response:
        # Retrieves a set of orders by their IDs
        body = {"location_id": location_id, "order_ids": [order_id]}
        url = f"{self.base_url}/orders/batch-retrieve"
        customer_response: Response = requests.post(
            url=url,
            json=body,
            headers=self.headers,
        )
        return customer_response


@pytest.fixture(scope="function")
def square_test_client(
    square_connection_config: SquareTestClient,
) -> Generator:
    test_client = SquareTestClient(square_connection_config=square_connection_config)
    yield test_client


def _customer_exists(customer_email: str, square_test_client: SquareTestClient) -> Any:
    """check if the customer exists in the square"""
    customer_response = square_test_client.get_customer(customer_email)
    customers = customer_response.json()
    # it always return status 200 and {} if no customer otherwise {"customers": []}
    if customer_response.ok and customers:
        return customers


def _order_exists(
    location_id: str, order_id: str, square_test_client: SquareTestClient
) -> Any:
    """check if the order exists in the square"""
    order_response = square_test_client.get_order(location_id, order_id)
    orders = order_response.json()
    # it always return status 200 and {} if no order otherwise {"orders": []}
    if order_response.ok and orders:
        return order_response.json()


@pytest.fixture(scope="function")
def square_erasure_data(
    square_test_client: SquareTestClient,
    square_erasure_identity_email: str,
) -> Generator:
    """
    Creates a dynamic test data record for erasure tests.
        there are 2 steps to create data for erasure api
        1) create a new user
        2) get the seller location
    """
    # 1) create a new user
    customer_response = square_test_client.create_customer(
        square_erasure_identity_email, square_idempotency_key()
    )
    customer = customer_response.json()
    customer_id = customer["customer"]["id"]

    error_message = (
        f"customer with customer id [{customer_id}] could not be added to Square"
    )
    poll_for_existence(
        _customer_exists,
        (square_erasure_identity_email, square_test_client),
        error_message=error_message,
        interval=30,
    )
    # 2) get the seller location
    location_response = square_test_client.get_location()
    locations = location_response.json()
    # we deal with only first location
    location_id = locations["locations"][0]["id"]

    # 3) create an order for given customer on given location
    order_response = square_test_client.create_order(
        location_id, customer_id, square_idempotency_key()
    )

    order = order_response.json()["order"]
    order_id = order["id"]
    error_message = f"Order with customer id [{customer_id}] for location [{location_id}] could not be added to Square"
    sleep(5)
    poll_for_existence(
        _order_exists,
        (location_id, order_id, square_test_client),
        error_message=error_message,
    )

    yield order, customer
    # delete customer
    customer_response = square_test_client.delete_customer(customer_id)
    assert customer_response.ok

    # verify customer is deleted
    error_message = (
        f"customer with customer id {customer_id} could not be deleted from Square"
    )
    poll_for_existence(
        _customer_exists,
        (square_erasure_identity_email, square_test_client),
        error_message=error_message,
        existence_desired=False,
    )
