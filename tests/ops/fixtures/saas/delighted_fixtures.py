from typing import Any, Dict, Generator

import pydash
import pytest
import requests
from sqlalchemy.orm import Session
from starlette.status import HTTP_202_ACCEPTED

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
from fides.lib.db import session
from tests.ops.test_helpers.saas_test_utils import poll_for_existence
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("delighted")

@pytest.fixture(scope="function")
def delighted_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "delighted.domain") or secrets["domain"],
        "username": pydash.get(saas_config, "delighted.username") or secrets["username"],
        "api_key": pydash.get(saas_config, "delighted.api_key") or secrets["api_key"],
        "identity_email": pydash.get(saas_config, "delighted.identity_email") or secrets["identity_email"],
    }

@pytest.fixture(scope="function")
def delighted_identity_email(saas_config):
    return (
        pydash.get(saas_config, "delighted.identity_email") or secrets["identity_email"]
    )


@pytest.fixture(scope="session")
def delighted_erasure_identity_email():
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture
def delighted_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/delighted_config.yml",
        "<instance_fides_key>",
        "delighted_instance",
    )


@pytest.fixture
def delighted_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/delighted_dataset.yml",
        "<instance_fides_key>",
        "delighted_instance",
    )[0]


@pytest.fixture(scope="function")
def delighted_connection_config(
    db: session, delighted_config, delighted_secrets
) -> Generator:
    fides_key = delighted_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": delighted_secrets,
            "saas_config": delighted_config,
        },
    )
    yield connection_config
    connection_config.delete(db)

@pytest.fixture
def delighted_dataset_config(
    db: Session,
    delighted_connection_config: ConnectionConfig,
    delighted_dataset: Dict[str, Any],
) -> Generator:
    fides_key = delighted_dataset["fides_key"]
    delighted_connection_config.name = fides_key
    delighted_connection_config.key = fides_key
    delighted_connection_config.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": delighted_connection_config.id,
            "fides_key": fides_key,
            "dataset": delighted_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)