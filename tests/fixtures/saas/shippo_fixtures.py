from typing import Any, Dict, Generator

import pydash
import pytest
import requests
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
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("shippo")


@pytest.fixture(scope="session")
def shippo_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "shippo.domain") or secrets["domain"],
        "api_key": pydash.get(saas_config, "shippo.api_key") or secrets["api_key"],
    }


@pytest.fixture(scope="session")
def shippo_identity_email(saas_config):
    return pydash.get(saas_config, "shippo.identity_email") or secrets["identity_email"]


@pytest.fixture(scope="function")
def shippo_erasure_identity_email() -> str:
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture
def shippo_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/shippo_config.yml",
        "<instance_fides_key>",
        "shippo_instance",
    )


@pytest.fixture
def shippo_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/shippo_dataset.yml",
        "<instance_fides_key>",
        "shippo_instance",
    )[0]


@pytest.fixture(scope="function")
def shippo_connection_config(db: Session, shippo_config, shippo_secrets) -> Generator:
    fides_key = shippo_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": shippo_secrets,
            "saas_config": shippo_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def shippo_dataset_config(
    db: Session,
    shippo_connection_config: ConnectionConfig,
    shippo_dataset: Dict[str, Any],
) -> Generator:
    fides_key = shippo_dataset["fides_key"]
    shippo_connection_config.name = fides_key
    shippo_connection_config.key = fides_key
    shippo_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, shippo_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": shippo_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture(scope="function")
def shippo_create_erasure_data(
    shippo_connection_config: ConnectionConfig, shippo_erasure_identity_email: str
) -> None:
    shippo_secrets = shippo_connection_config.secrets
    base_url = f"https://{shippo_secrets['domain']}"
    headers = {
        "Authorization": f"ShippoToken {shippo_secrets['api_key']}",
    }

    # address
    body = {
        "name": "Ethyca Test Erasure",
        "company": "Ethyca Test company",
        "street1": "test street",
        "city": "test city",
        "state": "test state",
        "zip": "test zip",
        "country": "test country",
        "email": shippo_erasure_identity_email,
    }

    address_response = requests.post(
        url=f"{base_url}/addresses", headers=headers, json=body
    )
    address = address_response.json()
    address_id = address["object_id"]

    # orders
    order_data = {
        "to_address": {
            "city": "test city",
            "company": "test company",
            "country": "test country",
            "email": shippo_erasure_identity_email,
            "name": "Ethyca test erasure",
            "state": "test state",
            "street1": "test street",
            "zip": "test zip",
        },
        "line_items": [
            {
                "quantity": 1,
                "sku": "HM-123",
                "title": "Hippo Magazines",
                "total_price": "12.10",
                "currency": "USD",
                "weight": "0.40",
                "weight_unit": "lb",
            }
        ],
        "placed_at": "2023-01-31T01:28:12Z",
        "order_number": "#1068",
        "order_status": "PAID",
        "shipping_cost": "12.83",
        "shipping_cost_currency": "USD",
        "shipping_method": "USPS First Class Package",
        "subtotal_price": "12.10",
        "total_price": "24.93",
        "total_tax": "0.00",
        "currency": "USD",
        "weight": "0.40",
        "weight_unit": "lb",
    }
    response = requests.post(url=f"{base_url}/orders", headers=headers, json=order_data)
    order = response.json()
    order_id = order["object_id"]
    yield address, order
