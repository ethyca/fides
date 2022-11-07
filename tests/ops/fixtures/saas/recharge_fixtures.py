from typing import Any, Dict, Generator

import pydash
import pytest
from fideslib.db import session
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


secrets = get_secrets("recharge")


@pytest.fixture(scope="function")
def recharge_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "recharge.domain") or secrets["domain"],
        "api_key": pydash.get(saas_config, "recharge.api_key") or secrets["api_key"],
    }


@pytest.fixture(scope="function")
def recharge_identity_email(saas_config):
    return (
        pydash.get(saas_config, "recharge.identity_email") or secrets["identity_email"]
    )


@pytest.fixture
def recharge_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/recharge_config.yml",
        "<instance_fides_key>",
        "recharge_instance",
    )


@pytest.fixture
def recharge_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/recharge_dataset.yml",
        "<instance_fides_key>",
        "recharge_instance",
    )[0]


@pytest.fixture(scope="function")
def recharge_connection_config(
    db: session, recharge_config, recharge_secrets
) -> Generator:
    fides_key = recharge_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": recharge_secrets,
            "saas_config": recharge_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def recharge_dataset_config(
    db: Session,
    recharge_connection_config: ConnectionConfig,
    recharge_dataset: Dict[str, Any],
) -> Generator:
    fides_key = recharge_dataset["fides_key"]
    recharge_connection_config.name = fides_key
    recharge_connection_config.key = fides_key
    recharge_connection_config.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": recharge_connection_config.id,
            "fides_key": fides_key,
            "dataset": recharge_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)
