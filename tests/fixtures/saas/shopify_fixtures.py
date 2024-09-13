from time import sleep
from typing import Any, Dict, Generator

import pydash
import pytest
import requests
from faker import Faker
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

secrets = get_secrets("shopify")


@pytest.fixture(scope="function")
def shopify_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "shopify.domain") or secrets["domain"],
        "access_token": pydash.get(saas_config, "shopify.access_token")
        or secrets["access_token"],
    }


@pytest.fixture(scope="function")
def shopify_identity_email(saas_config):
    return (
        pydash.get(saas_config, "shopify.identity_email") or secrets["identity_email"]
    )


@pytest.fixture(scope="session")
def shopify_erasure_identity_email():
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture
def shopify_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/shopify_config.yml",
        "<instance_fides_key>",
        "shopify_instance",
    )


@pytest.fixture
def shopify_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/shopify_dataset.yml",
        "<instance_fides_key>",
        "shopify_instance",
    )[0]


@pytest.fixture(scope="function")
def shopify_connection_config(
    db: session, shopify_config, shopify_secrets
) -> Generator:
    fides_key = shopify_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": shopify_secrets,
            "saas_config": shopify_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def shopify_dataset_config(
    db: Session,
    shopify_connection_config: ConnectionConfig,
    shopify_dataset: Dict[str, Any],
) -> Generator:
    fides_key = shopify_dataset["fides_key"]
    shopify_connection_config.name = fides_key
    shopify_connection_config.key = fides_key
    shopify_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, shopify_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": shopify_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture(scope="function")
def shopify_erasure_data(
    shopify_connection_config, shopify_erasure_identity_email, shopify_secrets
) -> Generator:
    """
    Creates a dynamic test data record for erasure tests.
    Yields customer, order, blog, article and comment as this may be useful to have in test scenarios
    """
    base_url = f"https://{shopify_secrets['domain']}"
    faker = Faker()
    firstName = faker.first_name()
    lastName = faker.last_name()
    body = {
        "customer": {
            "first_name": firstName,
            "last_name": lastName,
            "email": shopify_erasure_identity_email,
            "verified_email": True,
            "addresses": [
                {
                    "address1": "123 Test",
                    "city": "Toronto",
                    "province": "ON",
                    "zip": "66777",
                    "last_name": lastName,
                    "first_name": firstName,
                    "country": "Canada",
                }
            ],
        }
    }
    headers = {"X-Shopify-Access-Token": f"{shopify_secrets['access_token']}"}
    customers_response = requests.post(
        url=f"{base_url}/admin/api/2022-07/customers.json", json=body, headers=headers
    )
    customer = customers_response.json()
    # not asserting that customer response is okay for running back to back requests for DSR 2.0 and DSR 3.0
    # which can cause a 422 - that the email is already taken

    sleep(30)

    error_message = f"customer with email {shopify_erasure_identity_email} could not be added to Shopify"
    poll_for_existence(
        customer_exists,
        (shopify_erasure_identity_email, shopify_secrets),
        error_message=error_message,
    )

    # Create Order
    body = {
        "order": {
            "email": shopify_erasure_identity_email,
            "fulfillment_status": "fulfilled",
            "send_receipt": True,
            "financial_status": "paid",
            "send_fulfillment_receipt": True,
            "line_items": [
                {
                    "product_id": 6923717967965,
                    "name": "Short leeve t-shirt",
                    "title": "Short sleeve t-shirt",
                    "requires_shipping": "true",
                    "price": 10,
                    "quantity": 1,
                }
            ],
            "shipping_address": {
                "first_name": "Jane",
                "last_name": "Smith",
                "address1": "123 Fake Street",
                "phone": "777-777-7777",
                "city": "Fakecity",
                "province": "Ontario",
                "country": "Canada",
                "zip": "K2P 1L4",
            },
        }
    }
    orders_response = requests.post(
        url=f"{base_url}/admin/api/2022-07/orders.json", json=body, headers=headers
    )

    assert orders_response.ok
    order = orders_response.json()
    order_id = order["order"]["id"]

    # Get Blog
    blogs_response = requests.get(
        url=f"{base_url}/admin/api/2022-07/blogs.json", headers=headers
    )
    assert blogs_response.ok
    blog = blogs_response.json()["blogs"][1]

    blog_id = blog["id"]
    # Create Article
    body = {
        "article": {
            "title": "Test Article",
            "author": firstName,
        }
    }
    articles_response = requests.post(
        url=f"{base_url}/admin/api/2022-07/blogs/{blog_id}/articles.json",
        json=body,
        headers=headers,
    )
    assert articles_response.ok
    article = articles_response.json()
    article_id = article["article"]["id"]

    # Create Comment
    body = {
        "comment": {
            "body": "I like comments\nAnd I like posting them *RESTfully*.",
            "author": firstName,
            "email": shopify_erasure_identity_email,
            "ip": faker.ipv4_private(),
            "blog_id": blog_id,
            "article_id": article_id,
        }
    }
    comments_response = requests.post(
        url=f"{base_url}/admin/api/2022-07/comments.json", json=body, headers=headers
    )
    assert comments_response.ok
    comment = comments_response.json()

    yield customer, order, blog, article, comment

    # Deleting order and article after verifying update request
    order_delete_response = requests.delete(
        url=f"{base_url}/admin/api/2022-07/orders/{order_id}.json",
        headers=headers,
    )
    assert order_delete_response.ok
    article_delete_response = requests.delete(
        url=f"{base_url}/admin/api/2022-07/articles/{article_id}.json",
        headers=headers,
    )
    assert article_delete_response.ok


def customer_exists(shopify_erasure_identity_email: str, shopify_secrets):
    """
    Confirm whether customer exists by calling customer search by email api and comparing resulting firstname str.
    Returns customer ID if it exists, returns None if it does not.
    """
    base_url = f"https://{shopify_secrets['domain']}"
    headers = {"X-Shopify-Access-Token": f"{shopify_secrets['access_token']}"}

    customer_response = requests.get(
        url=f"{base_url}/admin/api/2022-07/customers.json?email={shopify_erasure_identity_email}",
        headers=headers,
    )

    # we expect 404 if customer doesn't exist
    if 404 == customer_response.status_code:
        return None

    return customer_response.json()
