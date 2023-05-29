from typing import Any, Dict, Generator

import pydash
import pytest
import requests

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
        "scope": pydash.get(saas_config, "adobe_sign.scope") or secrets["scope"],
        "access_token": pydash.get(saas_config, "adobe_sign.access_token") or secrets["access_token"],
        # add the rest of your secrets here
    }


@pytest.fixture(scope="session")
def adobe_sign_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "adobe_sign.identity_email") or secrets["identity_email"]
    )


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