from time import sleep
from typing import Any, Dict, Generator

import pydash
import pytest
import requests
from sqlalchemy.orm import Session

from fides.api.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.ops.models.datasetconfig import DatasetConfig
from fides.api.ops.util.saas_util import (
    load_config_with_replacement,
    load_dataset_with_replacement,
)
from fides.lib.cryptography import cryptographic_util
from tests.ops.test_helpers.vault_client import get_secrets
from tests.ops.test_helpers.saas_test_utils import poll_for_existence

secrets = get_secrets("jira")


@pytest.fixture(scope="session")
def jira_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "jira.domain") or secrets["domain"],
        "api_key": pydash.get(saas_config, "jira.api_key") or secrets["api_key"],
    }


@pytest.fixture(scope="session")
def jira_identity_email(saas_config):
    return (
        pydash.get(saas_config, "jira.identity_email") or secrets["identity_email"]
    )

@pytest.fixture(scope="session")
def jira_user_name(saas_config):
    return (
        pydash.get(saas_config, "jira.user_name") or secrets["user_name"]
    )


@pytest.fixture(scope="function")
def jira_erasure_identity_email() -> str:
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture
def jira_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/jira_config.yml",
        "<instance_fides_key>",
        "jira_instance",
    )


@pytest.fixture
def jira_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/jira_dataset.yml",
        "<instance_fides_key>",
        "jira_instance",
    )[0]


@pytest.fixture(scope="function")
def jira_connection_config(
    db: Session, jira_config, jira_secrets
) -> Generator:
    fides_key = jira_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": jira_secrets,
            "saas_config": jira_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def jira_dataset_config(
    db: Session,
    jira_connection_config: ConnectionConfig,
    jira_dataset: Dict[str, Any],
) -> Generator:
    fides_key = jira_dataset["fides_key"]
    jira_connection_config.name = fides_key
    jira_connection_config.key = fides_key
    jira_connection_config.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": jira_connection_config.id,
            "fides_key": fides_key,
            "dataset": jira_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)


@pytest.fixture(scope="function")
def jira_create_erasure_data(
    jira_connection_config: ConnectionConfig, jira_erasure_identity_email: str
) -> None:

    # sleep(60)

    jira_secrets = jira_connection_config.secrets    
    base_url = f"https://{jira_secrets['domain']}"
    headers = {        
        "Authorization": f"Basic {jira_secrets['api_key']}",
    }


    # user
    body = {
            "name": "Ethyca Test Erasure",
            "emailAddress": jira_erasure_identity_email,
    }

    users_response = requests.post(url=f"{base_url}/rest/api/3/user", headers=headers, json=body)
    user = users_response.json()
    # sleep(30)

    error_message = f"customer with email {jira_erasure_identity_email} could not be added to Jira"
    user_data = poll_for_existence(
        customer_exists,
        (jira_erasure_identity_email, jira_secrets),
        error_message=error_message,
        # retries=20,
        # interval=5,
    )

    yield user

def customer_exists(jira_erasure_identity_email: str, jira_secrets):
    """
    Confirm whether customer exists by calling customer search by email api and comparing resulting firstname str.
    Returns customer ID if it exists, returns None if it does not.
    """
    base_url = f"https://{jira_secrets['domain']}"
    headers = {        
        "Authorization": f"Basic {jira_secrets['api_key']}",
    }

    customer_response = requests.get(
        url=f"{base_url}/rest/api/3/user/search",
        headers=headers,
        params={"query": jira_erasure_identity_email},
    )

    # we expect 404 if customer doesn't exist
    if 200 != customer_response.status_code:
        return None
    if len(customer_response.json()) == 0:
        return None

    return customer_response.json()
