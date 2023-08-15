from time import sleep
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

secrets = get_secrets("vend")


@pytest.fixture(scope="session")
def vend_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "vend.domain") or secrets["domain"],
        "token": pydash.get(saas_config, "vend.token") or secrets["token"],
    }


@pytest.fixture(scope="session")
def vend_identity_email(saas_config):
    return pydash.get(saas_config, "vend.identity_email") or secrets["identity_email"]


@pytest.fixture(scope="function")
def vend_erasure_identity_email() -> str:
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture
def vend_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/vend_config.yml",
        "<instance_fides_key>",
        "vend_instance",
    )


@pytest.fixture
def vend_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/vend_dataset.yml",
        "<instance_fides_key>",
        "vend_instance",
    )[0]


@pytest.fixture(scope="function")
def vend_connection_config(db: Session, vend_config, vend_secrets) -> Generator:
    fides_key = vend_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": vend_secrets,
            "saas_config": vend_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def vend_dataset_config(
    db: Session,
    vend_connection_config: ConnectionConfig,
    vend_dataset: Dict[str, Any],
) -> Generator:
    fides_key = vend_dataset["fides_key"]
    vend_connection_config.name = fides_key
    vend_connection_config.key = fides_key
    vend_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, vend_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": vend_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture(scope="function")
def vend_create_erasure_data(
    vend_connection_config: ConnectionConfig, vend_erasure_identity_email: str
) -> None:
    vend_secrets = vend_connection_config.secrets
    headers = {
        "Authorization": f"Bearer {vend_secrets['token']}",
    }
    base_url = f"https://{vend_secrets['domain']}"

    # customer
    body = {
        "first_name": "Ethyca",
        "last_name": "Test Erasure",
        "email": vend_erasure_identity_email,
        "do_not_email": "true",
    }

    customers_response = requests.post(
        url=f"{base_url}/api/2.0/customers", headers=headers, json=body
    )
    customer = customers_response.json()

    # there is no endpoint to create a sale so we cannot test it
    sleep(60)

    yield customer
