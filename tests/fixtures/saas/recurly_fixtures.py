from typing import Any, Dict, Generator

import pydash
import pytest
import requests
import base64
import string
import random
import json

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
    accounts_url = base_url + "/accounts"
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
                "email": "shippingemail@ethyca.com"
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
                "phone": "string"
        }
    }

    # create a new account with shipping info
    response = requests.post(accounts_url, headers=headers, json=body)
    assert response.ok
    # part of the response to the request to create a new account is the account_id
    account_id = response.json()["shipping_addresses"][0]["account_id"]
    shipping_id = response.json()["shipping_addresses"][0]["id"]
    accounts = response.json()['username']
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
    # if we get this far we've got our new account with billing and shipping info
    billing_info = response.json()['first_name']
    # I'll need 3 here, one for account, shipping addresses and billing info

    check_url = f"{accounts_url}/{account_id}"
    response = requests.get(check_url, headers=headers)
    assert response.ok


    # check that the newly created account responds

    ### set up done, we now have a valid account, that has shipping and billing details that we can mask

    body = {
        "first_name": "MASKED",
        "last_name": "MASKED",
        "username": "MASKED",
        "email": "MASKED@Ethyca.com",
        "address": {
            "street1": "MASKED",
            "street2": "MASKED",
            "city": "MASKED",
            "region": "MASKED",
            "postal_code": "3446",
            "country": "IN",
            "phone": "MASKED",
        },
    }
    mask_account_url = f"{accounts_url}/{account_id}"
    response = requests.put(mask_account_url, headers=headers, json=body)
    assert response.ok

    assert response.json()['first_name'] == 'MASKED', "Expected 'MASKED' for first_name, got {}".format(response.json()['first_name'])
    assert response.json()['last_name'] == 'MASKED', "Expected 'MASKED' for last_name, got {}".format(response.json()['last_name'])
    assert response.json()['email'] == 'MASKED@Ethyca.com', "Expected 'MASKED@Ethyca.com' for email, got {}".format(response.json()['email'])
    assert response.json()['address']['street1'] == 'MASKED', "Expected 'MASKED' for street1, got {}".format(response.json()['address']['street1'])
    assert response.json()['address']['street2'] == 'MASKED', "Expected 'MASKED' for street2, got {}".format(response.json()['address']['street2'])
    assert response.json()['address']['city'] == 'MASKED', "Expected 'MASKED' for city, got {}".format(response.json()['address']['city'])
    assert response.json()['address']['region'] == 'MASKED', "Expected 'MASKED' for region, got {}".format()(response.json()['address']['region'])
    assert response.json()['address']['phone'] == 'MASKED', "Expected 'MASKED' for phone, got {}".format()(response.json()['address']['phone'])
    ## repeat for shipping and billing
    # billing
    body = {
        "first_name": "MASKED",
        "last_name":"MASKED",
        "number": "4111111111111111",
        "address": {
            "street1": "MASKED",
            "street2": "MASKED",
            "city": "MASKED",
            "region": "string",
            "postal_code": "3446",
            "country": "IN",
            "phone": "MASKED",
        }
    }
    mask_billing_url = f"{accounts_url}/{account_id}/billing_info"
    response = requests.put(mask_billing_url, headers=headers, json=body)
    assert response.ok

    assert response.json()['first_name'] == 'MASKED', "Expected 'MASKED' for first_name, got {}".format(response.json()['first_name'])
    assert response.json()['last_name'] == 'MASKED', "Expected 'MASKED' for last_name, got {}".format(response.json()['last_name'])
    assert response.json()['payment_method']['first_six'] == '411111', "Expected '411111' for first_six, got {}".format(response.json()['first_six'])
    assert response.json()['payment_method']['last_four'] == '1111', "Expected '1111' for last_four, got {}".format(response.json()['last_four'])
    assert response.json()['address']['phone'] == 'MASKED', "Expected 'MASKED' for phone, got {}".format(response.json()['address']['phone'])
    assert response.json()['address']['street1'] == 'MASKED', "Expected 'MASKED' for street1, got {}".format(response.json()['address']['street1'])
    assert response.json()['address']['street2'] == 'MASKED', "Expected 'MASKED' for street2, got {}".format(response.json()['address']['street2'])
    assert response.json()['address']['city'] == 'MASKED', "Expected 'MASKED' for city, got {}".format(response.json()['address']['city'])
## good to here

    # shipping
    body = {
        "first_name": "MASKED",
        "last_name": "MASKED",
        "email": "MASKED@Ethyca.com",
        "phone": "MASKED",
        "street1": "MASKED",
        "street2": "MASKED",
    }
    mask_shipping_url = f"{accounts_url}/{account_id}/shipping_addresses/{shipping_id}"
    response = requests.put(mask_shipping_url, headers=headers, json=body)
    shipping_address = response.json()['first_name']
    # verification that the values we expected to be masked were masked.
    assert response.json()['first_name'] == 'MASKED', "Expected 'MASKED' for first_name, got {}".format(response.json()['first_name'])
    assert response.json()['last_name'] == 'MASKED', "Expected 'MASKED' for last_name, got {}".format(response.json()['last_name'])
    assert response.json()['phone'] == 'MASKED', "Expected 'MASKED' for phone, got {}".format(response.json()['phone'])
    assert response.json()['street1'] == 'MASKED', "Expected 'MASKED' for street1, got {}".format(response.json()['street1'])
    assert response.json()['street2'] == 'MASKED', "Expected 'MASKED' for street2, got {}".format(response.json()['street2'])
    assert response.json()['email'] == 'MASKED@Ethyca.com', "Expected 'MASKED' for email, got {}".format(response.json()['email'])


    # import pdb; pdb.set_trace()

    yield accounts

@pytest.fixture
def recurly_runner(db, cache, recurly_secrets) -> ConnectorRunner:
    return ConnectorRunner(db, cache, "recurly", recurly_secrets)
