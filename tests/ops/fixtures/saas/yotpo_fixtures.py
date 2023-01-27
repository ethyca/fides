from time import sleep
from typing import Any, Dict, Generator

import pydash
import pytest
import requests
from sqlalchemy.orm import Session

from fides.api.ctl.sql_models import Dataset as CtlDataset
from fides.api.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.ops.models.datasetconfig import DatasetConfig
from fides.api.ops.util.saas_util import (
    load_config_with_replacement,
    load_dataset_with_replacement,
)
from fides.lib.cryptography import cryptographic_util
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("yotpo")


@pytest.fixture(scope="session")
def yotpo_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "yotpo.domain") or secrets["domain"],
        "app_key": pydash.get(saas_config, "yotpo.app_key") or secrets["app_key"],
        "secret_key": pydash.get(saas_config, "yotpo.secret_key") or secrets["secret_key"],
        "external_id": pydash.get(saas_config, "yotpo.external_id") or secrets["external_id"],
        "x-guid": pydash.get(saas_config, "yotpo.x-guid") or secrets["x-guid"],
        "x-api-key": pydash.get(saas_config, "yotpo.x-api-key") or secrets["x-api-key"]
    }


@pytest.fixture(scope="session")
def yotpo_identity_email(saas_config):
    return (
        pydash.get(
            saas_config, "yotpo.identity_email") or secrets["identity_email"]
    )


@pytest.fixture(scope="function")
def yotpo_erasure_identity_email() -> str:
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture
def yotpo_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/yotpo_config.yml",
        "<instance_fides_key>",
        "yotpo_instance",
    )


@pytest.fixture
def yotpo_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/yotpo_dataset.yml",
        "<instance_fides_key>",
        "yotpo_instance",
    )[0]

@pytest.fixture(scope="function")
def yotpo_random_external_id() -> str:
    return f"{cryptographic_util.generate_secure_random_string(8)}"

@pytest.fixture(scope="function")
def yotpo_connection_config(
    db: Session, yotpo_config, yotpo_secrets
) -> Generator:
    fides_key = yotpo_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": yotpo_secrets,
            "saas_config": yotpo_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def yotpo_dataset_config(
    db: Session,
    yotpo_connection_config: ConnectionConfig,
    yotpo_dataset: Dict[str, Any],
) -> Generator:
    fides_key = yotpo_dataset["fides_key"]
    yotpo_connection_config.name = fides_key
    yotpo_connection_config.key = fides_key
    yotpo_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, yotpo_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": yotpo_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture(scope="function")
def yotpo_create_erasure_data(
    yotpo_connection_config: ConnectionConfig, yotpo_erasure_identity_email: str
) -> None:

    # sleep(60)

    yotpo_secrets = yotpo_connection_config.secrets
    secret_key = yotpo_secrets["secret_key"]
    app_key = yotpo_secrets["app_key"]
    base_url = f"https://{yotpo_secrets['domain']}"

    # uToken

    body = {
        "secret": f"{yotpo_secrets['secret_key']}",
    }

    response = requests.post(
        url=f"{base_url}/core/v3/stores/{app_key}/access_tokens", headers={}, json=body)
    token = response.json()['access_token']
    headers = {
        "X-Yotpo-Token": token
    }

    # Customer
    body = {
        "customer": {
            "external_id": yotpo_random_external_id,
            "email": yotpo_erasure_identity_email,
            "phone_number": "+14155552671",
            "first_name": "Tom",
            "last_name": "Smith"
        }
    }

    response = requests.patch(
        url=f"{base_url}/core/v3/stores/{app_key}/customers", headers=headers, json=body)

    customer = {}

    # Update customer
    body = {
        "external_id": yotpo_random_external_id,
        "phone_number": "123456789"
    }
    response = requests.patch(
        url=f"{base_url}/core/v3/stores/{app_key}/customers", headers=headers, json=body)

    # Reviews

    body = {
        "appkey": "3wU9yBbB7YLY2YzAUeY8V9TDBTqpLAQ4ehm2n5e8",
        "sku": "1234",
        "product_title": "test product",
        "display_name": "test",
        "review_content": "Hello Iam human",
        "review_score": "143",
        "email": yotpo_identity_email,
        "review_title": "Review"
    }
    
    response = requests.post(
        url=f"{base_url}/v1/widget/reviews", headers={}, json=body)
    assert response.json()['code'] == 200
    
    # Customer(Loyalty)
    body = {
        "email" : yotpo_identity_email
    }
    customerLoyaltyHeaders = {
        "x-guid" : f"{yotpo_secrets['x-guid']}",
        "x-api-key" : f"{yotpo_secrets['x-api-key']}"
    }
    
    response = requests.post(
        url=f"{base_url}/api/v2/customers", headers=customerLoyaltyHeaders, json=body)
    
    assert response.json()['code'] == 201
    
    
    yield customer
