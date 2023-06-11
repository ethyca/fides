from typing import Any, Dict, Generator

import pydash
import pytest
import requests
from sqlalchemy.orm import Session

from fides.api.cryptography import cryptographic_util
from fides.api.db import session
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
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("outreach")


@pytest.fixture(scope="session")
def outreach_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "outreach.domain") or secrets["domain"],
        "requester_email": pydash.get(saas_config, "outreach.requester_email")
        or secrets["requester_email"],
        "client_id": pydash.get(saas_config, "outreach.client_id")
        or secrets["client_id"],
        "client_secret": pydash.get(saas_config, "outreach.client_secret")
        or secrets["client_secret"],
        "redirect_uri": pydash.get(saas_config, "outreach.redirect_uri")
        or secrets["redirect_uri"],
        "page_size": pydash.get(saas_config, "outreach.page_size")
        or secrets["page_size"],
    }


@pytest.fixture(scope="session")
def outreach_identity_email(saas_config):
    return (
        pydash.get(saas_config, "outreach.identity_email") or secrets["identity_email"]
    )


@pytest.fixture(scope="function")
def outreach_erasure_identity_email() -> str:
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture
def outreach_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/outreach_config.yml",
        "<instance_fides_key>",
        "outreach_instance",
    )


@pytest.fixture
def outreach_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/outreach_dataset.yml",
        "<instance_fides_key>",
        "outreach_dataset",
    )[0]


@pytest.fixture(scope="function")
def outreach_connection_config(
    db: session, outreach_config, outreach_secrets
) -> Generator:
    fides_key = outreach_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": outreach_secrets,
            "saas_config": outreach_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def outreach_dataset_config(
    db: Session,
    outreach_connection_config: ConnectionConfig,
    outreach_dataset: Dict[str, Any],
) -> Generator:
    fides_key = outreach_dataset["fides_key"]
    outreach_connection_config.name = fides_key
    outreach_connection_config.key = fides_key
    outreach_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, outreach_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": outreach_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture(scope="function")
def outreach_create_erasure_data(
    outreach_connection_config: ConnectionConfig, outreach_erasure_identity_email: str
) -> None:
    outreach_secrets = outreach_connection_config.secrets
    base_url = f"https://{outreach_secrets['domain']}"
    headers = {
        "Authorization": f"Bearer {outreach_secrets['access_token']}",
    }

    # prospect
    prospect_data = {
        "data": {
            "type": "prospect",
            "attributes": {
                "emails": [outreach_erasure_identity_email],
                "firstName": "Ethyca",
                "lastName": "RTF",
            },
        }
    }

    response = requests.post(
        url=f"{base_url}/api/v2/prospects",
        headers=headers,
        json=prospect_data,
    )
    assert response.ok

    # recipient
    recipient_data = {
        "data": {
            "type": "recipient",
            "attributes": {
                "recipientType": "to",
                "value": outreach_erasure_identity_email,
            },
        }
    }

    response = requests.post(
        url=f"{base_url}/api/v2/recipients",
        headers=headers,
        json=recipient_data,
    )
    assert response.ok
