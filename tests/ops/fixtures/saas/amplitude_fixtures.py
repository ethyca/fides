from time import sleep
from typing import Any, Dict, Generator

import pydash
import pytest
import requests
from multidimensional_urlencode import urlencode as multidimensional_urlencode
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

secrets = get_secrets("amplitude")


@pytest.fixture(scope="session")
def amplitude_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "amplitude.domain") or secrets["domain"],
        "api_token": pydash.get(saas_config, "amplitude.api_token") or secrets["api_token"],
        "requester_email": pydash.get(saas_config, "amplitude.requester_email") or secrets["requester_email"],
        "create_domain_url": pydash.get(saas_config, "amplitude.create_domain_url") or secrets["create_domain_url"],
    }


@pytest.fixture(scope="session")
def amplitude_identity_email(saas_config):
    return (
        pydash.get(saas_config, "amplitude.identity_email") or secrets["identity_email"]
    )


@pytest.fixture(scope="function")
def amplitude_erasure_identity_email() -> str:
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture
def amplitude_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/amplitude_config.yml",
        "<instance_fides_key>",
        "amplitude_instance",
    )


@pytest.fixture
def amplitude_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/amplitude_dataset.yml",
        "<instance_fides_key>",
        "amplitude_instance",
    )[0]


@pytest.fixture(scope="function")
def amplitude_connection_config(
    db: Session, amplitude_config, amplitude_secrets
) -> Generator:
    fides_key = amplitude_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": amplitude_secrets,
            "saas_config": amplitude_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def amplitude_dataset_config(
    db: Session,
    amplitude_connection_config: ConnectionConfig,
    amplitude_dataset: Dict[str, Any],
) -> Generator:
    fides_key = amplitude_dataset["fides_key"]
    amplitude_connection_config.name = fides_key
    amplitude_connection_config.key = fides_key
    amplitude_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, amplitude_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": amplitude_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture(scope="function")
def amplitude_create_erasure_data(
    amplitude_connection_config: ConnectionConfig, amplitude_erasure_identity_email: str
) -> None:

    # sleep(60)

    amplitude_secrets = amplitude_connection_config.secrets
    base_url = f"https://{amplitude_secrets['create_domain_url']}"
    # headers = {
    #     "Content-Type": "application/x-www-form-urlencoded",        
    # }

    # user
    # get_param_value ={"api_key" : "c92f6b0222117d44766aba11f346e7a6",
    #     "identification" : {'user_id':amplitude_erasure_identity_email,'country':'ind'}
    #     }
    url_val = '/identify?api_key=c92f6b0222117d44766aba11f346e7a6&identification={"user_id":"'+amplitude_erasure_identity_email+'","country":"ind"}'

    # users_response = requests.get(
    #     url=f"{base_url}/identify", 
    #     params=get_param_value,
    #     )
    users_response = requests.get(
        url=f"{base_url}"+url_val
        )
    sleep(30)

    yield users_response.ok
