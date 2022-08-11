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
from fidesops.ops.util.saas_util import load_config
from tests.ops.fixtures.application_fixtures import load_dataset
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
    return load_config("data/saas/config/sentry_config.yml")


@pytest.fixture
def sentry_dataset() -> Dict[str, Any]:
    return load_dataset("data/saas/dataset/sentry_dataset.yml")[0]


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
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": sentry_connection_config.id,
            "fides_key": fides_key,
            "dataset": sentry_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)
