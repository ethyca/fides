from typing import Any, Dict, Generator

import pydash
import pytest
from fideslib.db import session
from sqlalchemy.orm import Session

from fidesops.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fidesops.ops.models.datasetconfig import DatasetConfig
from fidesops.ops.util.saas_util import (
    load_config_with_replacement,
    load_dataset_with_replacement,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("rollbar")


@pytest.fixture(scope="session")
def rollbar_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "rollbar.domain") or secrets["domain"],
        "read_access_token": pydash.get(saas_config, "rollbar.read_access_token")
        or secrets["read_access_token"],
        "write_access_token": pydash.get(saas_config, "rollbar.write_access_token")
        or secrets["write_access_token"],
        "page_limit": pydash.get(saas_config, "rollbar.page_limit")
        or secrets["page_limit"],
    }


@pytest.fixture(scope="session")
def rollbar_identity_email(saas_config):
    return (
        pydash.get(saas_config, "rollbar.identity_email") or secrets["identity_email"]
    )


@pytest.fixture
def rollbar_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/rollbar_config.yml",
        "<instance_fides_key>",
        "rollbar_instance",
    )


@pytest.fixture
def rollbar_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/rollbar_dataset.yml",
        "<instance_fides_key>",
        "rollbar_instance",
    )[0]


@pytest.fixture(scope="function")
def rollbar_connection_config(
    db: session, rollbar_config, rollbar_secrets
) -> Generator:
    fides_key = rollbar_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": rollbar_secrets,
            "saas_config": rollbar_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def rollbar_dataset_config(
    db: Session,
    rollbar_connection_config: ConnectionConfig,
    rollbar_dataset,
    rollbar_config,
) -> Generator:
    fides_key = rollbar_config["fides_key"]
    rollbar_connection_config.name = fides_key
    rollbar_connection_config.key = fides_key
    rollbar_connection_config.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": rollbar_connection_config.id,
            "fides_key": fides_key,
            "dataset": rollbar_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)
