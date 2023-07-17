from typing import Any, Dict, Generator, cast

import pydash
import pytest
import requests
from requests import Response
from sqlalchemy.orm import Session

from fides.api.cryptography import cryptographic_util
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

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("adobe_sign")


@pytest.fixture(scope="session")
def adobe_sign_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "adobe_sign.domain") or secrets["domain"],
        "client_id": pydash.get(saas_config, "adobe_sign.client_id") or secrets["client_id"],
        "client_secret": pydash.get(saas_config, "adobe_sign.client_secret") or secrets["client_secret"],
        "redirect_uri": pydash.get(saas_config, "adobe_sign.redirect_uri") or secrets["redirect_uri"],
        "access_token": pydash.get(saas_config, "adobe_sign.access_token") or secrets["access_token"],
        "scope": pydash.get(saas_config, "adobe_sign.scope") or secrets["scope"]
        # add the rest of your secrets here
    }


@pytest.fixture(scope="session")
def adobe_sign_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "adobe_sign.identity_email") or secrets["identity_email"]
    )


@pytest.fixture(scope="function")
def adobe_sign_erasure_identity_email() -> str:
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture
def adobe_sign_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/adobe_sign_config.yml",
        "<instance_fides_key>",
        "adobe_signinstance",
    )


@pytest.fixture
def adobe_sign_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/adobe_sign_dataset.yml",
        "<instance_fides_key>",
        "adobe_sign_instance",
    )[0]


@pytest.fixture(scope="function")
def adobe_sign_connection_config(
    db: Session, adobe_sign_config, adobe_sign_secrets
) -> Generator:
    fides_key = adobe_sign_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": adobe_sign_secrets,
            "saas_config": adobe_sign_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def adobe_sign_dataset_config(
    db: Session,
    adobe_sign_connection_config: ConnectionConfig,
    adobe_sign_dataset: Dict[str, Any],
) -> Generator:
    fides_key = adobe_sign_dataset["fides_key"]
    adobe_sign_connection_config.name = fides_key
    adobe_sign_connection_config.key = fides_key
    adobe_sign_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, adobe_sign_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": adobe_sign_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)

@pytest.fixture
def adobe_sign_runner(
    db,
    cache,
    adobe_sign_secrets,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "adobe_sign",
        adobe_sign_secrets
    )