from typing import Any, Dict, Generator

import pydash
import pytest
from fideslib.cryptography import cryptographic_util
from fideslib.db import session
from sqlalchemy.orm import Session
from sqlalchemy_utils.functions import drop_database

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
from tests.ops.test_helpers.db_utils import seed_postgres_data
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("twilio")


@pytest.fixture(scope="function")
def twilio_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "twilio.domain") or secrets["domain"],
        "account_id": pydash.get(saas_config, "twilio.account_id")
        or secrets["account_id"],
        "password": pydash.get(saas_config, "twilio.password") or secrets["password"],
        "twilio_user_id": {
            "dataset": "twilio_postgres",
            "field": "twilio_users.twilio_user_id",
            "direction": "from",
        },
    }


@pytest.fixture(scope="function")
def twilio_identity_email(saas_config):
    return pydash.get(saas_config, "twilio.identity_email") or secrets["identity_email"]


@pytest.fixture(scope="session")
def twilio_erasure_identity_email():
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture
def twilio_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/twilio_config.yml", "<instance_fides_key>", "twilio_instance"
    )


@pytest.fixture
def twilio_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/twilio_dataset.yml",
        "<instance_fides_key>",
        "twilio_instance",
    )[0]


@pytest.fixture(scope="function")
def twilio_connection_config(db: session, twilio_config, twilio_secrets) -> Generator:
    fides_key = twilio_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": twilio_secrets,
            "saas_config": twilio_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def twilio_dataset_config(
    db: Session,
    twilio_connection_config: ConnectionConfig,
    twilio_dataset: Dict[str, Any],
) -> Generator:
    fides_key = twilio_dataset["fides_key"]
    twilio_connection_config.name = fides_key
    twilio_connection_config.key = fides_key
    twilio_connection_config.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": twilio_connection_config.id,
            "fides_key": fides_key,
            "dataset": twilio_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)


@pytest.fixture()
def twilio_postgres_dataset() -> Dict[str, Any]:
    return {
        "fides_key": "twilio_postgres",
        "name": "Twilio Postgres",
        "description": "Lookup for Twilio User IDs",
        "collections": [
            {
                "name": "twilio_users",
                "fields": [
                    {
                        "name": "email",
                        "data_categories": ["user.contact.email"],
                        "fidesops_meta": {"data_type": "string", "identity": "email"},
                    },
                    {
                        "name": "twilio_user_id",
                        "fidesops_meta": {"data_type": "string"},
                    },
                ],
            }
        ],
    }


@pytest.fixture
def twilio_postgres_dataset_config(
    connection_config: ConnectionConfig,
    twilio_postgres_dataset: Dict[str, Any],
    db: Session,
) -> Generator:
    fides_key = twilio_postgres_dataset["fides_key"]
    connection_config.name = fides_key
    connection_config.key = fides_key
    connection_config.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": fides_key,
            "dataset": twilio_postgres_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)


@pytest.fixture(scope="function")
def twilio_postgres_db(postgres_integration_session):
    postgres_integration_session = seed_postgres_data(
        postgres_integration_session,
        "./tests/ops/fixtures/saas/external_datasets/twilio.sql",
    )
    yield postgres_integration_session
    drop_database(postgres_integration_session.bind.url)
