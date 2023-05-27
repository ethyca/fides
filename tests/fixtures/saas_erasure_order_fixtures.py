from typing import Any, Dict, Generator

import pytest
from sqlalchemy.orm import Session

from fides.api.ctl.sql_models import Dataset as CtlDataset
from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.util.saas_util import (
    load_config_with_replacement,
    load_dataset_with_replacement,
)


@pytest.fixture(scope="function")
def saas_erasure_order_secrets():
    return {"domain": "domain"}


@pytest.fixture
def saas_erasure_order_config() -> Dict:
    return load_config_with_replacement(
        "data/saas/config/saas_erasure_order_config.yml",
        "<instance_fides_key>",
        "saas_erasure_order_instance",
    )


@pytest.fixture
def saas_erasure_order_dataset() -> Dict:
    return load_dataset_with_replacement(
        "data/saas/dataset/saas_erasure_order_dataset.yml",
        "<instance_fides_key>",
        "saas_erasure_order_instance",
    )[0]


@pytest.fixture(scope="function")
def saas_erasure_order_connection_config(
    db: Session,
    saas_erasure_order_config: Dict[str, Any],
    saas_erasure_order_secrets: Dict[str, Any],
) -> Generator:
    fides_key = saas_erasure_order_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": saas_erasure_order_secrets,
            "saas_config": saas_erasure_order_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def saas_erasure_order_dataset_config(
    db: Session,
    saas_erasure_order_connection_config: ConnectionConfig,
    saas_erasure_order_dataset: Dict,
) -> Generator:
    fides_key = saas_erasure_order_dataset["fides_key"]
    saas_erasure_order_connection_config.name = fides_key
    saas_erasure_order_connection_config.key = fides_key
    saas_erasure_order_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, saas_erasure_order_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": saas_erasure_order_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db)
