from typing import Any, Dict, Generator

import pydash
import pytest
import requests
from faker import Faker
from requests import Response
from sqlalchemy.orm import Session

from fides.api.cryptography import cryptographic_util
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

secrets = get_secrets("yotpo_loyalty")


@pytest.fixture(scope="session")
def yotpo_loyalty_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "yotpo_loyalty.domain") or secrets["domain"],
        "merchant_id": pydash.get(saas_config, "yotpo_loyalty.merchant_id")
        or secrets["merchant_id"],
        "guid": pydash.get(saas_config, "yotpo_loyalty.guid") or secrets["guid"],
        "api_key": pydash.get(saas_config, "yotpo_loyalty.api_key")
        or secrets["api_key"],
        "store_id": pydash.get(saas_config, "yotpo_loyalty.store_id")
        or secrets["store_id"],
        "secret_key": pydash.get(saas_config, "yotpo_loyalty.secret_key")
        or secrets["secret_key"],
    }


@pytest.fixture(scope="session")
def yotpo_loyalty_identity_email(saas_config):
    return (
        pydash.get(saas_config, "yotpo_loyalty.identity_email")
        or secrets["identity_email"]
    )


@pytest.fixture(scope="session")
def yotpo_loyalty_identity_phone_number(saas_config):
    return (
        pydash.get(saas_config, "yotpo_loyalty.identity_phone_number")
        or secrets["identity_phone_number"]
    )


@pytest.fixture(scope="function")
def yotpo_loyalty_erasure_identity_email() -> str:
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture
def yotpo_loyalty_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/yotpo_loyalty_config.yml",
        "<instance_fides_key>",
        "yotpo_loyalty_instance",
    )


@pytest.fixture
def yotpo_loyalty_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/yotpo_loyalty_dataset.yml",
        "<instance_fides_key>",
        "yotpo_loyalty_instance",
    )[0]


@pytest.fixture(scope="function")
def yotpo_loyalty_connection_config(
    db: Session, yotpo_loyalty_config, yotpo_loyalty_secrets
) -> Generator:
    fides_key = yotpo_loyalty_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": yotpo_loyalty_secrets,
            "saas_config": yotpo_loyalty_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def yotpo_loyalty_dataset_config(
    db: Session,
    yotpo_loyalty_connection_config: ConnectionConfig,
    yotpo_loyalty_dataset: Dict[str, Any],
) -> Generator:
    fides_key = yotpo_loyalty_dataset["fides_key"]
    yotpo_loyalty_connection_config.name = fides_key
    yotpo_loyalty_connection_config.key = fides_key
    yotpo_loyalty_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, yotpo_loyalty_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": yotpo_loyalty_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


class YotpoLoyaltyTestClient:
    def __init__(self, connection_config: ConnectionConfig):
        yotpo_loyalty_secrets = connection_config.secrets
        self.domain = yotpo_loyalty_secrets["domain"]
        self.headers = {
            "x-guid": yotpo_loyalty_secrets["guid"],
            "x-api-key": yotpo_loyalty_secrets["api_key"],
        }

    def create_customer(self, email: str) -> Response:
        faker = Faker()
        return requests.post(
            url=f"https://{self.domain}/api/v2/customers",
            headers=self.headers,
            json={
                "email": email,
                "first_name": faker.first_name(),
                "last_name": faker.last_name(),
            },
        )

    def get_customer(self, email: str) -> Any:
        response = requests.get(
            url=f"https://{self.domain}/api/v2/customers",
            headers=self.headers,
            params={"customer_email": email},
        )
        if not response.status_code == 404:
            return response


@pytest.fixture(scope="function")
def yotpo_loyalty_test_client(
    yotpo_loyalty_connection_config: ConnectionConfig,
) -> Generator:
    test_client = YotpoLoyaltyTestClient(yotpo_loyalty_connection_config)
    yield test_client


@pytest.fixture(scope="function")
def yotpo_loyalty_erasure_data(
    yotpo_loyalty_test_client: YotpoLoyaltyTestClient,
    yotpo_loyalty_erasure_identity_email,
) -> None:
    # create customer
    response = yotpo_loyalty_test_client.create_customer(
        yotpo_loyalty_erasure_identity_email
    )
    assert response.ok

    poll_for_existence(
        yotpo_loyalty_test_client.get_customer,
        (yotpo_loyalty_erasure_identity_email,),
        interval=30,
        verification_count=3,
    )
