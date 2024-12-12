from typing import Any, Dict, Generator, cast

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
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("unbounce")


@pytest.fixture(scope="session")
def unbounce_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "unbounce.domain") or secrets["domain"],
        "client_id": pydash.get(saas_config, "unbounce.client_id")
        or secrets["client_id"],
        "client_secret": pydash.get(saas_config, "unbounce.client_secret")
        or secrets["client_secret"],
        "redirect_uri": pydash.get(saas_config, "unbounce.redirect_uri")
        or secrets["redirect_uri"],
        "access_token": pydash.get(saas_config, "unbounce.access_token")
        or secrets["access_token"],
        "page_id": pydash.get(saas_config, "unbounce.page_id") or secrets["page_id"],
    }


@pytest.fixture(scope="session")
def unbounce_identity_email(saas_config):
    return (
        pydash.get(saas_config, "unbounce.identity_email") or secrets["identity_email"]
    )


@pytest.fixture(scope="function")
def unbounce_erasure_identity_email() -> str:
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture
def unbounce_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/unbounce_config.yml",
        "<instance_fides_key>",
        "unbounce_instance",
    )


@pytest.fixture
def unbounce_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/unbounce_dataset.yml",
        "<instance_fides_key>",
        "unbounce_instance",
    )[0]


@pytest.fixture(scope="function")
def unbounce_connection_config(
    db: Session, unbounce_config, unbounce_secrets
) -> Generator:
    fides_key = unbounce_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": unbounce_secrets,
            "saas_config": unbounce_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def unbounce_dataset_config(
    db: Session,
    unbounce_connection_config: ConnectionConfig,
    unbounce_dataset: Dict[str, Any],
) -> Generator:
    fides_key = unbounce_dataset["fides_key"]
    unbounce_connection_config.name = fides_key
    unbounce_connection_config.key = fides_key
    unbounce_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, unbounce_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": unbounce_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


class UnbounceTestClient:
    def __init__(self, unbounce_connection_config: ConnectionConfig):
        self.unbounce_secrets = cast(Dict, unbounce_connection_config.secrets)
        self.headers = {
            "Authorization": f"Bearer {self.unbounce_secrets['access_token']}"
        }
        self.page_id = self.unbounce_secrets["page_id"]
        self.base_url = f"https://{self.unbounce_secrets['domain']}"

    def create_lead(self, email: str) -> Response:
        body = {
            "conversion": "True",
            "form_submission": {
                "variant_id": "a",
                "form_data": {
                    "first_name": "Test",
                    "last_name": "User",
                    "email": email,
                },
            },
        }

        return requests.post(
            url=f"{self.base_url}/pages/{self.page_id}/leads",
            headers=self.headers,
            json=body,
        )


@pytest.fixture(scope="function")
def unbounce_test_client(
    unbounce_connection_config: ConnectionConfig,
) -> Generator:
    test_client = UnbounceTestClient(unbounce_connection_config)
    yield test_client


@pytest.fixture(scope="function")
def unbounce_create_erasure_data(
    unbounce_test_client,
    unbounce_erasure_identity_email: str,
) -> None:
    # create lead
    unbounce_test_client.create_lead(unbounce_erasure_identity_email)
