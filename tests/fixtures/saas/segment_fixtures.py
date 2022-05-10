from fidesops.core.config import load_toml
from fidesops.db import session
from fidesops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fidesops.models.datasetconfig import DatasetConfig
import pytest
import pydash
import os
from typing import Any, Dict, Generator
from tests.fixtures.application_fixtures import load_dataset
from tests.fixtures.saas_example_fixtures import load_config
from sqlalchemy.orm import Session

saas_config = load_toml("saas_config.toml")


@pytest.fixture(scope="function")
def segment_secrets():
    return {
        "domain": pydash.get(saas_config, "segment.domain")
        or os.environ.get("SEGMENT_DOMAIN"),
        "personas_domain": pydash.get(saas_config, "segment.personas_domain")
        or os.environ.get("SEGMENT_PERSONAS_DOMAIN"),
        "workspace": pydash.get(saas_config, "segment.workspace")
        or os.environ.get("SEGMENT_WORKSPACE"),
        "access_token": pydash.get(saas_config, "segment.access_token")
        or os.environ.get("SEGMENT_ACCESS_TOKEN"),
        "namespace_id": pydash.get(saas_config, "segment.namespace_id")
        or os.environ.get("SEGMENT_NAMESPACE_ID"),
        "access_secret": pydash.get(saas_config, "segment.access_secret")
        or os.environ.get("SEGMENT_ACCESS_SECRET"),
        "api_domain": pydash.get(saas_config, "segment.api_domain")
        or os.environ.get("SEGMENT_API_DOMAIN"),
        "user_token": pydash.get(saas_config, "segment.user_token")
        or os.environ.get("SEGMENT_USER_TOKEN"),
    }


@pytest.fixture(scope="function")
def segment_identity_email():
    return pydash.get(saas_config, "segment.identity_email") or os.environ.get(
        "SEGMENT_IDENTITY_EMAIL"
    )


@pytest.fixture
def segment_config() -> Dict[str, Any]:
    return load_config("data/saas/config/segment_config.yml")


@pytest.fixture
def segment_dataset() -> Dict[str, Any]:
    return load_dataset("data/saas/dataset/segment_dataset.yml")[0]


@pytest.fixture(scope="function")
def segment_connection_config(
    db: session, segment_config, segment_secrets
) -> Generator:
    fides_key = segment_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": segment_secrets,
            "saas_config": segment_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def segment_dataset_config(
    db: Session,
    segment_connection_config: ConnectionConfig,
    segment_dataset: Dict[str, Any],
) -> Generator:
    fides_key = segment_dataset["fides_key"]
    segment_connection_config.name = fides_key
    segment_connection_config.key = fides_key
    segment_connection_config.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": segment_connection_config.id,
            "fides_key": fides_key,
            "dataset": segment_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)
