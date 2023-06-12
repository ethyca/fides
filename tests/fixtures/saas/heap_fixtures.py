from typing import Any, Dict, Generator

import pydash
import pytest
import requests

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("heap")


@pytest.fixture(scope="session")
def heap_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "heap.domain") or secrets["domain"],
        "app_id": pydash.get(saas_config, "heap.app_id") or secrets["app_id"],
        "api_key": pydash.get(saas_config, "heap.api_key") or secrets["api_key"],
    }


@pytest.fixture(scope="session")
def heap_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "heap.identity_email") or secrets["identity_email"]
    )


@pytest.fixture(scope="session")
def heap_erasure_identity_email() -> str:
    return generate_random_email()


class heapClient:
    def __init__(self, secrets: Dict[str, Any]):
        self.base_url = f"https://{secrets['domain']}"
        # self.headers = (
        #     {
        #         "Authorization": f"Basic {secrets['api_key']}",
        #     },
        # )
        self.auth = secrets["app_id"], secrets["api_key"]

        self.api_key = secrets['api_key']
        self.app_id = secrets["app_id"]

    def create_device(self, email) -> str:
        response = requests.post(
            url=f"{self.base_url}/api/add_user_properties",
            #auth={self.auth},
            json={
                "app_id": self.app_id,
                "identity": email,
                "properties": {
                    "age": "25",
                    "language": "English",
                    "profession": "Scientist",
                    "email": email
                }
            },
        )
        
        return response.ok

    def get_device(self, player_id: str):
        response = requests.get(
            url=f"{self.base_url}/api/v1/players/{player_id}",
            headers={"Authorization": self.api_key},
            params={"app_id": self.app_id},
        )
        if response.ok:
            return response.json()["id"]


@pytest.fixture
def heap_client(heap_secrets) -> Generator:
    yield heapClient(heap_secrets)


@pytest.fixture
def heap_erasure_data(
    heap_client: heapClient,
    heap_erasure_identity_email: str,
) -> Generator:
    # create user
    user = heap_client.create_device(heap_erasure_identity_email)
    yield user


@pytest.fixture
def heap_runner(
    db,
    cache,
    heap_secrets,
   # heap_external_references,
    #heap_erasure_external_references,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "heap",
        heap_secrets,
        #external_references=heap_external_references,
       # erasure_external_references=heap_erasure_external_references,
    )
