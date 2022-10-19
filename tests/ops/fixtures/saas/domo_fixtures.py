from typing import Any, Dict, Generator

import pydash
import pytest
import requests
from faker import Faker
from fideslib.cryptography import cryptographic_util
from fideslib.db import session
from requests.auth import HTTPBasicAuth
from sqlalchemy.orm import Session

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
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("domo")
faker = Faker()


@pytest.fixture(scope="session")
def domo_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "domo.domain") or secrets["domain"],
        "client_id": pydash.get(saas_config, "domo.client_id") or secrets["client_id"],
        "client_secret": pydash.get(saas_config, "domo.client_secret")
        or secrets["client_secret"],
    }


@pytest.fixture(scope="session")
def domo_identity_email(saas_config):
    return pydash.get(saas_config, "domo.identity_email") or secrets["identity_email"]


@pytest.fixture(scope="session")
def domo_erasure_identity_email():
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture
def domo_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/domo_config.yml",
        "<instance_fides_key>",
        "domo_instance",
    )


@pytest.fixture
def domo_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/domo_dataset.yml",
        "<instance_fides_key>",
        "domo_instance",
    )[0]


@pytest.fixture(scope="function")
def domo_connection_config(
    db: session,
    domo_config,
    domo_secrets,
) -> Generator:
    fides_key = domo_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": domo_secrets,
            "saas_config": domo_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def domo_dataset_config(
    db: Session,
    domo_connection_config: ConnectionConfig,
    domo_dataset: Dict[str, Any],
) -> Generator:
    fides_key = domo_dataset["fides_key"]
    domo_connection_config.name = fides_key
    domo_connection_config.key = fides_key
    domo_connection_config.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": domo_connection_config.id,
            "fides_key": fides_key,
            "dataset": domo_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)