from typing import Any, Dict, Generator

import pydash
import pytest
from fideslib.cryptography import cryptographic_util
from fideslib.db import session
from sqlalchemy.orm import Session

from fidesops.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fidesops.ops.models.datasetconfig import DatasetConfig
from fidesops.ops.util.saas_util import (
    load_config_with_replacement,
    load_dataset_with_replacement,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("shopify")


@pytest.fixture(scope="function")
def shopify_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "shopify.domain") or secrets["domain"],
        "access_token": pydash.get(saas_config, "shopify.access_token")
        or secrets["access_token"],
    }


@pytest.fixture(scope="function")
def shopify_identity_email(saas_config):
    return (
        pydash.get(saas_config, "shopify.identity_email") or secrets["identity_email"]
    )


@pytest.fixture(scope="session")
def shopify_erasure_identity_email():
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture
def shopify_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/shopify_config.yml",
        "<instance_fides_key>",
        "shopify_instance",
    )


@pytest.fixture
def shopify_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/shopify_dataset.yml",
        "<instance_fides_key>",
        "shopify_instance",
    )[0]


@pytest.fixture(scope="function")
def shopify_connection_config(
    db: session, shopify_config, shopify_secrets
) -> Generator:
    fides_key = shopify_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": shopify_secrets,
            "saas_config": shopify_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def shopify_dataset_config(
    db: Session,
    shopify_connection_config: ConnectionConfig,
    shopify_dataset: Dict[str, Any],
) -> Generator:
    fides_key = shopify_dataset["fides_key"]
    shopify_connection_config.name = fides_key
    shopify_connection_config.key = fides_key
    shopify_connection_config.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": shopify_connection_config.id,
            "fides_key": fides_key,
            "dataset": shopify_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)
