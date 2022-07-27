import json
from typing import Any, Dict, Generator

import pydash
import pytest
from fideslib.core.config import load_toml
from fideslib.db import session
from sqlalchemy.orm import Session

from fidesops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fidesops.models.datasetconfig import DatasetConfig
from fidesops.schemas.saas.shared_schemas import HTTPMethod, SaaSRequestParams
from fidesops.service.connectors.saas_connector import SaaSConnector
from fidesops.util.saas_util import load_config
from tests.ops.fixtures.application_fixtures import load_dataset
from tests.ops.test_helpers.vault_client import get_secrets

saas_config = load_toml(["saas_config.toml"])
secrets = get_secrets("mailchimp")


@pytest.fixture(scope="session")
def mailchimp_secrets():
    return {
        "domain": pydash.get(saas_config, "mailchimp.domain") or secrets["domain"],
        "username": pydash.get(saas_config, "mailchimp.username")
        or secrets["username"],
        "api_key": pydash.get(saas_config, "mailchimp.api_key") or secrets["api_key"],
    }


@pytest.fixture(scope="session")
def mailchimp_identity_email():
    return (
        pydash.get(saas_config, "mailchimp.identity_email") or secrets["identity_email"]
    )


@pytest.fixture
def mailchimp_config() -> Dict[str, Any]:
    return load_config("data/saas/config/mailchimp_config.yml")


@pytest.fixture
def mailchimp_dataset() -> Dict[str, Any]:
    return load_dataset("data/saas/dataset/mailchimp_dataset.yml")[0]


@pytest.fixture(scope="function")
def mailchimp_connection_config(
    db: session, mailchimp_config, mailchimp_secrets
) -> Generator:
    fides_key = mailchimp_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": mailchimp_secrets,
            "saas_config": mailchimp_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def mailchimp_dataset_config(
    db: Session,
    mailchimp_connection_config: ConnectionConfig,
    mailchimp_dataset: Dict[str, Any],
) -> Generator:
    fides_key = mailchimp_dataset["fides_key"]
    mailchimp_connection_config.name = fides_key
    mailchimp_connection_config.key = fides_key
    mailchimp_connection_config.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": mailchimp_connection_config.id,
            "fides_key": fides_key,
            "dataset": mailchimp_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)


@pytest.fixture(scope="function")
def reset_mailchimp_data(
    mailchimp_connection_config, mailchimp_identity_email
) -> Generator:
    """
    Gets the current value of the resource and restores it after the test is complete.
    Used for erasure tests.
    """
    connector = SaaSConnector(mailchimp_connection_config)
    request: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.GET,
        path="/3.0/search-members",
        query_params={"query": mailchimp_identity_email},
    )
    response = connector.create_client().send(request)
    body = response.json()
    member = body["exact_matches"]["members"][0]
    yield member
    request: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.PUT,
        headers={"Content-Type": "application/json"},
        path=f'/3.0/lists/{member["list_id"]}/members/{member["id"]}',
        body=json.dumps(member),
    )
    connector.create_client().send(request)
