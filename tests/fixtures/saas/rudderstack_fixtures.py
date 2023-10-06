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

secrets = get_secrets("rudderstack")


@pytest.fixture(scope="session")
def rudderstack_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "rudderstack.domain") or secrets["domain"],
        "token": pydash.get(saas_config, "rudderstack.token") or secrets["token"],
    }


@pytest.fixture(scope="session")
def rudderstack_identity_email(saas_config):
    return "customer-1@example.com"


@pytest.fixture
def rudderstack_external_references(saas_config) -> Dict[str, Any]:
    return {
        "user_id": pydash.get(saas_config, "rudderstack.user_id") or secrets["user_id"]
    }


@pytest.fixture
def rudderstack_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/rudderstack_config.yml",
        "<instance_fides_key>",
        "rudderstack_instance",
    )


@pytest.fixture
def rudderstack_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/rudderstack_dataset.yml",
        "<instance_fides_key>",
        "rudderstack_instance",
    )[0]


@pytest.fixture(scope="function")
def rudderstack_connection_config(
    db: Session, rudderstack_config, rudderstack_secrets
) -> Generator:
    fides_key = rudderstack_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": rudderstack_secrets,
            "saas_config": rudderstack_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def rudderstack_dataset_config(
    db: Session,
    rudderstack_connection_config: ConnectionConfig,
    rudderstack_dataset: Dict[str, Any],
) -> Generator:
    fides_key = rudderstack_dataset["fides_key"]
    rudderstack_connection_config.name = fides_key
    rudderstack_connection_config.key = fides_key
    rudderstack_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, rudderstack_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": rudderstack_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture(scope="function")
def reset_rudderstack_data(
    rudderstack_connection_config,
    rudderstack_identity_email,
    rudderstack_external_references,
) -> Generator:
    """
    Adds regulation to the RudderStack Allowlist
    """
    connector = SaaSConnector(rudderstack_connection_config)
    connector.set_saas_request_state(
        SaaSRequest(path="test_path", method=HTTPMethod.GET)
    )  # dummy request as connector requires it
    request: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.POST,
        path="/v2/regulations",
        body=json.dumps(
            {
                "regulationType": "suppress",
                # "destinationIds": [
                #     "27OeyCriZ4vGFiOFPihSMgr0Nt1"
                # ],
                "users": [{"userId": "543256", "email": "ethyca.email@email.com"}],
            }
        ),
    )
    response = connector.create_client().send(request)
    body = response.json()
    assert (
        body["email"] == rudderstack_identity_email
    ), "Identity has been added to allowlist"


@pytest.fixture(scope="function")
def rudderstack_connection_config_no_secrets(
    db: session, rudderstack_config
) -> Generator:
    """This test connector cannot not be used to make live requests"""
    fides_key = rudderstack_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": {"api_key": "test"},
            "saas_config": rudderstack_config,
        },
    )
    yield connection_config
    connection_config.delete(db)
