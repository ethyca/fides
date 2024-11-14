from time import sleep
from typing import  Dict, Generator

import pydash
import pytest
import requests
from faker import Faker
from loguru import logger

from fides.api.cryptography import cryptographic_util
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.sql_models import Dataset as CtlDataset
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner
from tests.ops.test_helpers.saas_test_utils import poll_for_existence
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("shopify")
faker = Faker()


@pytest.fixture(scope="function")
def shopify_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "shopify.domain") or secrets["domain"],
        "access_token": pydash.get(saas_config, "shopify.access_token")
        or secrets["access_token"],
        'fixtures_access_token' : pydash.get(saas_config, "shopify.fixtures_access_token")
        or secrets["fixtures_access_token"],
    }


@pytest.fixture(scope="function")
def shopify_identity_email():
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


# TODO: Pass fixture creation to GraphQL API
# We are gonna still use REST API for ease of development on data creation
@pytest.fixture(scope="function")
def shopify_access_data(shopify_identity_email, shopify_secrets) -> Generator:
    """
    Creates a dynamic test data record for access tests.
    Yields the list of orders and comments created for validation
    """

    base_url = f"https://{shopify_secrets['domain']}"
    headers = {"X-Shopify-Access-Token": f"{shopify_secrets['fixtures_access_token']}"}

    # Create Customer
    customer = create_customer(shopify_identity_email, base_url, headers)

    # Confirm customer exists
    error_message = (
        f"customer with email {shopify_identity_email} could not be added to Shopify"
    )
    poll_for_existence(
        customer_exists,
        (shopify_identity_email, shopify_secrets),
        error_message=error_message,
    )

    ## Note: We are hitting the API rate limit with 10 items per page.
    ## So we have to manually reduce the pagination of orders on the request override to test pagination

    orders = []
    orders_pagination_number = 2

    for i in range(orders_pagination_number + 1):
        order = create_order(shopify_identity_email, base_url, headers)
        orders.append(order)
        logger.info("sleeping 5 seconds to avoid rate limit")
        sleep(5)

    # Get Blog
    blogs_response = requests.get(
        url=f"{base_url}/admin/api/2022-07/blogs.json", headers=headers
    )
    assert blogs_response.ok
    blog = blogs_response.json()["blogs"][1]
    blog_id = blog["id"]

    # Create Article
    article = create_article(blog_id, base_url, headers)
    article_id = article["article"]["id"]

    ## Note: We are hitting the API rate limit with 100 items per page.
    ## So we have to manually reduce the pagination of orders on the request override to test pagination
    comments = []
    comments_pagination_number = 10
    for i in range(comments_pagination_number + 1):
        comment = create_comment(
            blog_id, article_id, shopify_identity_email, base_url, headers
        )
        comments.append(comment)

    ## We are only using order numbers on the test, so we are only yielding orders
    yield {"orders": orders, "comments": comments}

    # Deleting order and article after verifying  request
    for order in orders:
        order_id = order["order"]["id"]
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


@pytest.fixture(scope="session")
def shopify_erasure_identity_email():
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


# TODO: Pass fixture creation to GraphQL API
# We are gonna still use REST API for ease of development on data creation
@pytest.fixture(scope="function")
def shopify_erasure_data(shopify_erasure_identity_email, shopify_secrets) -> Generator:
    """
    Creates a dynamic base  test data record for erasure tests.
    Yields customer, order, blog, article and comment as this may be useful to have in test scenarios
    """
    base_url = f"https://{shopify_secrets['domain']}"
    headers = {"X-Shopify-Access-Token": f"{shopify_secrets['fixtures_access_token']}"}

    # Create Customer
    customer = create_customer(shopify_erasure_identity_email, base_url, headers)
    # Confirm customer exists
    error_message = f"customer with email {shopify_erasure_identity_email} could not be added to Shopify"
    poll_for_existence(
        customer_exists,
        (shopify_erasure_identity_email, shopify_secrets),
        error_message=error_message,
    )

    # Create Order
    order = create_order(shopify_erasure_identity_email, base_url, headers)
    order_id = order["order"]["id"]
    # Get Blog
    blogs_response = requests.get(
        url=f"{base_url}/admin/api/2022-07/blogs.json", headers=headers
    )
    assert blogs_response.ok
    blog = blogs_response.json()["blogs"][1]
    blog_id = blog["id"]

    # Create Article
    article = create_article(blog_id, base_url, headers)
    article_id = article["article"]["id"]

    # Create Comment
    comment = create_comment(
        blog_id, article_id, shopify_erasure_identity_email, base_url, headers
    )

    yield customer, order, blog, article, comment

    # Deleting order and article after verifying  request
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


def create_customer(identity_email: str, base_url: str, headers: Dict[str, str]):
    firstName = faker.first_name()
    lastName = faker.last_name()
    body = {
        "customer": {
            "first_name": firstName,
            "last_name": lastName,
            "email": identity_email,
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
    customers_response = requests.post(
        url=f"{base_url}/admin/api/2022-07/customers.json", json=body, headers=headers
    )
    logger.info(customers_response.json())
    logger.info(f"Customer Response status: {customers_response.status_code}")
    if customers_response.status_code == 422:
        return customers_response.json()

    assert customers_response.ok
    ##sleep to give Shopify time to confirm existance
    sleep(10)
    return customers_response.json()


def customer_exists(shopify_identity_email: str, shopify_secrets):
    """
    Confirm whether customer exists by calling customer search by email api and comparing resulting firstname str.
    Returns customer ID if it exists, returns None if it does not.
    """
    base_url = f"https://{shopify_secrets['domain']}"
    headers = {"X-Shopify-Access-Token": f"{shopify_secrets['fixtures_access_token']}"}

    customer_response = requests.get(
        url=f"{base_url}/admin/api/2022-07/customers.json?email={shopify_identity_email}",
        headers=headers,
    )

    # we expect 404 if customer doesn't exist
    if 404 == customer_response.status_code:
        return None

    return customer_response.json()


def create_order(identity_email: str, base_url: str, headers: Dict[str, str]):
    body = {
        "order": {
            "email": identity_email,
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
    logger.info(f"Orders Response {orders_response.json()}")
    assert orders_response.ok

    return orders_response.json()


def create_article(blog_id: int, base_url: str, headers: Dict[str, str]):
    firstName = faker.first_name()
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
    return articles_response.json()


def create_comment(
    blog_id: int,
    article_id: int,
    identity_email: str,
    base_url: str,
    headers: Dict[str, str],
):
    firstName = faker.first_name()
    ip = faker.ipv4_private()
    body = {
        "comment": {
            "body": "I like comments\nAnd I like posting them *RESTfully*.",
            "author": firstName,
            "email": identity_email,
            "ip": ip,
            "blog_id": blog_id,
            "article_id": article_id,
        }
    }
    comments_response = requests.post(
        url=f"{base_url}/admin/api/2022-07/comments.json", json=body, headers=headers
    )
    assert comments_response.ok
    return comments_response.json()


@pytest.fixture
def shopify_runner(
    db,
    cache,
    shopify_secrets,
) -> ConnectorRunner:
    return ConnectorRunner(db, cache, "shopify", shopify_secrets)
