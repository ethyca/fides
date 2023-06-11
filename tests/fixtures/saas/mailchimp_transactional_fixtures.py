import json
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
from fides.api.schemas.saas.saas_config import SaaSRequest
from fides.api.schemas.saas.shared_schemas import HTTPMethod, SaaSRequestParams
from fides.api.service.connectors import SaaSConnector
from fides.api.util.saas_util import (
    load_config_with_replacement,
    load_dataset_with_replacement,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("mailchimp_transactional")


@pytest.fixture(scope="session")
def mailchimp_transactional_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "mailchimp_transactional.domain")
        or secrets["domain"],
        "api_key": pydash.get(saas_config, "mailchimp_transactional.api_key")
        or secrets["api_key"],
    }


@pytest.fixture(scope="session")
def mailchimp_transactional_identity_email(saas_config):
    return "customer-1@example.com"


@pytest.fixture
def mailchimp_transactional_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/mailchimp_transactional_config.yml",
        "<instance_fides_key>",
        "mailchimp_transactional_instance",
    )


@pytest.fixture
def mailchimp_transactional_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/mailchimp_transactional_dataset.yml",
        "<instance_fides_key>",
        "mailchimp_transactional_instance",
    )[0]


@pytest.fixture(scope="function")
def mailchimp_transactional_connection_config(
    db: session, mailchimp_transactional_config, mailchimp_transactional_secrets
) -> Generator:
    fides_key = mailchimp_transactional_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": mailchimp_transactional_secrets,
            "saas_config": mailchimp_transactional_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def mailchimp_transactional_dataset_config(
    db: Session,
    mailchimp_transactional_connection_config: ConnectionConfig,
    mailchimp_transactional_dataset: Dict[str, Any],
) -> Generator:
    fides_key = mailchimp_transactional_dataset["fides_key"]
    mailchimp_transactional_connection_config.name = fides_key
    mailchimp_transactional_connection_config.key = fides_key
    mailchimp_transactional_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(
        db, mailchimp_transactional_dataset
    )

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": mailchimp_transactional_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture(scope="function")
def reset_mailchimp_transactional_data(
    mailchimp_transactional_connection_config, mailchimp_transactional_identity_email
) -> Generator:
    """
    Adds user to the Mailchimp Transactional Allowlist
    """
    connector = SaaSConnector(mailchimp_transactional_connection_config)
    connector.set_saas_request_state(
        SaaSRequest(path="test_path", method=HTTPMethod.GET)
    )  # dummy request as connector requires it
    request: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.POST,
        path="/allowlists/add",
        body=json.dumps({"email": mailchimp_transactional_identity_email}),
    )
    response = connector.create_client().send(request)
    body = response.json()
    assert (
        body["email"] == mailchimp_transactional_identity_email
    ), "Identity has been added to allowlist"


@pytest.fixture(scope="function")
def mailchimp_transactional_connection_config_no_secrets(
    db: session, mailchimp_transactional_config
) -> Generator:
    """This test connector cannot not be used to make live requests"""
    fides_key = mailchimp_transactional_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": {"api_key": "test"},
            "saas_config": mailchimp_transactional_config,
        },
    )
    yield connection_config
    connection_config.delete(db)
