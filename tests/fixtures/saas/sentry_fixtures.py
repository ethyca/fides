import os
from typing import Any, Dict, Generator

import pydash
import pytest
from sqlalchemy.orm import Session

from fidesops.core.config import load_toml
from fidesops.db import session
from fidesops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fidesops.models.datasetconfig import DatasetConfig
from tests.fixtures.application_fixtures import load_dataset
from tests.fixtures.saas_example_fixtures import load_config

saas_config = load_toml("saas_config.toml")


@pytest.fixture(scope="function")
def sentry_secrets():
    return {
        "host": pydash.get(saas_config, "sentry.host") or os.environ.get("SENTRY_HOST"),
        "access_token": pydash.get(saas_config, "sentry.access_token")
        or os.environ.get("SENTRY_ACCESS_TOKEN"),
        "erasure_access_token": pydash.get(saas_config, "sentry.erasure_access_token")
        or os.environ.get("SENTRY_ERASURE_TOKEN"),
        "erasure_identity_email": pydash.get(
            saas_config, "sentry.erasure_identity_email"
        )
        or os.environ.get("SENTRY_ERASURE_IDENTITY"),
        "user_id_erasure": pydash.get(saas_config, "sentry.user_id_erasure")
        or os.environ.get("SENTRY_USER_ID"),
        "issue_url": pydash.get(saas_config, "sentry.issue_url")
        or os.environ.get("SENTRY_ISSUE_URL"),
    }


@pytest.fixture(scope="function")
def sentry_identity_email():
    return pydash.get(saas_config, "sentry.identity_email") or os.environ.get(
        "SENTRY_IDENTITY_EMAIL"
    )


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
