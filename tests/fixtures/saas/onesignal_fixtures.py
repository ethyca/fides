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

secrets = get_secrets("onesignal")


@pytest.fixture(scope="session")
def onesignal_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "onesignal.domain") or secrets["domain"],
        "api_key": pydash.get(saas_config, "onesignal.api_key") or secrets["api_key"],
        "app_id": pydash.get(saas_config, "onesignal.app_id") or secrets["app_id"],
        "player_id": pydash.get(saas_config, "onesignal.player_id")
        or secrets["player_id"],
    }


@pytest.fixture(scope="session")
def onesignal_identity_email(saas_config):
    return (
        pydash.get(saas_config, "onesignal.identity_email") or secrets["identity_email"]
    )


@pytest.fixture(scope="function")
def onesignal_erasure_identity_email() -> str:
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture
def onesignal_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/onesignal_config.yml",
        "<instance_fides_key>",
        "onesignal_instance",
    )


@pytest.fixture
def onesignal_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/onesignal_dataset.yml",
        "<instance_fides_key>",
        "onesignal_instance",
    )[0]


@pytest.fixture(scope="function")
def onesignal_connection_config(
    db: Session, onesignal_config, onesignal_secrets
) -> Generator:
    fides_key = onesignal_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": onesignal_secrets,
            "saas_config": onesignal_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def onesignal_dataset_config(
    db: Session,
    onesignal_connection_config: ConnectionConfig,
    onesignal_dataset: Dict[str, Any],
) -> Generator:
    fides_key = onesignal_dataset["fides_key"]
    onesignal_connection_config.name = fides_key
    onesignal_connection_config.key = fides_key
    onesignal_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, onesignal_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": onesignal_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture(scope="function")
def onesignal_create_erasure_data(
    onesignal_connection_config: ConnectionConfig, onesignal_erasure_identity_email: str
) -> None:

    sleep(60)

    onesignal_secrets = onesignal_connection_config.secrets
    base_url = f"https://{onesignal_secrets['domain']}"
    headers={}

    # user
    body = {
     "app_id": f"{onesignal_secrets['app_id']}",
     "device_type": 11,
     "identifier": onesignal_erasure_identity_email,
     "tags": {
          "first_name": "test erasure",
          "last_name": "check",         
     },
    }

    users_response = requests.post(url=f"{base_url}/api/v1/players", headers=headers, json=body)
    user = users_response.json()
    user_id = user["id"]

    yield user_id
