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

secrets = get_secrets("google_analytics")


@pytest.fixture(scope="session")
def google_analytics_secrets(saas_config):
    # Obtaining an access token via the OAuth2.0 flow and adding directly to secrets makes this workflow
    # easier to test
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
    }


@pytest.fixture(scope="session")
def google_analytics_client_id(saas_config):
    return "fides_test_client_id"


@pytest.fixture
def google_analytics_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/google_analytics_config.yml",
        "<instance_fides_key>",
        "google_analytics_instance",
    )


@pytest.fixture
def google_analytics_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/google_analytics_dataset.yml",
        "<instance_fides_key>",
        "google_analytics_instance",
    )[0]


@pytest.fixture(scope="function")
def google_analytics_connection_config(
    db: session, google_analytics_config, google_analytics_secrets
) -> Generator:
    fides_key = google_analytics_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": google_analytics_secrets,
            "saas_config": google_analytics_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def google_analytics_dataset_config(
    db: Session,
    google_analytics_connection_config: ConnectionConfig,
    google_analytics_dataset: Dict[str, Any],
) -> Generator:
    fides_key = google_analytics_dataset["fides_key"]
    google_analytics_connection_config.name = fides_key
    google_analytics_connection_config.key = fides_key
    google_analytics_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, google_analytics_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": google_analytics_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture(scope="function")
def google_analytics_connection_config_without_secrets(
    db: session, google_analytics_config
) -> Generator:
    """This test connector can't be used to make live requests"""
    fides_key = "new_google_analytics_instance_no_secrets"
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": {},
            "saas_config": google_analytics_config,
        },
    )

    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def google_analytics_dataset_config_no_secrets(
    db: Session,
    google_analytics_connection_config_without_secrets: ConnectionConfig,
    google_analytics_dataset: Dict[str, Any],
) -> Generator:
    fides_key = google_analytics_dataset["fides_key"]
    google_analytics_connection_config_without_secrets.name = fides_key
    google_analytics_connection_config_without_secrets.key = fides_key
    google_analytics_connection_config_without_secrets.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, google_analytics_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": google_analytics_connection_config_without_secrets.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)
