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

secrets = get_secrets("slack")


@pytest.fixture(scope="session")
def slack_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "slack.domain") or secrets["domain"],
        "access_token": pydash.get(saas_config, "slack.access_token")
        or secrets["access_token"],
    }


@pytest.fixture(scope="session")
def slack_identity_email(saas_config):
    return pydash.get(saas_config, "slack.identity_email") or secrets["identity_email"]


@pytest.fixture
def slack_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/slack_config.yml",
        "<instance_fides_key>",
        "slack_instance",
    )


@pytest.fixture
def slack_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/slack_dataset.yml",
        "<instance_fides_key>",
        "slack_instance",
    )[0]


@pytest.fixture(scope="function")
def slack_connection_config(db: session, slack_config, slack_secrets) -> Generator:
    fides_key = slack_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": slack_secrets,
            "saas_config": slack_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def slack_dataset_config(
    db: Session,
    slack_connection_config: ConnectionConfig,
    slack_dataset,
    slack_config,
) -> Generator:
    fides_key = slack_config["fides_key"]
    slack_connection_config.name = fides_key
    slack_connection_config.key = fides_key
    slack_connection_config.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": slack_connection_config.id,
            "fides_key": fides_key,
            "dataset": slack_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)
