from typing import Any, Dict, Generator

import pydash
import pytest
import requests
from requests import Response
from requests.auth import HTTPBasicAuth
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

secrets = get_secrets("delighted")


@pytest.fixture(scope="session")
def delighted_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "delighted.domain") or secrets["domain"],
        "api_key": pydash.get(saas_config, "delighted.api_key") or secrets["api_key"],
    }


@pytest.fixture(scope="session")
def delighted_identity_email(saas_config):
    return (
        pydash.get(saas_config, "delighted.identity_email") or secrets["identity_email"]
    )


@pytest.fixture(scope="function")
def delighted_erasure_identity_email() -> str:
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture
def delighted_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/delighted_config.yml",
        "<instance_fides_key>",
        "delighted_instance",
    )


@pytest.fixture
def delighted_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/delighted_dataset.yml",
        "<instance_fides_key>",
        "delighted_instance",
    )[0]


@pytest.fixture(scope="function")
def delighted_connection_config(
    db: Session, delighted_config, delighted_secrets
) -> Generator:
    fides_key = delighted_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": delighted_secrets,
            "saas_config": delighted_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def delighted_dataset_config(
    db: Session,
    delighted_connection_config: ConnectionConfig,
    delighted_dataset: Dict[str, Any],
) -> Generator:
    fides_key = delighted_dataset["fides_key"]
    delighted_connection_config.name = fides_key
    delighted_connection_config.key = fides_key
    delighted_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, delighted_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": delighted_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


class DelightedTestClient:
    def __init__(self, delighted_connection_config: ConnectionConfig):
        delighted_secrets = delighted_connection_config.secrets
        self.auth = HTTPBasicAuth(delighted_secrets["api_key"], "")
        self.base_url = f"https://{delighted_secrets['domain']}"

    def create_person(self, email) -> Response:
        return requests.post(
            url=f"{self.base_url}/v1/people",
            auth=self.auth,
            json={
                "name": "ethyca test erasure",
                "email": email,
                "send": "false",
            },
        )

    def create_survey_response(self, person_id) -> Response:
        return requests.post(
            url=f"{self.base_url}/v1/survey_responses.json",
            auth=self.auth,
            json={"person": person_id, "score": "3"},
        )

    def get_person(self, email) -> Any:
        response = requests.get(
            url=f"{self.base_url}/v1/people.json",
            auth=self.auth,
            params={"email": email},
        )
        if len(response.json()):
            return response

    def get_survey_responses(self, person_id) -> Any:
        response = requests.get(
            url=f"{self.base_url}/v1/survey_responses",
            auth=self.auth,
            params={"person_id": person_id},
        )
        if response.ok:
            return response


@pytest.fixture(scope="function")
def delighted_test_client(
    delighted_connection_config: DelightedTestClient,
) -> Generator:
    test_client = DelightedTestClient(delighted_connection_config)
    yield test_client


@pytest.fixture(scope="function")
def delighted_create_erasure_data(
    delighted_test_client, delighted_erasure_identity_email
) -> Generator:
    # create person
    response = delighted_test_client.create_person(delighted_erasure_identity_email)
    assert response.ok
    person = response.json()

    # create survey response
    response = delighted_test_client.create_survey_response(person["id"])
    assert response.ok
    poll_for_existence(
        delighted_test_client.get_survey_responses,
        (person["id"],),
        interval=60,
        verification_count=10,
    )
    yield person
