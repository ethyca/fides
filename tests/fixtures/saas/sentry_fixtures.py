from typing import Any, Dict, Generator

import pydash
import pytest
from sqlalchemy.orm import Session

from fides.api.db import session
from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.sql_models import Dataset as CtlDataset
from fides.api.util.saas_util import (
    load_config_with_replacement,
    load_dataset_with_replacement,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("sentry")


@pytest.fixture(scope="session")
def sentry_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "sentry.domain") or secrets["sentry.domain"],
        "access_token": pydash.get(saas_config, "sentry.access_token")
        or secrets["access_token"],
        "erasure_access_token": pydash.get(saas_config, "sentry.erasure_access_token")
        or secrets["erasure_access_token"],
        "erasure_identity_email": pydash.get(
            saas_config, "sentry.erasure_identity_email"
        )
        or secrets["erasure_identity_email"],
        "user_id_erasure": pydash.get(saas_config, "sentry.user_id_erasure")
        or secrets["user_id_erasure"],
        "issue_url": pydash.get(saas_config, "sentry.issue_url")
        or secrets["issue_url"],
    }


@pytest.fixture(scope="session")
def sentry_identity_email(saas_config):
    return pydash.get(saas_config, "sentry.identity_email") or secrets["identity_email"]


@pytest.fixture
def sentry_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/sentry_config.yml", "<instance_fides_key>", "sentry_dataset"
    )


@pytest.fixture
def sentry_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/sentry_dataset.yml", "<instance_fides_key>", "sentry_dataset"
    )[0]


@pytest.fixture(scope="function")
def sentry_connection_config(db: session, sentry_config, sentry_secrets) -> Generator:
    fides_key = sentry_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": sentry_secrets,
            "saas_config": sentry_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def sentry_connection_config_without_secrets(db: session, sentry_config) -> Generator:
    fides_key = sentry_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": {},
            "saas_config": sentry_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def sentry_dataset_config(
    db: Session,
    sentry_connection_config: ConnectionConfig,
    sentry_dataset: Dict[str, Any],
) -> Generator:
    fides_key = sentry_dataset["fides_key"]
    sentry_connection_config.name = fides_key
    sentry_connection_config.key = fides_key
    sentry_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, sentry_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": sentry_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture
def sentry_dataset_config_without_secrets(
    db: Session,
    sentry_connection_config_without_secrets: ConnectionConfig,
    sentry_dataset: Dict[str, Any],
) -> Generator:
    fides_key = sentry_dataset["fides_key"]
    sentry_connection_config_without_secrets.name = fides_key
    sentry_connection_config_without_secrets.key = fides_key
    sentry_connection_config_without_secrets.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, sentry_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": sentry_connection_config_without_secrets.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)
