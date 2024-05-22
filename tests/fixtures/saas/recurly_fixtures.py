import base64
import json
import random
import string
import time
from typing import Any, Dict, Generator

import pydash
import pytest
import requests

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
        "username": pydash.get(saas_config, "recurly.username") or secrets["username"],
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
    # setup
    api_key = recurly_secrets['username']
    api_key_string = api_key
    api_key_bytes = api_key_string.encode("ascii")
    base64_bytes = base64.b64encode(api_key_bytes)
    auth_username = base64_bytes.decode("ascii")
    # print(auth_username) # for debugging
    gen_string = string.ascii_lowercase
    code = ''.join(random.choice(gen_string) for i in range(10))

    base_url = f"https://{recurly_secrets['domain']}"
    headers = {
        "Accept": "application/vnd.recurly.v2021-02-25",
        "Authorization": "Basic " + auth_username,
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
    response = requests.post(accounts_url, headers=headers, json=body)
    assert response.ok
    # import pdb; pdb.set_trace()
    # part of the response to the request to create a new account is the account_id
    time.sleep(1)
    account_id = response.json()["shipping_addresses"][0]["account_id"]
    shipping_id = response.json()["shipping_addresses"][0]["id"]
    # now we can form up a request to add billing details
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
            "country": "IN"
        },
        "number": "4111 1111 1111 1111"
    }
    billing_url = f"{accounts_url}/{account_id}/billing_info"
    response = requests.put(billing_url, headers=headers, json=body)
    assert response.ok

@pytest.fixture
def recurly_runner(db, cache, recurly_secrets) -> ConnectorRunner:
    return ConnectorRunner(db, cache, "recurly", recurly_secrets)
