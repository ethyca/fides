from typing import Any, Dict, Generator, Optional, cast

import pydash
import pytest
import requests
from requests import Response
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
from tests.ops.test_helpers.saas_test_utils import poll_for_existence
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("aircall")


@pytest.fixture(scope="session")
def aircall_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "aircall.domain") or secrets["domain"],
        "api_id": pydash.get(saas_config, "aircall.api_id") or secrets["api_id"],
        "api_token": pydash.get(saas_config, "aircall.api_token")
        or secrets["api_token"],
    }


@pytest.fixture(scope="session")
def aircall_identity_email(saas_config):
    return (
        pydash.get(saas_config, "aircall.identity_email") or secrets["identity_email"]
    )


@pytest.fixture(scope="session")
def aircall_identity_phone_number(saas_config):
    return (
        pydash.get(saas_config, "aircall.identity_phone_number")
        or secrets["identity_phone_number"]
    )


@pytest.fixture(scope="function")
def aircall_erasure_identity_email() -> str:
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture(scope="function")
def aircall_erasure_identity_phone_number() -> str:
    return f"+16123456788"


@pytest.fixture
def aircall_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/aircall_config.yml",
        "<instance_fides_key>",
        "aircall_instance",
    )


@pytest.fixture
def aircall_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/aircall_dataset.yml",
        "<instance_fides_key>",
        "aircall_instance",
    )[0]


@pytest.fixture(scope="function")
def aircall_connection_config(
    db: Session, aircall_config, aircall_secrets
) -> Generator:
    fides_key = aircall_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": aircall_secrets,
            "saas_config": aircall_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def aircall_dataset_config(
    db: Session,
    aircall_connection_config: ConnectionConfig,
    aircall_dataset: Dict[str, Any],
) -> Generator:
    fides_key = aircall_dataset["fides_key"]
    aircall_connection_config.name = fides_key
    aircall_connection_config.key = fides_key
    aircall_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, aircall_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": aircall_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


class AircallTestClient:
    def __init__(self, aircall_connection_config: ConnectionConfig):
        self.aircall_secrets = cast(Dict, aircall_connection_config.secrets)
        self.auth = self.aircall_secrets["api_id"], self.aircall_secrets["api_token"]
        self.base_url = f"https://{self.aircall_secrets['domain']}"

    def create_contact(self, phone_number: str, email: str) -> Response:
        body = {
            "first_name": "john",
            "phone_numbers": [{"label": "Office", "value": phone_number}],
            "emails": [{"label": "Office", "value": email}],
        }

        return requests.post(
            url=f"{self.base_url}/v1/contacts", auth=self.auth, json=body
        )

    def get_contact(self, phone_number: str) -> Optional[Response]:
        response = requests.get(
            url=f"{self.base_url}/v1/contacts/search",
            auth=self.auth,
            params={"phone_number": phone_number},
        )
        if response.json()["contacts"]:
            return response
        return None


@pytest.fixture(scope="function")
def aircall_test_client(
    aircall_connection_config: ConnectionConfig,
) -> Generator:
    test_client = AircallTestClient(aircall_connection_config)
    yield test_client


@pytest.fixture(scope="function")
def aircall_create_erasure_data(
    aircall_test_client,
    aircall_erasure_identity_email: str,
    aircall_erasure_identity_phone_number: str,
) -> Generator:
    # create contact
    aircall_test_client.create_contact(
        aircall_erasure_identity_phone_number, aircall_erasure_identity_email
    )

    poll_for_existence(
        aircall_test_client.get_contact, (aircall_erasure_identity_phone_number,)
    )
