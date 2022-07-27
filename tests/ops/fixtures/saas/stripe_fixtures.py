from typing import Any, Dict, Generator

import pydash
import pytest
import requests
from fideslib.core.config import load_toml
from fideslib.db import session
from multidimensional_urlencode import urlencode as multidimensional_urlencode
from sqlalchemy.orm import Session

from fidesops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fidesops.models.datasetconfig import DatasetConfig
from fidesops.util.saas_util import load_config
from tests.ops.fixtures.application_fixtures import load_dataset
from tests.ops.test_helpers.vault_client import get_secrets

saas_config = load_toml(["saas_config.toml"])
secrets = get_secrets("stripe")


@pytest.fixture(scope="session")
def stripe_secrets():
    return {
        "domain": pydash.get(saas_config, "stripe.domain") or secrets["domain"],
        "api_key": pydash.get(saas_config, "stripe.api_key") or secrets["api_key"],
        "payment_types": pydash.get(saas_config, "stripe.payment_types")
        or secrets["payment_types"],
        "page_size": pydash.get(saas_config, "stripe.page_size")
        or secrets["page_size"],
    }


@pytest.fixture(scope="session")
def stripe_identity_email():
    return pydash.get(saas_config, "stripe.identity_email") or secrets["identity_email"]


@pytest.fixture(scope="function")
def stripe_erasure_identity_email():
    return "ethyca+stripe+rtf@example.com"


@pytest.fixture
def stripe_config() -> Dict[str, Any]:
    return load_config("data/saas/config/stripe_config.yml")


@pytest.fixture
def stripe_dataset() -> Dict[str, Any]:
    return load_dataset("data/saas/dataset/stripe_dataset.yml")[0]


@pytest.fixture(scope="function")
def stripe_connection_config(
    db: Session, stripe_config: Dict[str, Dict], stripe_secrets: Dict[str, Any]
) -> Generator:
    fides_key = stripe_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": stripe_secrets,
            "saas_config": stripe_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def stripe_dataset_config(
    db: session,
    stripe_connection_config: ConnectionConfig,
    stripe_dataset: Dict[str, Dict],
) -> Generator:
    fides_key = stripe_dataset["fides_key"]
    stripe_connection_config.name = fides_key
    stripe_connection_config.key = fides_key
    stripe_connection_config.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": stripe_connection_config.id,
            "fides_key": fides_key,
            "dataset": stripe_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)


