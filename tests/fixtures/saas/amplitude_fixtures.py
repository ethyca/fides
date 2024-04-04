import json
from typing import Any, Dict, Generator, cast

import pydash
import pytest
import requests
from multidimensional_urlencode import urlencode as multidimensional_urlencode
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

secrets = get_secrets("amplitude")


@pytest.fixture(scope="session")
def amplitude_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "amplitude.domain") or secrets["domain"],
        "identity_domain": pydash.get(saas_config, "amplitude.identity_domain")
        or secrets["identity_domain"],
        "api_key": pydash.get(saas_config, "amplitude.api_key") or secrets["api_key"],
        "secret_key": pydash.get(saas_config, "amplitude.secret_key")
        or secrets["secret_key"],
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


class AmplitudeTestClient:
    def __init__(self, amplitude_connection_config: ConnectionConfig):
        amplitude_secrets = cast(Dict, amplitude_connection_config.secrets)

        self.headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }
        self.auth = (
            amplitude_secrets["api_key"],
            amplitude_secrets["secret_key"],
        )
        self.api_key = amplitude_secrets["api_key"]
        self.base_url = f"https://{amplitude_secrets['domain']}"
        self.identity_url = f"https://{amplitude_secrets['identity_domain']}"

    def create_user(self, email_address: str) -> Response:
        return requests.post(
            f"{self.identity_url}/identify",
            headers=self.headers,
            data=multidimensional_urlencode(
                {
                    "api_key": self.api_key,
                    "identification": json.dumps([{"user_id": email_address}]),
                }
            ),
        )

    def get_user(self, email: str) -> Any:
        response = requests.get(
            url=f"{self.base_url}/api/2/usersearch",
            auth=self.auth,
            params={"user": email},
            headers=self.headers,
        )
        if response.json().get("matches"):
            return response


@pytest.fixture(scope="function")
def amplitude_test_client(
    amplitude_connection_config: ConnectionConfig,
) -> Generator:
    test_client = AmplitudeTestClient(
        amplitude_connection_config=amplitude_connection_config
    )
    yield test_client


@pytest.fixture(scope="function")
def amplitude_create_erasure_data(
    amplitude_test_client: AmplitudeTestClient,
    amplitude_erasure_identity_email: str,
) -> None:
    amplitude_test_client.create_user(amplitude_erasure_identity_email)

    poll_for_existence(
        amplitude_test_client.get_user,
        (amplitude_erasure_identity_email,),
        verification_count=3,
    )
