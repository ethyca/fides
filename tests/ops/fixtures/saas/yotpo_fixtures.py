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

secrets = get_secrets("yotpo")


@pytest.fixture(scope="session")
def yotpo_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "yotpo.domain") or secrets["domain"],
        "app_key": pydash.get(saas_config, "yotpo.app_key") or secrets["app_key"],
        "secret_key": pydash.get(saas_config, "yotpo.secret_key") or secrets["secret_key"],
        "external": pydash.get(saas_config, "yotpo.external") or secrets["external"],    
        "x_api_key": pydash.get(saas_config, "yotpo.x_api_key") or secrets["x_api_key"],
        "x_guid": pydash.get(saas_config, "yotpo.x_guid") or secrets["x_guid"],
        "another_domain": pydash.get(saas_config, "yotpo.another_domain") or secrets["another_domain"],    
    }


@pytest.fixture(scope="session")
def yotpo_identity_email(saas_config):
    return (
        pydash.get(saas_config, "yotpo.identity_email") or secrets["identity_email"]
    )

@pytest.fixture(scope="session")
def yotpo_app_key(saas_config):
    return (
        pydash.get(saas_config, "yotpo.app_key") or secrets["app_key"]
    )

@pytest.fixture(scope="session")
def yotpo_secret_key(saas_config):
    return (
        pydash.get(saas_config, "yotpo.secret_key") or secrets["secret_key"]
    )


@pytest.fixture(scope="function")
def yotpo_erasure_identity_email() -> str:
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture(scope="function")
def yotpo_random_external_id() -> str:
    return f"{cryptographic_util.generate_secure_random_string(13)}"


@pytest.fixture
def yotpo_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/yotpo_config.yml",
        "<instance_fides_key>",
        "yotpo_instance",
    )


@pytest.fixture
def yotpo_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/yotpo_dataset.yml",
        "<instance_fides_key>",
        "yotpo_instance",
    )[0]


@pytest.fixture(scope="function")
def yotpo_connection_config(
    db: Session, yotpo_config, yotpo_secrets
) -> Generator:
    fides_key = yotpo_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": yotpo_secrets,
            "saas_config": yotpo_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def yotpo_dataset_config(
    db: Session,
    yotpo_connection_config: ConnectionConfig,
    yotpo_dataset: Dict[str, Any],
) -> Generator:
    fides_key = yotpo_dataset["fides_key"]
    yotpo_connection_config.name = fides_key
    yotpo_connection_config.key = fides_key
    yotpo_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, yotpo_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": yotpo_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture(scope="function")
def yotpo_create_erasure_data(
    yotpo_connection_config: ConnectionConfig, yotpo_erasure_identity_email: str, yotpo_create_access_token: str,yotpo_random_external_id: str
) -> None:

    # sleep(10)

    yotpo_secrets = yotpo_connection_config.secrets    
    base_url = f"https://{yotpo_secrets['domain']}"
    headers = {        
        "X-Yotpo-Token": yotpo_create_access_token,
    }

    # user
    body = {
        "customer": {
            "external_id": yotpo_random_external_id,
            "email": yotpo_erasure_identity_email,
        }
    }

    users_response = requests.patch(url=f"{base_url}/core/v3/stores/{yotpo_secrets['app_key']}/customers", headers=headers, json=body)    
    # sleep(60)
    error_message = f"customer with email {yotpo_erasure_identity_email} could not be added to Yotpo"
    user_data = poll_for_existence(
        customer_exists,
        (yotpo_random_external_id, yotpo_secrets, yotpo_create_access_token),
        retries=20,
        interval=8,
        error_message=error_message,
    ) 

    #update customer name   

    body = {
        "customer": {
            "external_id": yotpo_random_external_id,
            "email": yotpo_erasure_identity_email,
            "first_name":"test_data"
        }
    }

    # users_update_response = requests.patch(url=f"{base_url}/core/v3/stores/{yotpo_secrets['app_key']}/customers", headers=headers, json=body) 


    yield users_response.ok

@pytest.fixture(scope="function")
def yotpo_create_loyalty_data(
    yotpo_connection_config: ConnectionConfig, yotpo_erasure_identity_email: str
) -> None:

    # sleep(10)

    yotpo_secrets = yotpo_connection_config.secrets    
    base_url = f"https://{yotpo_secrets['another_domain']}"
    headers = {        
        "x-guid": f"{yotpo_secrets['x_guid']}",
        "x-api-key": f"{yotpo_secrets['x_api_key']}",
        "Content-Type": "application/json",
    }

    # user
    body = {
            "email":yotpo_erasure_identity_email,
            "first_name":"test_i",
            "last_name":"last_test",        
    }

    users_response = requests.post(url=f"{base_url}/api/v2/customers", headers=headers, json=body)

    error_message = f"customer with email {yotpo_erasure_identity_email} could not be added to Yotpo"
    user_loyalty_data = poll_for_existence(
        customer_loyalty_exists,
        (yotpo_erasure_identity_email, yotpo_secrets),
        retries=20,
        interval=8,
        error_message=error_message,
    )

    # sleep(60)

    yield users_response.ok


@pytest.fixture(scope="function")
def yotpo_create_access_token(
    yotpo_connection_config: ConnectionConfig, yotpo_erasure_identity_email: str
) -> None:

    # sleep(10)

    yotpo_secrets = yotpo_connection_config.secrets    
    base_url = f"https://{yotpo_secrets['domain']}"
    headers = {        
        "Content-Type": "application/json",
    }

    # user
    body = {        
            "secret": f"{yotpo_secrets['secret_key']}",
    }

    users_response = requests.post(url=f"{base_url}/core/v3/stores/{yotpo_secrets['app_key']}/access_tokens", headers=headers, json=body)
    token = users_response.json()["access_token"]
    # token = 'v14C9LXiLroH6Kfs3JaSygRrKtJH2G6qrm5GPHtL'    

    yield token


def customer_exists(yotpo_random_external_id: str, yotpo_secrets , yotpo_create_access_token: str):
    """
    Confirm whether customer exists by calling customer search by email api and comparing resulting firstname str.
    Returns customer ID if it exists, returns None if it does not.
    """       
    base_url = f"https://{yotpo_secrets['domain']}"
    headers = {        
        "X-Yotpo-Token": yotpo_create_access_token,
    }

    customer_response = requests.get(
        url=f"{base_url}/core/v3/stores/{yotpo_secrets['app_key']}/customers",
        headers=headers,
        params={"external_ids": yotpo_random_external_id},
    )    

    # Check the status of the api
    if 200 != customer_response.status_code:
        return None
    if len(customer_response.json()['customers']) == 0:
        return None
    
    datas = customer_response.json()['customers'][0]['first_name']    

    return customer_response.json()

def customer_loyalty_exists(yotpo_erasure_identity_email: str, yotpo_secrets):
    """
    Confirm whether customer exists by calling customer search by email api and comparing resulting firstname str.
    Returns customer ID if it exists, returns None if it does not.
    """       

    base_url = f"https://{yotpo_secrets['another_domain']}"
    headers = {        
        "x-guid": f"{yotpo_secrets['x_guid']}",
        "x-api-key": f"{yotpo_secrets['x_api_key']}",        
    }

    # customer loyalty update checking
    loyalty_response = requests.get(
        url=f"{base_url}/api/v2/customers",
        headers=headers,
        params={"customer_email": yotpo_erasure_identity_email},
    )   

    # Check the status of the api
    if 200 != loyalty_response.status_code:
        return None
    if len(loyalty_response.json()) == 0:
        return None   

    return loyalty_response.json()
