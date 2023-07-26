from typing import Any, Dict, Generator

import pydash
import pytest

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("gong")


@pytest.fixture(scope="session")
def gong_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "gong.domain")
        or secrets["domain"],
        "token": pydash.get(saas_config, "gong.token")
        or secrets["token"],
        # "salesforce_domain": pydash.get(saas_config, "gong.salesforce_domain")
        # or secrets["salesforce_domain"],
        # "salesforce_token": pydash.get(saas_config, "gong.salesforce_token")
        # or secrets["salesforce_token"],
    }


@pytest.fixture(scope="session")
def gong_identity_email(saas_config) -> str:
    return (
        pydash.get(
            saas_config, "gong.identity_email") or secrets["identity_email"]
    )


@pytest.fixture(scope="session")
def gong_identity_phone_number(saas_config) -> str:
    return (
        pydash.get(
            saas_config, "gong.identity_phone_number") or secrets["identity_phone_number"]
    )


@pytest.fixture
def gong_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def gong_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def gong_erasure_external_references() -> Dict[str, Any]:
    return {}


# class GongClient:
#     def __init__(self, secrets: Dict[str, Any]):
#         self.base_url = f"https://{secrets['domain']}"
#         self.salesforce_url = f"https://{secrets['salesforce_domain']}"
#         self.headers = (
#             {
#                 "Authorization": f"Basic {secrets['token']}",
#             },
#         )
#         self.salesforce_token = f"Bearer {secrets['salesforce_token']}"

#     def create_data(self, email) -> str:
#         response = requests.post(
#             url=f"{self.salesforce_url}/services/data/v54.0/sobjects/Contact",
#             headers={"Authorization": self.salesforce_token},
#             json={
#                 "firstName": "Gong",
#                 "lastName": "Test",
#                 "email": email,
#                 "phone": "%2B19518938593"
#             }
#         )
#         return response.json()

#     def get_email_data(self, player_id: str):
#         response = requests.get(
#             url=f"{self.base_url}/v2/data-privacy/data-for-email-address",
#             headers=self.headers,
#             params={"emailAddress": gong_erasure_identity_email},
#         )
#         if response.ok:
#             return response.json()["requestId"]
        
#     def get_phone_data(self, player_id: str):
#         response = requests.get(
#             url=f"{self.base_url}/v2/data-privacy/data-for-phone-number",
#             headers=self.headers,
#             params={"phoneNumber": "%2B19518938593"},
#         )
#         if response.ok:
#             return response.json()["requestId"]


@pytest.fixture
def gong_client(gong_secrets) -> Generator:
    yield GongClient(gong_secrets)


# @pytest.fixture
# def gong_erasure_data(
#     gong_client: GongClient,
#     gong_erasure_identity_email: str,
# ) -> Generator:
#     # create data
#     data = gong_client.create_data(gong_erasure_identity_email)
#     yield data


@pytest.fixture
def gong_runner(
    db,
    cache,
    gong_secrets,
    gong_external_references,
    gong_erasure_external_references,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "gong",
        gong_secrets,
        external_references=gong_external_references,
        erasure_external_references=gong_erasure_external_references,
    )
