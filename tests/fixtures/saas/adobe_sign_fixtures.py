from typing import Any, Dict, Generator

import pydash
import pytest
import requests
from sqlalchemy.orm import Session

from fides.api.ctl.sql_models import Dataset as CtlDataset
from fides.api.ops.cryptography import cryptographic_util
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

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("adobe_sign")


@pytest.fixture(scope="session")
def adobe_sign_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "adobe_sign.domain") or secrets["domain"],
        "client_id": pydash.get(saas_config, "adobe_sign.client_id") or secrets["client_id"],
        "client_secret": pydash.get(saas_config, "adobe_sign.client_secret") or secrets["client_secret"],
        "redirect_uri": pydash.get(saas_config, "adobe_sign.redirect_uri") or secrets["redirect_uri"],
        "scope": pydash.get(saas_config, "adobe_sign.scope") or secrets["scope"]
        # add the rest of your secrets here
    }


@pytest.fixture(scope="session")
def adobe_sign_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "adobe_sign.identity_email") or secrets["identity_email"]
    )


@pytest.fixture
def adobe_sign_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/adobe_sign_config.yml",
        "<instance_fides_key>",
        "adobe_signinstance",
    )


@pytest.fixture
def adobe_sign_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/adobe_sign_dataset.yml",
        "<instance_fides_key>",
        "adobe_sign_instance",
    )[0]


@pytest.fixture(scope="function")
def adobe_sign_connection_config(
    db: Session, adobe_sign_config, adobe_sign_secrets
) -> Generator:
    fides_key = adobe_sign_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": adobe_sign_secrets,
            "saas_config": adobe_sign_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def adobe_sign_dataset_config(
    db: Session,
    adobe_sign_connection_config: ConnectionConfig,
    adobe_sign_dataset: Dict[str, Any],
) -> Generator:
    fides_key = adobe_sign_dataset["fides_key"]
    adobe_sign_connection_config.name = fides_key
    adobe_sign_connection_config.key = fides_key
    adobe_sign_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, adobe_sign_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": adobe_sign_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)

@pytest.fixture
def adobe_sign_erasure_identity_email() -> str:
    return generate_random_email()

# class AdobeSignClient:
#     def __init__(self, secrets: Dict[str, Any]):
#         self.base_url = f"https://{secrets['domain']}"
#         self.headers = {
#             "Authorization": f"Basic {secrets['access_token']}",
#         }

#     def create_user(self, email):
#         return requests.post(
#             url=f"{self.base_url}/api/rest/v6/users",
#             headers=self.headers,
#             json={
#                 "accountType": "PRO",
#                 "email": email,
#                 "company": "Test company",
#                 "firstName": "Test",
#                 "initials": "T",
#                 "lastName": "name",
#                 "title": "Php"
#             },
#         )

#     def get_user(self, email):
#         return requests.get(
#             url=f"{self.base_url}/api/rest/v6/users",
#             headers=self.headers,
#             params={"email": email},
#         )


# @pytest.fixture
# def adobe_sign_client(adobe_sign_secrets) -> Generator:
#     yield AdobeSignClient(adobe_sign_secrets)


# @pytest.fixture
# def adobe_sign_erasure_data(
#     adobe_sign_client: AdobeSignClient,
#     adobe_sign_erasure_identity_email: str,
# ) -> Generator:
    
#     # user
#     response = adobe_sign_client.create_user(adobe_sign_erasure_identity_email)
#     assert response.ok
#     user = response.json()["userId"]

#     yield {user}


@pytest.fixture
def adobe_sign_runner(
    db,
    cache,
    adobe_sign_secrets,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "adobe_sign",
        adobe_sign_secrets
    )