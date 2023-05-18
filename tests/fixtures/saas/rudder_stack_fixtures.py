import json
from typing import Any, Dict, Generator

import pydash
import pytest
from sqlalchemy.orm import Session

from fides.api.ctl.sql_models import Dataset as CtlDataset
from fides.api.ops.db import session
from fides.api.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.ops.models.datasetconfig import DatasetConfig
from fides.api.ops.schemas.saas.saas_config import SaaSRequest
from fides.api.ops.schemas.saas.shared_schemas import HTTPMethod, SaaSRequestParams
from fides.api.ops.service.connectors import SaaSConnector
from fides.api.ops.util.saas_util import (
    load_config_with_replacement,
    load_dataset_with_replacement,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("rudder_stack")


@pytest.fixture(scope="session")
def rudder_stack_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "rudder_stack.domain")
        or secrets["domain"],
        "token": pydash.get(saas_config, "rudder_stack.token")
        or secrets["token"],
    }


@pytest.fixture(scope="session")
def rudder_stack_identity_email(saas_config):
    return "customer-1@example.com"

@pytest.fixture
def rudder_stack_external_references(saas_config) -> Dict[str, Any]:
    return {
        "user_id": pydash.get(saas_config, "rudder_stack.user_id")
        or secrets["user_id"]
    }


@pytest.fixture
def rudder_stack_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/rudder_stack_config.yml",
        "<instance_fides_key>",
        "rudder_stack_instance",
    )


@pytest.fixture
def rudder_stack_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/rudder_stack_dataset.yml",
        "<instance_fides_key>",
        "rudder_stack_instance",
    )[0]


@pytest.fixture(scope="function")
def rudder_stack_connection_config(
    db: session, rudder_stack_config, rudder_stack_secrets
) -> Generator:
    fides_key = rudder_stack_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": rudder_stack_secrets,
            "saas_config": rudder_stack_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def rudder_stack_dataset_config(
    db: Session,
    rudder_stack_connection_config: ConnectionConfig,
    rudder_stack_dataset: Dict[str, Any],
) -> Generator:
    fides_key = rudder_stack_dataset["fides_key"]
    rudder_stack_connection_config.name = fides_key
    rudder_stack_connection_config.key = fides_key
    rudder_stack_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(
        db, rudder_stack_dataset
    )

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": rudder_stack_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture(scope="function")
def reset_rudder_stack_data(
    rudder_stack_connection_config, rudder_stack_identity_email, rudder_stack_external_references
) -> Generator:
    """
    Adds regulation to the rudder stack Allowlist
    """
    connector = SaaSConnector(rudder_stack_connection_config)
    connector.set_saas_request_state(
        SaaSRequest(path="test_path", method=HTTPMethod.GET)
    )  # dummy request as connector requires it
    request: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.POST,
        path="/v2/regulations",
        body=json.dumps({
            "regulationType": "suppress",
            "destinationIds": [
                "27OeyCriZ4vGFiOFPihSMgr0Nt1"
            ],
            "users": [
                {
                    "userId": "12345",
                    "phone": "+123456789",
                    "email": rudder_stack_identity_email
                }
            ]
        }),
    )
    response = connector.create_client().send(request)
    body = response.json()
    assert (
        body["email"] == rudder_stack_identity_email
    ), "Identity has been added to allowlist"


@pytest.fixture(scope="function")
def rudder_stack_connection_config_no_secrets(
    db: session, rudder_stack_config
) -> Generator:
    """This test connector cannot not be used to make live requests"""
    fides_key = rudder_stack_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": {"api_key": "test"},
            "saas_config": rudder_stack_config,
        },
    )
    yield connection_config
    connection_config.delete(db)
