from time import sleep
from typing import Any, Dict, Generator

import pydash
import pytest
import requests
from sqlalchemy.orm import Session

from fides.api.ctl.sql_models import Dataset as CtlDataset
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


secrets = get_secrets("gorgias")


@pytest.fixture(scope="session")
def gorgias_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "gorgias.domain") or secrets["domain"],
        "user_name": pydash.get(saas_config, "gorgias.user_name") or secrets["user_name"],
        "api_key": pydash.get(saas_config, "gorgias.api_key") or secrets["api_key"],
    }


@pytest.fixture(scope="session")
def gorgias_identity_email(saas_config):
    return (
        pydash.get(
            saas_config, "gorgias.identity_email") or secrets["identity_email"]
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

    sleep(60)

    gorgias_secrets = gorgias_connection_config.secrets
    auth = gorgias_secrets["user_name"], gorgias_secrets["api_key"]
    base_url = f"https://{gorgias_secrets['domain']}"

    # customer
    body = {
        "email": gorgias_erasure_identity_email
    }

    customers_response = requests.post(
        
    url=f"{base_url}/api/customers", auth=auth, json=body)
    
    customer = customers_response.json()
   
    customer_id = customer["id"]

    # tickets

    # ticket_body = {
    #  "channel": "email",
    #  "created_datetime": "2019-07-05T14:42:00.384938",
    #  "customer": {
    #       "id": customer_id,
    #       "email": gorgias_erasure_identity_email
    #  },
    #  "external_id": "RETURN#4213",
    #  "from_agent": True,
    #  "language": "fr",
    #  "last_message_datetime": "2020-02-01T19:12:32.432197",
    #  "last_received_message_datetime": "2020-01-27T10:42:21.468912",
    #  "messages": [
    #       {
    #            "sender": {
    #                "id": customer_id,
    #                "email": gorgias_erasure_identity_email
    #             },
    #            "channel": "email",
    #            "from_agent": False,
    #            "via": "email"
    #       }
    #  ],
    #  "opened_datetime": "2019-07-05T15:22:46.472436",
    #  "spam": False,
    #  "status": "open",
    #  "subject": "Can I get a refund?",
    #  "tags": [
    #       {
    #            "name": "urgent"
    #       }
    #  ],
    #  "updated_datetime": "2020-01-27T10:42:21.932637",
    #  "via": "email"
    # }
    
    ticket_body ={
        "customer": {
            "id": customer_id,
            "email": gorgias_erasure_identity_email
            },
        "messages": [
            {
                "sender": {
                    "id": customer_id,
                    "email": gorgias_erasure_identity_email
                    },
                "channel": "twitter-direct-message",
                "from_agent": "true",
                "via": "instagram-ad-comment"
            }
        ],
        "channel": "api",
        "status": "open",
        "subject": "Tested"

    } 
    
    ticket_response = requests.post(
        url=f"{base_url}/api/tickets", auth=auth, json=ticket_body)

    ticket = ticket_response.json()
    
    yield customer
    

