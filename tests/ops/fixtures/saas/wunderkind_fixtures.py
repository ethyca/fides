import json
from typing import Any, Dict, Generator

import pydash
import pytest
from sqlalchemy.orm import Session

from fides.api.ctl.sql_models import Dataset as CtlDataset
from fides.api.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.ops.models.datasetconfig import DatasetConfig
from fides.api.ops.schemas.saas.saas_config import SaaSRequest
from fides.api.ops.schemas.saas.shared_schemas import HTTPMethod, SaaSRequestParams
from fides.api.ops.service.connectors import SaaSConnector
from fides.api.ops.util.saas_util import (
    load_config_with_replacement,
    load_dataset_with_replacement,
)
from fides.lib.db import session
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("wunderkind")


@pytest.fixture(scope="session")
def wunderkind_secrets(saas_config):
    return {
        "website_id": pydash.get(saas_config, "wunderkind.website_id")
        or secrets["domain"]
    }


@pytest.fixture(scope="session")
def wunderkind_identity_email(saas_config):
    return "customer-1@example.com"


@pytest.fixture
def wunderkind_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/wunderkind_config.yml",
        "<instance_fides_key>",
        "wunderkind_instance",
    )


@pytest.fixture
def wunderkind_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/wunderkind_dataset.yml",
        "<instance_fides_key>",
        "wunderkind_instance",
    )[0]


@pytest.fixture(scope="function")
def wunderkind_connection_config(
    db: session, wunderkind_config, wunderkind_secrets
) -> Generator:
    fides_key = wunderkind_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": wunderkind_secrets,
            "saas_config": wunderkind_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def wunderkind_dataset_config(
    db: Session,
    wunderkind_connection_config: ConnectionConfig,
    wunderkind_dataset: Dict[str, Any],
) -> Generator:
    fides_key = wunderkind_dataset["fides_key"]
    wunderkind_connection_config.name = fides_key
    wunderkind_connection_config.key = fides_key
    wunderkind_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, wunderkind_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": wunderkind_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)
