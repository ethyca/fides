import logging
from typing import Any, Dict, Generator

import pytest
from fideslib.core.config import load_toml
from fidesops.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fidesops.ops.models.datasetconfig import DatasetConfig
from fidesops.ops.schemas.saas.strategy_configuration import (
    OAuth2AuthenticationConfiguration,
)
from fidesops.ops.util.logger import NotPii
from fidesops.ops.util.saas_util import load_config
from sqlalchemy.orm import Session

from tests.ops.fixtures.application_fixtures import load_dataset

logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def saas_example_secrets():
    return {
        "domain": "domain",
        "username": "username",
        "api_key": "api_key",
        "api_version": "2.0",
        "page_size": "page_size",
    }


@pytest.fixture
def saas_example_config() -> Dict:
    return load_config("data/saas/config/saas_example_config.yml")


@pytest.fixture
def saas_example_dataset() -> Dict:
    return load_dataset("data/saas/dataset/saas_example_dataset.yml")[0]


@pytest.fixture(scope="function")
def saas_example_connection_config(
    db: Session,
    saas_example_config: Dict[str, Any],
    saas_example_secrets: Dict[str, Any],
) -> Generator:
    fides_key = saas_example_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": saas_example_secrets,
            "saas_config": saas_example_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def saas_example_dataset_config(
    db: Session,
    saas_example_connection_config: ConnectionConfig,
    saas_example_dataset: Dict,
) -> Generator:
    fides_key = saas_example_dataset["fides_key"]
    saas_example_connection_config.name = fides_key
    saas_example_connection_config.key = fides_key
    saas_example_connection_config.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": saas_example_connection_config.id,
            "fides_key": fides_key,
            "dataset": saas_example_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)


@pytest.fixture(scope="function")
def saas_example_connection_config_without_saas_config(
    db: Session, saas_example_secrets
) -> Generator:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": "connection_config_without_saas_config",
            "name": "connection_config_without_saas_config",
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.read,
            "secrets": saas_example_secrets,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def saas_example_connection_config_with_invalid_saas_config(
    db: Session,
    saas_example_config: Dict[str, Any],
    saas_example_secrets: Dict[str, Any],
) -> Generator:
    invalid_saas_config = saas_example_config.copy()
    invalid_saas_config["endpoints"][0]["requests"]["read"]["param_values"].pop()
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": "connection_config_with_invalid_saas_config",
            "name": "connection_config_with_invalid_saas_config",
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.read,
            "secrets": saas_example_secrets,
            "saas_config": invalid_saas_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def oauth2_configuration() -> OAuth2AuthenticationConfiguration:
    return {
        "authorization_request": {
            "method": "GET",
            "path": "/auth/authorize",
            "query_params": [
                {"name": "client_id", "value": "<client_id>"},
                {"name": "redirect_uri", "value": "<redirect_uri>"},
                {"name": "response_type", "value": "code"},
                {
                    "name": "scope",
                    "value": "admin.read admin.write",
                },
                {"name": "state", "value": "<state>"},
            ],
        },
        "token_request": {
            "method": "POST",
            "path": "/oauth/token",
            "headers": [
                {
                    "name": "Content-Type",
                    "value": "application/x-www-form-urlencoded",
                }
            ],
            "query_params": [
                {"name": "client_id", "value": "<client_id>"},
                {"name": "client_secret", "value": "<client_secret>"},
                {"name": "grant_type", "value": "authorization_code"},
                {"name": "code", "value": "<code>"},
                {"name": "redirect_uri", "value": "<redirect_uri>"},
            ],
        },
        "refresh_request": {
            "method": "POST",
            "path": "/oauth/token",
            "headers": [
                {
                    "name": "Content-Type",
                    "value": "application/x-www-form-urlencoded",
                }
            ],
            "query_params": [
                {"name": "client_id", "value": "<client_id>"},
                {"name": "client_secret", "value": "<client_secret>"},
                {"name": "redirect_uri", "value": "<redirect_uri>"},
                {"name": "grant_type", "value": "refresh_token"},
                {"name": "refresh_token", "value": "<refresh_token>"},
            ],
        },
    }


@pytest.fixture(scope="function")
def oauth2_connection_config(db: Session, oauth2_configuration) -> Generator:
    secrets = {
        "domain": "localhost",
        "client_id": "client",
        "client_secret": "secret",
        "redirect_uri": "https://localhost/callback",
        "access_token": "access",
        "refresh_token": "refresh",
    }
    saas_config = {
        "fides_key": "oauth2_connector",
        "name": "OAuth2 Connector",
        "type": "custom",
        "description": "Generic OAuth2 connector for testing",
        "version": "0.0.1",
        "connector_params": [{"name": item} for item in secrets.keys()],
        "client_config": {
            "protocol": "https",
            "host": secrets["domain"],
            "authentication": {
                "strategy": "oauth2",
                "configuration": oauth2_configuration,
            },
        },
        "endpoints": [],
        "test_request": {"method": "GET", "path": "/test"},
    }

    fides_key = saas_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": secrets,
            "saas_config": saas_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="session")
def saas_config() -> Dict[str, Any]:
    saas_config: Dict[str, Any] = {}
    try:
        saas_config: Dict[str, Any] = load_toml(["saas_config.toml"])
    except FileNotFoundError as e:
        logger.warning("saas_config.toml could not be loaded: %s", NotPii(e))
    return saas_config
