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
from tests.ops.test_helpers.saas_test_utils import poll_for_existence
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("klaviyo")


@pytest.fixture(scope="session")
def klaviyo_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "klaviyo.domain") or secrets["domain"],
        "api_key": pydash.get(saas_config, "klaviyo.api_key") or secrets["api_key"]
    }


@pytest.fixture(scope="session")
def klaviyo_identity_email(saas_config):
    return (
        pydash.get(saas_config, "klaviyo.identity_email") or secrets["identity_email"]
    )


@pytest.fixture(scope="function")
def klaviyo_erasure_identity_email() -> str:
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture
def klaviyo_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/klaviyo_config.yml",
        "<instance_fides_key>",
        "klaviyo_instance",
    )


@pytest.fixture
def klaviyo_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/klaviyo_dataset.yml",
        "<instance_fides_key>",
        "klaviyo_instance",
    )[0]


@pytest.fixture(scope="function")
def klaviyo_connection_config(
    db: Session, klaviyo_config, klaviyo_secrets
) -> Generator:
    fides_key = klaviyo_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": klaviyo_secrets,
            "saas_config": klaviyo_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def klaviyo_dataset_config(
    db: Session,
    klaviyo_connection_config: ConnectionConfig,
    klaviyo_dataset: Dict[str, Any],
) -> Generator:
    fides_key = klaviyo_dataset["fides_key"]
    klaviyo_connection_config.name = fides_key
    klaviyo_connection_config.key = fides_key
    klaviyo_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, klaviyo_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": klaviyo_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)

@pytest.fixture(scope="function")
def klaviyo_create_erasure_data(
    klaviyo_connection_config: ConnectionConfig, klaviyo_erasure_identity_email: str
) -> None:

    # sleep(60)

    klaviyo_secrets = klaviyo_connection_config.secrets
    base_url = f"https://{klaviyo_secrets['domain']}"
    headers = {
        "Authorization": f"Klaviyo-API-Key {klaviyo_secrets['api_key']}",
        "revision": "2023-02-03"
    }
    # user
    body = {
        "data": {
            "type": "profile",
            "attributes": {
                "email": klaviyo_erasure_identity_email
            }
        }
    }

    users_response = requests.post(url=f"{base_url}/api/profiles/", headers=headers, json=body)
    user = users_response.json()

    yield user
