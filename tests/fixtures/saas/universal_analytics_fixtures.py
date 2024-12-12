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

secrets = get_secrets("google_analytics")  # Sharing secrets with google_analytics


@pytest.fixture(scope="session")
def universal_analytics_secrets(saas_config):
    # Obtaining an access token via the OAuth2.0 flow and adding directly to secrets makes this workflow
    # easier to test
    # Sharing secrets with google_analytics. They are identical except for web_property_id
    return {
        "client_id": pydash.get(saas_config, "google_analytics.client_id")
        or secrets["client_id"],
        "client_secret": pydash.get(saas_config, "google_analytics.client_secret")
        or secrets["client_secret"],
        "redirect_uri": pydash.get(saas_config, "google_analytics.redirect_uri")
        or secrets["redirect_uri"],
        "property_id": pydash.get(saas_config, "google_analytics.property_id")
        or secrets["property_id"],
        "access_token": pydash.get(saas_config, "google_analytics.access_token")
        or secrets["access_token"],
        "web_property_id": pydash.get(saas_config, "google_analytics.web_property_id")
        or secrets["web_property_id"],
    }


@pytest.fixture(scope="session")
def universal_analytics_client_id(saas_config):
    return "fides_test_client_id_ua"


@pytest.fixture
def universal_analytics_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/universal_analytics_config.yml",
        "<instance_fides_key>",
        "universal_analytics_instance",
    )


@pytest.fixture
def universal_analytics_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/universal_analytics_dataset.yml",
        "<instance_fides_key>",
        "universal_analytics_instance",
    )[0]


@pytest.fixture(scope="function")
def universal_analytics_connection_config(
    db: session, universal_analytics_config, universal_analytics_secrets
) -> Generator:
    fides_key = universal_analytics_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": universal_analytics_secrets,
            "saas_config": universal_analytics_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def universal_analytics_dataset_config(
    db: Session,
    universal_analytics_connection_config: ConnectionConfig,
    universal_analytics_dataset: Dict[str, Any],
) -> Generator:
    fides_key = universal_analytics_dataset["fides_key"]
    universal_analytics_connection_config.name = fides_key
    universal_analytics_connection_config.key = fides_key
    universal_analytics_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, universal_analytics_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": universal_analytics_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture(scope="function")
def universal_analytics_connection_config_without_secrets(
    db: session, universal_analytics_config
) -> Generator:
    """Universal analytics config without secrets - can't be used to make live requests"""
    fides_key = universal_analytics_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": {},
            "saas_config": universal_analytics_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def universal_analytics_dataset_config_without_secrets(
    db: Session,
    universal_analytics_connection_config_without_secrets: ConnectionConfig,
    universal_analytics_dataset: Dict[str, Any],
) -> Generator:
    """Universal analytics dataset config without secrets - can't be used to make live requests"""

    fides_key = universal_analytics_dataset["fides_key"]
    universal_analytics_connection_config_without_secrets.name = fides_key
    universal_analytics_connection_config_without_secrets.key = fides_key
    universal_analytics_connection_config_without_secrets.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, universal_analytics_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": universal_analytics_connection_config_without_secrets.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)
