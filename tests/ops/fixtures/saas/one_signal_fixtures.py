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

secrets = get_secrets("one_signal")


@pytest.fixture(scope="session")
def one_signal_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "one_signal.domain") or secrets["domain"],
        "app_id": pydash.get(saas_config, "one_signal.app_id") or secrets["app_id"],
        "api_key": pydash.get(saas_config, "one_signal.api_key") or secrets["api_key"],
        "player_id": pydash.get(saas_config, "one_signal.player_id") or secrets["player_id"]
    }


@pytest.fixture(scope="session")
def one_signal_identity_email(saas_config):
    return (
        pydash.get(saas_config, "one_signal.identity_email") or secrets["identity_email"]
    )


@pytest.fixture(scope="function")
def one_signal_erasure_identity_email() -> str:
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture
def one_signal_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/one_signal_config.yml",
        "<instance_fides_key>",
        "one_signal_instance",
    )


@pytest.fixture
def one_signal_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/one_signal_dataset.yml",
        "<instance_fides_key>",
        "one_signal_instance",
    )[0]


@pytest.fixture(scope="function")
def one_signal_connection_config(
    db: Session, one_signal_config, one_signal_secrets
) -> Generator:
    fides_key = one_signal_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": one_signal_secrets,
            "saas_config": one_signal_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def one_signal_dataset_config(
    db: Session,
    one_signal_connection_config: ConnectionConfig,
    one_signal_dataset: Dict[str, Any],
) -> Generator:
    fides_key = one_signal_dataset["fides_key"]
    one_signal_connection_config.name = fides_key
    one_signal_connection_config.key = fides_key
    one_signal_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, one_signal_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": one_signal_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)
    
@pytest.fixture(scope="function")
def one_signal_create_erasure_data(
    one_signal_connection_config: ConnectionConfig, one_signal_erasure_identity_email: str
) -> None:

    #sleep(60)

    one_signal_secrets = one_signal_connection_config.secrets
    base_url = f"https://{one_signal_secrets['domain']}"

    # device
    body = {
        "app_id" : one_signal_secrets['app_id'],
        "device_type" : 1,
        "identifier": one_signal_erasure_identity_email
    }
    
    headers = {"Authorization": f"basic {one_signal_secrets['api_key']}"}

    response = requests.post(url=f"{base_url}/api/v1/players", headers=headers, json=body)
    device = response.json()

   
    yield device
