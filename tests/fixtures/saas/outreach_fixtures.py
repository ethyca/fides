import os
from typing import Any, Dict, Generator

import pydash
import pytest
import requests
from fideslib.core.config import load_toml
from fideslib.cryptography import cryptographic_util
from fideslib.db import session
from sqlalchemy.orm import Session

from fidesops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fidesops.models.datasetconfig import DatasetConfig
from fidesops.util.saas_util import load_config
from tests.fixtures.application_fixtures import load_dataset

saas_config = load_toml(["saas_config.toml"])


@pytest.fixture(scope="function")
def outreach_secrets():
    return {
        "domain": pydash.get(saas_config, "outreach.domain")
        or os.environ.get("OUTREACH_DOMAIN"),
        "requester_email": pydash.get(saas_config, "outreach.requester_email")
        or os.environ.get("OUTREACH_REQUESTER_EMAIL"),
        "client_id": pydash.get(saas_config, "outreach.client_id")
        or os.environ.get("OUTREACH_CLIENT_ID"),
        "client_secret": pydash.get(saas_config, "outreach.client_secret")
        or os.environ.get("OUTREACH_CLIENT_SECRET"),
        "redirect_uri": pydash.get(saas_config, "outreach.redirect_uri")
        or os.environ.get("OUTREACH_REDIRECT_URI"),
        "page_size": pydash.get(saas_config, "outreach.page_size")
        or os.environ.get("OUTREACH_PAGE_SIZE"),
    }


@pytest.fixture(scope="session")
def outreach_identity_email():
    return pydash.get(saas_config, "outreach.identity_email") or os.environ.get(
        "OUTREACH_IDENTITY_EMAIL"
    )


@pytest.fixture(scope="function")
def outreach_erasure_identity_email() -> str:
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture
def outreach_config() -> Dict[str, Any]:
    return load_config("data/saas/config/outreach_config.yml")


@pytest.fixture
def outreach_dataset() -> Dict[str, Any]:
    return load_dataset("data/saas/dataset/outreach_dataset.yml")[0]


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
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": outreach_connection_config.id,
            "fides_key": fides_key,
            "dataset": outreach_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)


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
