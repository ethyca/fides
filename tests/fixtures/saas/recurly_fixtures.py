from typing import Any, Dict, Generator

import pydash
import pytest
import requests
import uuid

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets
from tests.ops.test_helpers.saas_test_utils import poll_for_existence

secrets = get_secrets("recurly")


@pytest.fixture(scope="session")
def recurly_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "recurly.domain")
        or secrets["domain"],
        "username": pydash.get(saas_config, "recurly.username") or secrets["username"],
        "accept_header": pydash.get(saas_config, "recurly.accept_header") or secrets["accept_header"],        
    }


@pytest.fixture(scope="session")
def recurly_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "recurly.identity_email") or secrets["identity_email"]
    )


@pytest.fixture
def recurly_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def recurly_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def recurly_erasure_external_references() -> Dict[str, Any]:
    return {}


class RecurlyClient:
    def __init__(self, secrets: Dict[str, Any]):
        self.base_url = f"https://{secrets['domain']}"
        self.headers = (
            {
                "Accept": secrets["accept_header"],
            },
        )
        self.auth = secrets["username"], ''
        self.accept_header = secrets["accept_header"]

    def create_accounts(self, email) -> str:
        account_response = requests.post(
            url=f"{self.base_url}/accounts",
            auth=self.auth,
            headers={"Accept": self.accept_header},
            json={
                "code": uuid.uuid4().hex,
                "username": "Erasure test",
                "email": email,
                "preferred_locale": "en-US",
                "preferred_time_zone": "America/Los_Angeles"
                },
        )
        # return response.json()["id"]
        return account_response
    
    def create_billing_info(self,account_id) -> str:
        billing_response = requests.put(
            url=f"{self.base_url}/accounts/{account_id}/billing_info",
            auth=self.auth,
            headers={"Accept": self.accept_header},
            json={
                "first_name": "first bill",
                "last_name": "testing",
                "address": {
                    "phone": "string",
                    "street1": "string",
                    "street2": "string",
                    "city": "string",
                    "region": "string",
                    "postal_code": "3446",
                    "country": "IN"
                },
                "number": "4111 1111 1111 1111"
            },
        )
        # return response.json()["id"]
        return billing_response
    
    def create_shipping_address(self, account_id) -> str:
        shipping_response = requests.post(
            url=f"{self.base_url}/accounts/{account_id}/shipping_addresses",
            auth=self.auth,
            headers={"Accept": self.accept_header},
            json={
                "nickname": "string",
                "first_name": "second",
                "last_name": "test",
                "company": "test new",
                "email": "test_ethycas@gmail.com",
                "vat_number": "string",
                "phone": "string",
                "street1": "asfaad",
                "street2": "string",
                "city": "tupp",
                "region": "string",
                "postal_code": "3456",
                "country": "in"
            },
        )
        # return response.json()["id"]
        return shipping_response

    def get_accounts(self, email: str):
        act_response = requests.get(
            url=f"{self.base_url}/accounts",
            auth=self.auth,
            headers={"Accept": self.accept_header},
            params={"email": email},
        )
        if act_response.ok:
            return act_response
        
    def get_shipping_address(self, account_id: str):
        ship_address_response = requests.get(
            url=f"{self.base_url}/accounts/{account_id}/shipping_addresses",
            auth=self.auth,
            headers={"Accept": self.accept_header},
        )
        if ship_address_response.ok:
            return ship_address_response
        
    def get_billing_info(self, account_id: str):
        billing_response = requests.get(
            url=f"{self.base_url}/accounts/{account_id}/billing_info",
            auth=self.auth,
            headers={"Accept": self.accept_header},
        )
        if billing_response.ok:
            return billing_response


@pytest.fixture
def recurly_client(recurly_secrets) -> Generator:
    yield RecurlyClient(recurly_secrets)

@pytest.fixture
def recurly_erasure_data(
    recurly_client: RecurlyClient,
    recurly_erasure_identity_email: str,
) -> Generator:
    account_response = recurly_client.create_accounts(recurly_erasure_identity_email)
    # error_message = f"customer with email {recurly_erasure_identity_email} could not be created in Recharge"
    # poll_for_existence(
    #     recurly_client.get_customer,
    #     (recurly_erasure_identity_email,),
    #     error_message=error_message,
    # )
    account_id = account_response.json()["id"]

    billing_response = recurly_client.create_billing_info(account_id)
    billing_id = billing_response.json()["id"]

    shiiping_address_response = recurly_client.create_shipping_address(account_id)
    shiiping_address_id = shiiping_address_response.json()["id"]
    yield account_id


@pytest.fixture
def recurly_runner(
    db,
    cache,
    recurly_secrets,
    recurly_external_references,
    recurly_erasure_external_references,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "recurly",
        recurly_secrets,
        external_references=recurly_external_references,
        erasure_external_references=recurly_erasure_external_references,
    )