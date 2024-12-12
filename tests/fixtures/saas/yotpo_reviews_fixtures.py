from typing import Any, Dict, Generator

import pydash
import pytest
import requests
from faker import Faker
from requests import Response

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.saas_test_utils import poll_for_existence
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("yotpo_reviews")


@pytest.fixture(scope="session")
def yotpo_reviews_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "yotpo_reviews.domain") or secrets["domain"],
        "store_id": pydash.get(saas_config, "yotpo_reviews.store_id")
        or secrets["store_id"],
        "secret_key": pydash.get(saas_config, "yotpo_reviews.secret_key")
        or secrets["secret_key"],
    }


@pytest.fixture(scope="session")
def yotpo_reviews_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "yotpo_reviews.identity_email")
        or secrets["identity_email"]
    )


@pytest.fixture(scope="session")
def yotpo_reviews_identity_phone_number(saas_config) -> str:
    return (
        pydash.get(saas_config, "yotpo_reviews.identity_phone_number")
        or secrets["identity_phone_number"]
    )


@pytest.fixture
def yotpo_reviews_erasure_identity_email() -> str:
    return generate_random_email()


class YotpoReviewsTestClient:
    def __init__(self, secrets: Dict[str, Any]):
        self.domain = secrets["domain"]
        self.store_id = secrets["store_id"]
        response = requests.post(
            url=f"https://{self.domain}/core/v3/stores/{self.store_id}/access_tokens",
            json={
                "secret": f"{secrets['secret_key']}",
            },
        )
        assert response.ok
        self.access_token = response.json()["access_token"]

    def create_customer(self, email: str) -> Response:
        faker = Faker()
        return requests.patch(
            url=f"https://{self.domain}/core/v3/stores/{self.store_id}/customers",
            headers={"X-Yotpo-Token": self.access_token},
            json={
                "customer": {
                    "email": email,
                    "first_name": faker.first_name(),
                    "last_name": faker.last_name(),
                    "gender": "M",
                    "account_created_at": "2020-09-08T08:43:27Z",
                    "account_status": "enabled",
                    "default_language": "en",
                    "default_currency": "USD",
                    "accepts_sms_marketing": True,
                    "accepts_email_marketing": True,
                    "tags": "vipgold,loyal",
                    "address": {
                        "address1": faker.street_address(),
                        "address2": "",
                        "city": faker.city(),
                        "company": "null",
                        "state": faker.state(),
                        "zip": faker.zipcode(),
                        "country_code": "US",
                    },
                }
            },
        )

    def get_customer(self, email: str) -> Any:
        response = requests.get(
            url=f"https://{self.domain}/core/v3/stores/{self.store_id}/customers",
            headers={"X-Yotpo-Token": self.access_token},
            params={"email": email},
        )
        customers = response.json().get("customers")
        return (
            response if customers and customers[0]["first_name"] != "MASKED" else None
        )


@pytest.fixture
def yotpo_reviews_test_client(
    yotpo_reviews_secrets,
) -> Generator:
    test_client = YotpoReviewsTestClient(yotpo_reviews_secrets)
    yield test_client


@pytest.fixture
def yotpo_reviews_erasure_data(
    yotpo_reviews_test_client: YotpoReviewsTestClient,
    yotpo_reviews_erasure_identity_email,
) -> Generator:
    # create customer
    response = yotpo_reviews_test_client.create_customer(
        yotpo_reviews_erasure_identity_email
    )
    assert response.ok

    poll_for_existence(
        yotpo_reviews_test_client.get_customer,
        (yotpo_reviews_erasure_identity_email,),
        interval=30,
        verification_count=3,
    )

    yield yotpo_reviews_erasure_identity_email


@pytest.fixture
def yotpo_reviews_runner(
    db,
    cache,
    yotpo_reviews_secrets,
) -> ConnectorRunner:
    return ConnectorRunner(db, cache, "yotpo_reviews", yotpo_reviews_secrets)
