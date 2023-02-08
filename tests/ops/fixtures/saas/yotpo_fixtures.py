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
        "yopto_domain": pydash.get(saas_config, "yotpo.yopto_domain") or secrets["yopto_domain"],
        "loyalty_api_domain": pydash.get(saas_config, "yotpo.loyalty_api_domain") or secrets["loyalty_api_domain"],
        "app_key": pydash.get(saas_config, "yotpo.app_key") or secrets["app_key"],
        "secret_key": pydash.get(saas_config, "yotpo.secret_key") or secrets["secret_key"],
        "x_api_key": pydash.get(saas_config, "yotpo.x_api_key") or secrets["x_api_key"],
        "x_guid": pydash.get(saas_config, "yotpo.x_guid") or secrets["x_guid"],
        "identity_email": pydash.get(saas_config, "yotpo.identity_email") or secrets["identity_email"],
        "external_id": pydash.get(saas_config, "yotpo.external_id") or secrets["external_id"],
    }


@pytest.fixture(scope="session")
def yotpo_identity_email(saas_config):
    return (
        pydash.get(saas_config, "yotpo.identity_email") or secrets["identity_email"]
    )


@pytest.fixture(scope="function")
def yotpo_erasure_identity_email() -> str:
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture(scope="function")
def yotpo_erasure_external_id() -> str:
    return f"{cryptographic_util.generate_secure_random_string(13)}"


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
    yotpo_connection_config: ConnectionConfig, yotpo_erasure_identity_email: str, yotpo_erasure_external_id: str, yotpo_create_access_token : str
) -> None:

    # sleep(60)

    yotpo_secrets = yotpo_connection_config.secrets
    base_url = f"https://{yotpo_secrets['yopto_domain']}"
    appkey = yotpo_secrets['app_key']
    headers = {
        "X-Yotpo-Token": yotpo_create_access_token,
    }

    # user
    body = {
        "customer": {
            "external_id": yotpo_erasure_external_id,
            "email": yotpo_erasure_identity_email
        }
    }

    users_response = requests.patch(url=f"{base_url}/core/v3/stores/{appkey}/customers", headers=headers, json=body)
    user = users_response.ok

    sleep(30)

    yield user

@pytest.fixture(scope="function")
def yotpo_create_loyalty_user(
    yotpo_connection_config: ConnectionConfig, yotpo_erasure_identity_email: str
) -> None:

    yotpo_secrets = yotpo_connection_config.secrets
    base_url = f"https://{yotpo_secrets['loyalty_api_domain']}"
    headers = {
        "x-api-key": yotpo_secrets['x_api_key'],
        "x-guid": yotpo_secrets['x_guid'],
    }

    # user
    body = {
            "email": yotpo_erasure_identity_email,
            "first_name": "vivek",
            "last_name": "ct"
    }

    users_response = requests.post(url=f"{base_url}/api/v2/customers", headers=headers, json=body)
    loyalty_user = users_response.ok
        
    sleep(30)

    yield loyalty_user

@pytest.fixture(scope="function")
def yotpo_create_access_token(
    yotpo_connection_config: ConnectionConfig
) -> None:

    yotpo_secrets = yotpo_connection_config.secrets
    base_url = f"https://{yotpo_secrets['yopto_domain']}"
    appkey = yotpo_secrets['app_key']

    # user
    body = {
            "secret": yotpo_secrets['secret_key']
    }

    access_response = requests.post(url=f"{base_url}/core/v3/stores/{appkey}/access_tokens", json=body)
    token = access_response.json()["access_token"]

    yield token