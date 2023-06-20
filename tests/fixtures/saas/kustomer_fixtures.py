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

secrets = get_secrets("kustomer")


@pytest.fixture(scope="session")
def kustomer_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "kustomer.domain") or secrets["domain"],
        "api_key": pydash.get(saas_config, "kustomer.api_key") or secrets["api_key"],
    }


@pytest.fixture(scope="session")
def kustomer_identity_email(saas_config):
    return (
        pydash.get(saas_config, "kustomer.identity_email") or secrets["identity_email"]
    )


@pytest.fixture(scope="session")
def kustomer_non_existent_identity_email(saas_config):
    email_not_in_kustomer = "not_in_kustomer@example.com"
    return email_not_in_kustomer


@pytest.fixture(scope="session")
def kustomer_identity_phone_number(saas_config):
    return (
        pydash.get(saas_config, "kustomer.identity_phone_number")
        or secrets["identity_phone_number"]
    )


@pytest.fixture(scope="function")
def kustomer_erasure_identity_email() -> str:
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture
def kustomer_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/kustomer_config.yml",
        "<instance_fides_key>",
        "kustomer_instance",
    )


@pytest.fixture
def kustomer_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/kustomer_dataset.yml",
        "<instance_fides_key>",
        "kustomer_instance",
    )[0]


@pytest.fixture(scope="function")
def kustomer_connection_config(
    db: Session, kustomer_config, kustomer_secrets
) -> Generator:
    fides_key = kustomer_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": kustomer_secrets,
            "saas_config": kustomer_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def kustomer_dataset_config(
    db: Session,
    kustomer_connection_config: ConnectionConfig,
    kustomer_dataset: Dict[str, Any],
) -> Generator:
    fides_key = kustomer_dataset["fides_key"]
    kustomer_connection_config.name = fides_key
    kustomer_connection_config.key = fides_key
    kustomer_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, kustomer_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": kustomer_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture(scope="function")
def kustomer_create_erasure_data(
    kustomer_connection_config: ConnectionConfig, kustomer_erasure_identity_email: str
) -> None:
    kustomer_secrets = kustomer_connection_config.secrets
    base_url = f"https://{kustomer_secrets['domain']}"
    headers = {
        "Authorization": f"Bearer {kustomer_secrets['api_key']}",
    }
    # create customer
    body = {
        "name": "Ethyca Test Erasure",
        "emails": [{"email": kustomer_erasure_identity_email}],
    }

    customer_response = requests.post(
        url=f"{base_url}/v1/customers", headers=headers, json=body
    )
    customer = customer_response.json()
    yield customer
