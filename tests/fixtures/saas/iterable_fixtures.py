from typing import Any, Dict, Generator

import pydash
import pytest

from fides.api.db import session
from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.util.saas_util import load_config_with_replacement
from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("iterable")


@pytest.fixture(scope="session")
def iterable_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "iterable.domain") or secrets["domain"],
        "api_key": pydash.get(saas_config, "iterable.api_key") or secrets["api_key"],
    }


@pytest.fixture(scope="session")
def iterable_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "iterable.identity_email") or secrets["identity_email"]
    )


@pytest.fixture
def iterable_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def iterable_runner(
    db,
    cache,
    iterable_secrets,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "iterable",
        iterable_secrets,
    )


@pytest.fixture
def iterable_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/iterable_config.yml",
        "<instance_fides_key>",
        "iterable_instance",
    )


@pytest.fixture(scope="function")
def iterable_connection_config_no_secrets(
    db: session,
    iterable_config,
) -> Generator:
    """This test connector cannot not be used to make live requests"""
    fides_key = iterable_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": {"domain": "test.api.com", "api_key": "test"},
            "saas_config": iterable_config,
        },
    )
    yield connection_config
    connection_config.delete(db)