@pytest.fixture(scope="function")
def stripe_create_erasure_data(stripe_connection_config: ConnectionConfig) -> Generator:

    stripe_secrets = stripe_connection_config.secrets

    base_url = f"https://{stripe_secrets['domain']}"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Bearer {stripe_secrets['api_key']}",
    }

    # customer
    customer_data = {
        "address": {
            "city": "Anaheim",
            "country": "US",
            "line1": "123 Fake St",
            "line2": "Apt 1",
            "postal_code": "92882",
            "state": "CA",
        },
        "balance": 0,
        "description": "RTF Test Customer",
        "email": "ethyca+stripe+rtf@example.com",
        "name": "Ethyca RTF",
        "phone": "+19515551234",
        "preferred_locales": ["en-US"],
        "shipping": {
            "address": {
                "city": "Anaheim",
                "country": "US",
                "line1": "123 Fake St",
                "line2": "Apt 1",
                "postal_code": "92882",
                "state": "CA",
            },
            "name": "Ethyca RTF",
            "phone": "+19515551234",
        },
    }

    response = requests.post(
        url=f"{base_url}/v1/customers",
        headers=headers,
        data=multidimensional_urlencode(customer_data),
    )
    assert response.ok
    customer = response.json()
    customer_id = customer["id"]

    # create dispute by adding a fraudulent card and charging it
    response = requests.post(
        url=f"{base_url}/v1/customers/{customer['id']}",
        headers=headers,
        data=multidimensional_urlencode({"source": "tok_createDispute"}),
    )
    assert response.ok
    card = response.json()["sources"]["data"][0]
    card_id = card["id"]

    # update card name to have something to mask
    response = requests.post(
        url=f"{base_url}/v1/customers/{customer_id}/sources/{card_id}",
        headers=headers,
        data=multidimensional_urlencode({"name": customer_data["name"]}),
    )
    assert response.ok

    # charge
    response = requests.post(
        url=f"{base_url}/v1/charges",
        headers=headers,
        data=multidimensional_urlencode(
            {
                "customer": customer_id,
                "source": card_id,
                "amount": 1000,
                "currency": "usd",
            }
        ),
    )
    assert response.ok

    # bank account
    response = requests.post(
        url=f"{base_url}/v1/customers/{customer_id}/sources",
        headers=headers,
        data=multidimensional_urlencode({"source": "btok_us_verified"}),
    )
    assert response.ok
    bank_account = response.json()
    bank_account_id = bank_account["id"]
    # update bank account holder name to have something to mask
    response = requests.post(
        url=f"{base_url}/v1/customers/{customer_id}/sources/{bank_account_id}",
        headers=headers,
        data=multidimensional_urlencode({"account_holder_name": customer_data["name"]}),
    )
    assert response.ok

    # invoice item
    response = requests.post(
        url=f"{base_url}/v1/invoiceitems",
        headers=headers,
        params={"customer": customer_id},
        data=multidimensional_urlencode({"amount": 200, "currency": "usd"}),
    )
    assert response.ok

    # pulls in the previously created invoice item automatically to create the invoice
    response = requests.post(
        url=f"{base_url}/v1/invoices",
        headers=headers,
        params={"customer": customer_id},
    )
    assert response.ok
    invoice = response.json()
    invoice_id = invoice["id"]

    # finalize invoice
    response = requests.post(
        url=f"{base_url}/v1/invoices/{invoice_id}/finalize", headers=headers
    )
    assert response.ok

    # credit note
    response = requests.post(
        url=f"{base_url}/v1/credit_notes",
        headers=headers,
        params={"invoice": invoice_id},
        data=multidimensional_urlencode(
            {
                "lines[0]": {
                    "type": "invoice_line_item",
                    "invoice_line_item": invoice["lines"]["data"][0]["id"],
                    "quantity": 1,
                }
            }
        ),
    )
    assert response.ok

    # customer balance transaction
    response = requests.post(
        url=f"{base_url}/v1/customers/{customer_id}/balance_transactions",
        headers=headers,
        data=multidimensional_urlencode({"amount": -500, "currency": "usd"}),
    )
    assert response.ok

    # payment intent
    response = requests.post(
        url=f"{base_url}/v1/payment_intents",
        headers=headers,
        data=multidimensional_urlencode(
            {
                "customer": customer_id,
                "amount": 2000,
                "currency": "usd",
                "payment_method_types[]": "card",
                "confirm": True,
            }
        ),
    )
    assert response.ok

    # create and attach payment method to customer
    response = requests.post(
        url=f"{base_url}/v1/payment_methods",
        headers=headers,
        data=multidimensional_urlencode(
            {
                "type": "card",
                "card": {
                    "number": 4242424242424242,
                    "exp_month": 4,
                    "exp_year": 2023,
                    "cvc": 314,
                },
                "billing_details": {"name": customer_data["name"]},
            }
        ),
    )
    assert response.ok
    payment_method = response.json()
    payment_method_id = payment_method["id"]

    response = requests.post(
        url=f"{base_url}/v1/payment_methods/{payment_method_id}/attach",
        params={"customer": customer_id},
        headers=headers,
    )
    assert response.ok

    # setup intent
    response = requests.post(
        url=f"{base_url}/v1/setup_intents",
        params={"customer": customer_id, "payment_method_types[]": "card"},
        headers=headers,
    )
    assert response.ok

    # get an existing price and use it to create a subscription
    response = requests.get(
        url=f"{base_url}/v1/prices",
        params={"type": "recurring"},
        headers=headers,
    )
    assert response.ok
    price = response.json()["data"][0]
    price_id = price["id"]

    response = requests.post(
        url=f"{base_url}/v1/subscriptions",
        headers=headers,
        data=multidimensional_urlencode(
            {"customer": customer_id, "items[0]": {"price": price_id}}
        ),
    )
    assert response.ok

    # tax id
    response = requests.post(
        url=f"{base_url}/v1/customers/{customer_id}/tax_ids",
        headers=headers,
        data=multidimensional_urlencode({"type": "us_ein", "value": "000000000"}),
    )
    assert response.ok

    yield customer

    response = requests.delete(
        url=f"{base_url}/v1/customers/{customer_id}", headers=headers
    )
    assert response.ok
