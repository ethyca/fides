from time import sleep
from typing import Any, Dict, Generator

import pydash
import pytest
import requests
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
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("gorgias")


@pytest.fixture(scope="session")
def gorgias_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "gorgias.domain") or secrets["domain"],
        "username": pydash.get(saas_config, "gorgias.username") or secrets["username"],
        "api_key": pydash.get(saas_config, "gorgias.api_key") or secrets["api_key"],
    }


@pytest.fixture(scope="session")
def gorgias_identity_email(saas_config):
    return (
        pydash.get(saas_config, "gorgias.identity_email") or secrets["identity_email"]
    )


@pytest.fixture(scope="function")
def gorgias_erasure_identity_email() -> str:
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture
def gorgias_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/gorgias_config.yml",
        "<instance_fides_key>",
        "gorgias_instance",
    )


@pytest.fixture
def gorgias_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/gorgias_dataset.yml",
        "<instance_fides_key>",
        "gorgias_instance",
    )[0]


@pytest.fixture(scope="function")
def gorgias_connection_config(
    db: Session, gorgias_config, gorgias_secrets
) -> Generator:
    fides_key = gorgias_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": gorgias_secrets,
            "saas_config": gorgias_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def gorgias_dataset_config(
    db: Session,
    gorgias_connection_config: ConnectionConfig,
    gorgias_dataset: Dict[str, Any],
) -> Generator:
    fides_key = gorgias_dataset["fides_key"]
    gorgias_connection_config.name = fides_key
    gorgias_connection_config.key = fides_key
    gorgias_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, gorgias_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": gorgias_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture(scope="function")
def gorgias_create_erasure_data(
    gorgias_connection_config: ConnectionConfig, gorgias_erasure_identity_email: str
) -> None:
    gorgias_secrets = gorgias_connection_config.secrets
    auth = gorgias_secrets["username"], gorgias_secrets["api_key"]
    base_url = f"https://{gorgias_secrets['domain']}"

    # user
    body = {
        "name": "Ethyca Test Erasure",
        "email": gorgias_erasure_identity_email,
    }

    users_response = requests.post(
        url=f"{base_url}/api/customers", auth=auth, json=body
    )
    user = users_response.json()
    user_id = user["id"]

    ticket_data = {
        "customer": {"id": user_id, "email": gorgias_erasure_identity_email},
        "messages": [
            {
                "sender": {"id": user_id, "email": gorgias_erasure_identity_email},
                "channel": "twitter-direct-message",
                "from_agent": "false",
                "via": "instagram-ad-comment",
            }
        ],
        "channel": "api",
        "status": "open",
        "subject": "Tested",
    }
    response = requests.post(url=f"{base_url}/api/tickets", auth=auth, json=ticket_data)
    ticket = response.json()
    sleep(60)
    yield ticket, user
