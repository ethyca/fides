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

secrets = get_secrets("marketo")


@pytest.fixture(scope="session")
def marketo_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "marketo.domain") or secrets["domain"],
        "access_token": pydash.get(saas_config, "marketo.access_token")
        or secrets["access_token"],
    }


@pytest.fixture(scope="session")
def marketo_identity_email(saas_config):
    return (
        pydash.get(saas_config, "marketo.identity_email") or secrets["identity_email"]
    )


@pytest.fixture
def marketo_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/marketo_config.yml",
        "<instance_fides_key>",
        "marketo_instance",
    )


@pytest.fixture
def marketo_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/marketo_dataset.yml",
        "<instance_fides_key>",
        "marketo_instance",
    )[0]


@pytest.fixture(scope="function")
def marketo_connection_config(
    db: session, marketo_config, marketo_secrets
) -> Generator:
    fides_key = marketo_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": marketo_secrets,
            "saas_config": marketo_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def marketo_dataset_config(
    db: Session,
    marketo_connection_config: ConnectionConfig,
    marketo_dataset,
    marketo_config,
) -> Generator:
    fides_key = marketo_config["fides_key"]
    marketo_connection_config.name = fides_key
    marketo_connection_config.key = fides_key
    marketo_connection_config.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": marketo_connection_config.id,
            "fides_key": fides_key,
            "dataset": marketo_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)
