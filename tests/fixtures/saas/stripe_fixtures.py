from datetime import datetime
from time import sleep
from typing import Any, Dict, Generator

import pydash
import pytest
import requests
from multidimensional_urlencode import urlencode as multidimensional_urlencode
from sqlalchemy.orm import Session

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
from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
    generate_random_phone_number,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("stripe")


@pytest.fixture(scope="session")
def stripe_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "stripe.domain") or secrets["domain"],
        "api_key": pydash.get(saas_config, "stripe.api_key") or secrets["api_key"],
        "payment_types": pydash.get(saas_config, "stripe.payment_types")
        or secrets["payment_types"],
    }


@pytest.fixture
def stripe_identity_email():
    return generate_random_email()


@pytest.fixture
def stripe_identity_phone_number():
    return generate_random_phone_number()


@pytest.fixture
def stripe_erasure_identity_email():
    return generate_random_email()


@pytest.fixture
def stripe_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/stripe_config.yml", "<instance_fides_key>", "stripe_instance"
    )


@pytest.fixture
def stripe_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/stripe_dataset.yml",
        "<instance_fides_key>",
        "stripe_instance",
    )[0]


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

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, stripe_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": stripe_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


class StripeTestClient:

    def __init__(self, stripe_secrets: Dict[str, Any]):
        self.base_url = f"https://{stripe_secrets['domain']}"
        self.headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Bearer {stripe_secrets['api_key']}",
        }

    def create_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:

        response = requests.post(
            url=f"{self.base_url}/v1/customers",
            headers=self.headers,
            data=multidimensional_urlencode(customer_data),
        )
        assert response.ok
        return response.json()

    def create_dispute(self, customer_id, customer_data):
        # create dispute by adding a fraudulent card and charging it
        response = requests.post(
            url=f"{self.base_url}/v1/customers/{customer_id}",
            headers=self.headers,
            data=multidimensional_urlencode({"source": "tok_createDispute"}),
        )
        assert response.ok
        card = response.json()["sources"]["data"][0]
        card_id = card["id"]

        # update card name to have something to mask
        response = requests.post(
            url=f"{self.base_url}/v1/customers/{customer_id}/sources/{card_id}",
            headers=self.headers,
            data=multidimensional_urlencode({"name": customer_data["name"]}),
        )
        assert response.ok

        # charge
        response = requests.post(
            url=f"{self.base_url}/v1/charges",
            headers=self.headers,
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

        # charge
        response = requests.post(
            url=f"{self.base_url}/v1/charges",
            headers=self.headers,
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

        return card_id

    def create_bank_account(self, customer_id, customer_data):
        response = requests.post(
            url=f"{self.base_url}/v1/customers/{customer_id}/sources",
            headers=self.headers,
            data=multidimensional_urlencode({"source": "btok_us_verified"}),
        )
        assert response.ok
        bank_account = response.json()
        bank_account_id = bank_account["id"]
        # update bank account holder name to have something to mask
        response = requests.post(
            url=f"{self.base_url}/v1/customers/{customer_id}/sources/{bank_account_id}",
            headers=self.headers,
            data=multidimensional_urlencode(
                {"account_holder_name": customer_data["name"]}
            ),
        )
        assert response.ok

    def create_invoice(self, customer_id):
        # invoice item
        response = requests.post(
            url=f"{self.base_url}/v1/invoiceitems",
            headers=self.headers,
            params={"customer": customer_id},
            data=multidimensional_urlencode({"amount": 200, "currency": "usd"}),
        )
        assert response.ok

        # pulls in the previously created invoice item automatically to create the invoice
        response = requests.post(
            url=f"{self.base_url}/v1/invoices",
            headers=self.headers,
            params={"customer": customer_id},
        )
        assert response.ok
        invoice = response.json()
        invoice_id = invoice["id"]

        # finalize invoice
        response = requests.post(
            url=f"{self.base_url}/v1/invoices/{invoice_id}/finalize",
            headers=self.headers,
        )
        assert response.ok

        return invoice

    def create_credit_note(self, invoice):
        response = requests.post(
            url=f"{self.base_url}/v1/credit_notes",
            headers=self.headers,
            params={"invoice": invoice["id"]},
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

    def create_balance_transaction(self, customer_id):
        response = requests.post(
            url=f"{self.base_url}/v1/customers/{customer_id}/balance_transactions",
            headers=self.headers,
            data=multidimensional_urlencode({"amount": -500, "currency": "usd"}),
        )
        assert response.ok

    def create_payment_intent(self, customer_id):
        response = requests.post(
            url=f"{self.base_url}/v1/payment_intents",
            headers=self.headers,
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

        response = requests.post(
            url=f"{self.base_url}/v1/setup_intents",
            params={"customer": customer_id, "payment_method_types[]": "card"},
            headers=self.headers,
        )
        assert response.ok

    def create_payment_method(self, customer_id, customer_name):
        response = requests.post(
            url=f"{self.base_url}/v1/payment_methods",
            headers=self.headers,
            data=multidimensional_urlencode(
                {
                    "type": "card",
                    "card": {
                        "number": 4242424242424242,
                        "exp_month": 4,
                        "exp_year": datetime.today().year + 1,
                        "cvc": 314,
                    },
                    "billing_details": {"name": customer_name},
                }
            ),
        )
        assert response.ok
        payment_method = response.json()
        payment_method_id = payment_method["id"]

        response = requests.post(
            url=f"{self.base_url}/v1/payment_methods/{payment_method_id}/attach",
            params={"customer": customer_id},
            headers=self.headers,
        )
        assert response.ok

    def create_subscription(self, customer_id):
        response = requests.get(
            url=f"{self.base_url}/v1/prices",
            params={"type": "recurring"},
            headers=self.headers,
        )
        assert response.ok
        price = response.json()["data"][0]
        price_id = price["id"]

        response = requests.post(
            url=f"{self.base_url}/v1/subscriptions",
            headers=self.headers,
            data=multidimensional_urlencode(
                {"customer": customer_id, "items[0]": {"price": price_id}}
            ),
        )
        assert response.ok
        subscription = response.json()
        return subscription["id"]

    def create_tax(self, customer_id):
        # tax id
        response = requests.post(
            url=f"{self.base_url}/v1/customers/{customer_id}/tax_ids",
            headers=self.headers,
            data=multidimensional_urlencode({"type": "us_ein", "value": "000000000"}),
        )
        assert response.ok
        tax = response.json()
        return tax["id"]

    def delete_customer(self, customer_id):
        requests.delete(
            url=f"{self.base_url}/v1/customers/{customer_id}", headers=self.headers
        )

    def delete_card(self, customer_id, card_id):
        requests.get(
            url=f"{self.base_url}/v1/customers/{customer_id}/sources/{card_id}",
            headers=self.headers,
        )

    def delete_tax_id(self, customer_id, tax_id):
        requests.get(
            url=f"{self.base_url}/v1/customers/{customer_id}/tax_ids/{tax_id}",
            headers=self.headers,
        )

    def delete_subscription(self, subscription_id):
        requests.get(
            url=f"{self.base_url}/v1/subscriptions/{subscription_id}",
            headers=self.headers,
        )

    def get_customer(self, email):
        response = requests.get(
            url=f"{self.base_url}/v1/customers",
            headers=self.headers,
            params={"email": email},
        )
        customer = response.json()["data"][0]
        return customer

    def get_card(self, customer_id):
        response = requests.get(
            url=f"{self.base_url}/v1/customers/{customer_id}/sources",
            headers=self.headers,
            params={"object": "card"},
        )
        cards = response.json()["data"]
        return cards

    def get_payment_method(self, customer_id):
        response = requests.get(
            url=f"{self.base_url}/v1/customers/{customer_id}/payment_methods",
            headers=self.headers,
            params={"type": "card"},
        )
        payment_methods = response.json()["data"]
        return payment_methods

    def get_bank_account(self, customer_id):
        response = requests.get(
            url=f"{self.base_url}/v1/customers/{customer_id}/sources",
            headers=self.headers,
            params={"object": "bank_account"},
        )
        bank_account = response.json()["data"][0]
        return bank_account

    def get_tax_ids(self, customer_id):
        response = requests.get(
            url=f"{self.base_url}/v1/customers/{customer_id}/tax_ids",
            headers=self.headers,
        )
        tax_ids = response.json()["data"]
        return tax_ids

    def get_invoice_items(self, customer_id):
        response = requests.get(
            url=f"{self.base_url}/v1/invoiceitems",
            headers=self.headers,
            params={"customer": {customer_id}},
        )
        invoice_item = response.json()["data"]
        return invoice_item

    def get_subscription(self, customer_id):
        response = requests.get(
            url=f"{self.base_url}/v1/customers/{customer_id}/subscriptions",
            headers=self.headers,
        )
        subscriptions = response.json()["data"]
        return subscriptions


@pytest.fixture(scope="function")
def stripe_test_client(
    stripe_secrets,
) -> Generator:
    test_client = StripeTestClient(stripe_secrets)
    yield test_client


def stripe_generate_data(client, email, phone_number):

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
        "email": email,
        "phone": phone_number,
        "name": "Ethyca RTF",
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
        },
    }

    customer = client.create_customer(customer_data)

    customer_id = customer["id"]

    card_id = client.create_dispute(customer_id, customer_data)

    client.create_bank_account(customer_id, customer_data)

    invoice = client.create_invoice(customer_id)

    client.create_credit_note(invoice)

    client.create_balance_transaction(customer_id)

    client.create_payment_intent(customer_id)

    client.create_payment_method(customer_id, customer_data["name"])

    subscription_id = client.create_subscription(customer_id)

    tax_id = client.create_tax(customer_id)

    sleep(3)

    return {
        "customer_id": customer_id,
        "card_id": card_id,
        "subscription_id": subscription_id,
        "tax_id": tax_id,
    }


@pytest.fixture(scope="function")
def stripe_create_data(
    stripe_test_client: StripeTestClient,
    stripe_identity_email: str,
    stripe_identity_phone_number: str,
) -> Generator:
    customer = stripe_generate_data(
        stripe_test_client, stripe_identity_email, stripe_identity_phone_number
    )
    random_customer = stripe_generate_data(
        stripe_test_client, generate_random_email(), generate_random_phone_number()
    )

    yield

    for data in [customer, random_customer]:
        stripe_test_client.delete_customer(data["customer_id"])
        stripe_test_client.delete_card(data["customer_id"], data["card_id"])
        stripe_test_client.delete_subscription(data["subscription_id"])
        stripe_test_client.delete_tax_id(data["customer_id"], data["tax_id"])


@pytest.fixture
def stripe_runner(
    db,
    cache,
    stripe_secrets,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "stripe",
        stripe_secrets,
    )
