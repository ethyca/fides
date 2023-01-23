from typing import Any, Dict, Generator

import pydash
import pytest
from sqlalchemy.orm import Session
from sqlalchemy_utils.functions import drop_database

from fides.api.ctl.sql_models import Dataset as CtlDataset
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
from fides.lib.cryptography import cryptographic_util
from fides.lib.db import session
from tests.ops.test_helpers.db_utils import seed_postgres_data
from tests.ops.test_helpers.vault_client import get_secrets

from ..application_fixtures import load_dataset

secrets = get_secrets("doordash")


@pytest.fixture(scope="function")
def doordash_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "doordash.domain") or secrets["domain"],
        "developer_id": pydash.get(saas_config, "doordash.developer_id")
        or secrets["developer_id"],
        "key_id": pydash.get(saas_config, "doordash.key_id") or secrets["key_id"],
        "signing_secret": pydash.get(saas_config, "doordash.signing_secret")
        or secrets["signing_secret"],
        "doordash_delivery_id": {
            "dataset": "doordash_postgres",
            "field": "doordash_deliveries.delivery_id",
            "direction": "from",
        },
    }


@pytest.fixture(scope="function")
def doordash_identity_email(saas_config):
    return (
        pydash.get(saas_config, "doordash.identity_email") or secrets["identity_email"]
    )


@pytest.fixture(scope="session")
def doordash_erasure_identity_email():
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture
def doordash_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/doordash_config.yml",
        "<instance_fides_key>",
        "doordash_instance",
    )


@pytest.fixture
def doordash_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/doordash_dataset.yml",
        "<instance_fides_key>",
        "doordash_instance",
    )[0]


@pytest.fixture(scope="function")
def doordash_connection_config(
    db: session, doordash_config, doordash_secrets
) -> Generator:
    fides_key = doordash_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": doordash_secrets,
            "saas_config": doordash_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def doordash_dataset_config(
    db: Session,
    doordash_connection_config: ConnectionConfig,
    doordash_dataset: Dict[str, Any],
) -> Generator:
    fides_key = doordash_dataset["fides_key"]
    doordash_connection_config.name = fides_key
    doordash_connection_config.key = fides_key
    doordash_connection_config.save(db=db)
    ctl_dataset = CtlDataset.create_from_dataset_dict(db, doordash_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": doordash_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture()
def doordash_postgres_dataset() -> Dict[str, Any]:
    return {
        "fides_key": "doordash_postgres",
        "name": "Doordash Postgres",
        "description": "Lookup for Doordash delivery IDs",
        "collections": [
            {
                "name": "doordash_deliveries",
                "fields": [
                    {
                        "name": "email",
                        "data_categories": ["user.contact.email"],
                        "fidesops_meta": {"data_type": "string", "identity": "email"},
                    },
                    {
                        "name": "delivery_id",
                        "fidesops_meta": {"data_type": "string"},
                    },
                ],
            }
        ],
    }


@pytest.fixture
def doordash_postgres_dataset_config(
    connection_config: ConnectionConfig,
    doordash_postgres_dataset: Dict[str, Any],
    db: Session,
) -> Generator:
    fides_key = doordash_postgres_dataset["fides_key"]
    connection_config.name = fides_key
    connection_config.key = fides_key
    connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, doordash_postgres_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db)


@pytest.fixture(scope="function")
def doordash_postgres_db(postgres_integration_session):
    postgres_integration_session = seed_postgres_data(
        postgres_integration_session,
        "./tests/ops/fixtures/saas/external_datasets/doordash.sql",
    )
    yield postgres_integration_session
    drop_database(postgres_integration_session.bind.url)
