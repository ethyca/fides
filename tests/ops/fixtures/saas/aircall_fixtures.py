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

secrets = get_secrets("aircall")


@pytest.fixture(scope="session")
def aircall_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "aircall.domain") or secrets["domain"],        
        "api_token": pydash.get(saas_config, "aircall.api_token") or secrets["api_token"],
    }


@pytest.fixture(scope="session")
def aircall_identity_email(saas_config):
    return (
        pydash.get(saas_config, "aircall.identity_email") or secrets["identity_email"]
    )

@pytest.fixture(scope="session")
def aircall_identity_phone_number(saas_config):
    return (
        pydash.get(saas_config, "aircall.identity_phone_number")
        or secrets["identity_phone_number"]
    )


@pytest.fixture(scope="function")
def aircall_erasure_identity_email() -> str:
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture
def aircall_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/aircall_config.yml",
        "<instance_fides_key>",
        "aircall_instance",
    )


@pytest.fixture
def aircall_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/aircall_dataset.yml",
        "<instance_fides_key>",
        "aircall_instance",
    )[0]


@pytest.fixture(scope="function")
def aircall_connection_config(
    db: Session, aircall_config, aircall_secrets
) -> Generator:
    fides_key = aircall_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": aircall_secrets,
            "saas_config": aircall_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def aircall_dataset_config(
    db: Session,
    aircall_connection_config: ConnectionConfig,
    aircall_dataset: Dict[str, Any],
) -> Generator:
    fides_key = aircall_dataset["fides_key"]
    aircall_connection_config.name = fides_key
    aircall_connection_config.key = fides_key
    aircall_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, aircall_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": aircall_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)
