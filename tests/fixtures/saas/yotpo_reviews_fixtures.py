from time import sleep
from typing import Any, Dict, Generator, Optional
from uuid import uuid4

import pydash
import pytest
import requests
from faker import Faker
from requests import Response

from fides.api.ops.models.connectionconfig import ConnectionConfig
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


@pytest.fixture
def yotpo_reviews_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def yotpo_reviews_erasure_yotpo_external_id() -> str:
    return f"ext-{uuid4()}"


@pytest.fixture
def yotpo_reviews_external_references() -> Dict[str, Any]:
    return {"yotpo_external_id": "ak123798684365sdfkj"}


@pytest.fixture
def yotpo_reviews_erasure_external_references(
    yotpo_reviews_erasure_yotpo_external_id,
) -> Dict[str, Any]:
    return {"yotpo_external_id": yotpo_reviews_erasure_yotpo_external_id}


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

    def create_customer(self, external_id: str, email: str) -> Response:
        faker = Faker()
        return requests.patch(
            url=f"https://{self.domain}/core/v3/stores/{self.store_id}/customers",
            headers={"X-Yotpo-Token": self.access_token},
            json={
                "customer": {
                    "external_id": external_id,
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

    def get_customer(self, external_id: str) -> Optional[Response]:
        response = requests.get(
            url=f"https://{self.domain}/core/v3/stores/{self.store_id}/customers",
            headers={"X-Yotpo-Token": self.access_token},
            params={"external_ids": external_id},
        )
        return response if response.json().get("customers") else None


@pytest.fixture
def yotpo_reviews_test_client(
    yotpo_reviews_secrets,
) -> Generator:
    test_client = YotpoReviewsTestClient(yotpo_reviews_secrets)
    yield test_client


@pytest.fixture
def yotpo_reviews_erasure_data(
    yotpo_reviews_test_client: YotpoReviewsTestClient,
    yotpo_reviews_erasure_yotpo_external_id,
    yotpo_reviews_erasure_identity_email,
) -> Generator:
    # create customer
    response = yotpo_reviews_test_client.create_customer(
        yotpo_reviews_erasure_yotpo_external_id, yotpo_reviews_erasure_identity_email
    )
    assert response.ok

    poll_for_existence(
        yotpo_reviews_test_client.get_customer,
        (yotpo_reviews_erasure_yotpo_external_id,),
        interval=30,
        verification_count=3,
    )

    yield yotpo_reviews_erasure_identity_email, yotpo_reviews_erasure_yotpo_external_id


@pytest.fixture
def yotpo_reviews_runner(
    db,
    cache,
    yotpo_reviews_secrets,
    yotpo_reviews_external_references,
    yotpo_reviews_erasure_external_references,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "yotpo_reviews",
        yotpo_reviews_secrets,
        external_references=yotpo_reviews_external_references,
        erasure_external_references=yotpo_reviews_erasure_external_references,
    )
