import uuid
from typing import Any, Dict, Generator

import pydash
import pytest
import requests
from faker import Faker
from requests import Response
from sqlalchemy.orm import Session

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

secrets = get_secrets("recharge")


@pytest.fixture(scope="function")
def recharge_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "recharge.domain") or secrets["domain"],
        "api_key": pydash.get(saas_config, "recharge.api_key") or secrets["api_key"],
    }


@pytest.fixture(scope="function")
def recharge_identity_email(saas_config):
    return (
        pydash.get(saas_config, "recharge.identity_email") or secrets["identity_email"]
    )


@pytest.fixture(scope="function")
def recharge_erasure_identity_email():
    return f"{uuid.uuid4().hex}@email.com"


@pytest.fixture
def recharge_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/recharge_config.yml",
        "<instance_fides_key>",
        "recharge_instance",
    )


@pytest.fixture
def recharge_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/recharge_dataset.yml",
        "<instance_fides_key>",
        "recharge_instance",
    )[0]


@pytest.fixture(scope="function")
def recharge_connection_config(
    db: session, recharge_config, recharge_secrets
) -> Generator:
    fides_key = recharge_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": recharge_secrets,
            "saas_config": recharge_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def recharge_dataset_config(
    db: Session,
    recharge_connection_config: ConnectionConfig,
    recharge_dataset: Dict[str, Any],
) -> Generator:
    fides_key = recharge_dataset["fides_key"]
    recharge_connection_config.name = fides_key
    recharge_connection_config.key = fides_key
    recharge_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, recharge_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": recharge_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db)


class RechargeTestClient:
    """Helper to call various Recharge data management requests"""

    def __init__(self, recharge_connection_config: ConnectionConfig):
        self.recharge_secrets = recharge_connection_config.secrets
        self.headers = {
            "X-Recharge-Access-Token": self.recharge_secrets["api_key"],
            "Content-Type": "application/json",
        }
        self.base_url = f"https://{self.recharge_secrets['domain']}"
        self.faker = Faker()
        self.first_name = self.faker.first_name()
        self.last_name = self.faker.last_name()
        self.street_address = self.faker.street_address()

    # 1: Creates, checks for existance and deletes customer
    def create_customer(self, email) -> Response:
        customer_body = {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": email,
            "billing_address1": self.street_address,
            "billing_city": "New York City",
            "billing_province": "New York",
            "billing_country": "United States",
            "billing_first_name": self.first_name,
            "billing_last_name": self.last_name,
            "billing_zip": "10001",
        }

        customer_response: Response = requests.post(
            url=f"{self.base_url}/customers",
            json=customer_body,
            headers=self.headers,
        )
        assert customer_response.ok

        return customer_response

    def get_customer(self, email):
        customer_response: Response = requests.get(
            url=f"{self.base_url}/customers",
            params={"email": email},
            headers=self.headers,
        )
        assert customer_response.ok
        return customer_response.json()

    def delete_customer(self, customer_id):
        customer_response: Response = requests.delete(
            url=f"{self.base_url}/customers/{customer_id}", headers=self.headers
        )
        assert customer_response.ok

    # 2: Creates, checks for existance and deletes address
    def create_address(self, customer_id) -> Response:
        address_body = {
            "customer_id": customer_id,
            "address1": self.street_address,
            "address2": self.street_address,
            "city": "Los Angeles",
            "company": "Recharge",
            "country_code": "US",
            "country": "United States",
            "first_name": self.first_name,
            "last_name": self.last_name,
            "order_attributes": [{"name": "custom name", "value": "custom value"}],
            "phone": "5551234567",
            "province": "California",
            "zip": "90001",
        }
        address_response = requests.post(
            url=f"{self.base_url}/addresses",
            headers=self.headers,
            json=address_body,
        )
        assert address_response.ok
        return address_response

    def get_addresses(self, customer_id):
        address_response: Response = requests.get(
            url=f"{self.base_url}/addresses",
            params={"customer_id": customer_id},
            headers=self.headers,
        )
        assert address_response.ok
        return address_response.json()

    def delete_address(self, address_id):
        address_response: Response = requests.delete(
            url=f"{self.base_url}/addresses/{address_id}", headers=self.headers
        )
        assert address_response.ok


@pytest.fixture(scope="function")
def recharge_test_client(recharge_connection_config: RechargeTestClient) -> Generator:
    test_client = RechargeTestClient(
        recharge_connection_config=recharge_connection_config
    )
    yield test_client


@pytest.fixture(scope="function")
def recharge_erasure_data(
    recharge_test_client: RechargeTestClient, recharge_erasure_identity_email: str
) -> Generator:
    customer_response = recharge_test_client.create_customer(
        recharge_erasure_identity_email
    )
    error_message = f"customer with email {recharge_erasure_identity_email} could not be created in Recharge"
    poll_for_existence(
        recharge_test_client.get_customer,
        (recharge_erasure_identity_email,),
        error_message=error_message,
    )
    customer_id = customer_response.json()["customer"]["id"]

    address_response = recharge_test_client.create_address(customer_id)
    error_message = f"address for customer '{recharge_erasure_identity_email}' could not be created in Recharge"
    poll_for_existence(
        recharge_test_client.get_addresses,
        args=(customer_id,),
        error_message=error_message,
    )
    address_id = address_response.json()["address"]["id"]

    yield customer_response, address_response

    recharge_test_client.delete_address(address_id)
    recharge_test_client.delete_customer(customer_id)
