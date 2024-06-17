import random
import string
from typing import Any, Dict, Generator

import pydash
import pytest
import requests
from requests.auth import HTTPBasicAuth

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("recurly")


@pytest.fixture(scope="session")
def recurly_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "recurly.domain") or secrets["domain"],
        "api_key": pydash.get(saas_config, "recurly.api_key") or secrets["api_key"],
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
def recurly_erasure_data(
    recurly_erasure_identity_email: str,
    recurly_secrets,
) -> Generator:
    # setup for adding erasure info, a 'code' is required to add a new user
    gen_string = string.ascii_lowercase
    code = "".join(random.choice(gen_string) for i in range(10))

    base_url = f"https://{recurly_secrets['domain']}"
    auth = HTTPBasicAuth(recurly_secrets["api_key"], None)
    headers = {
        "Accept": "application/vnd.recurly.v2021-02-25",
        "Content-Type": "application/json",
    }
    accounts_url = f"{base_url}/accounts"
    body = {
        "code": code,
        "shipping_addresses": [
            {
                "first_name": "Ethycafirstname",
                "last_name": "Ethycalastname",
                "company": "Ethyca",
                "phone": "4125551212",
                "street1": "Street one",
                "street2": "Cross street two",
                "city": "Pittsburgh",
                "region": "string",
                "postal_code": "34567",
                "country": "IN",
                "nickname": "string",
                "email": "shippingemail@ethyca.com",
            }
        ],
        "username": "Ethyca username",
        "email": recurly_erasure_identity_email,
        "preferred_locale": "en-US",
        "preferred_time_zone": "America/Los_Angeles",
        "address": {
            "street1": "first cross street",
            "street2": "account address two",
            "city": "string",
            "region": "string",
            "postal_code": "3446",
            "country": "IN",
            "phone": "string",
        },
        "first_name": "Ethyca",
        "last_name": "Test",
    }

    # create a new account with shipping info
    response = requests.post(accounts_url, auth=auth, headers=headers, json=body)
    assert response.ok
    account_id = response.json()["shipping_addresses"][0]["account_id"]
    # add billing details
    body = {
        "first_name": "first bill",
        "last_name": "testing",
        "address": {
            "phone": "4125551212",
            "street1": "First steet one",
            "street2": "Second street cross",
            "city": "Pittsburgh",
            "region": "string",
            "postal_code": "3446",
            "country": "IN",
        },
        "number": "4111 1111 1111 1111",
    }
    billing_url = f"{accounts_url}/{account_id}/billing_info"
    response = requests.put(
        billing_url,
        auth=auth,
        headers=headers,
        json=body,
    )
    assert response.ok


@pytest.fixture
def recurly_runner(db, cache, recurly_secrets) -> ConnectorRunner:
    return ConnectorRunner(db, cache, "recurly", recurly_secrets)
