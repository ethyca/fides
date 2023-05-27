from typing import Any, Dict, Generator

import pydash
import pytest
import requests

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("onesignal")


@pytest.fixture(scope="session")
def onesignal_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "onesignal.domain") or secrets["domain"],
        "app_id": pydash.get(saas_config, "onesignal.app_id") or secrets["app_id"],
        "api_key": pydash.get(saas_config, "onesignal.api_key") or secrets["api_key"],
    }


@pytest.fixture(scope="session")
def onesignal_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "onesignal.identity_email") or secrets["identity_email"]
    )


@pytest.fixture(scope="session")
def onesignal_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def onesignal_external_references(saas_config) -> Dict[str, Any]:
    return {
        "player_id": pydash.get(saas_config, "onesignal.player_id")
        or secrets["player_id"]
    }


@pytest.fixture
def onesignal_erasure_external_references(onesignal_erasure_data) -> Dict[str, Any]:
    player_id = onesignal_erasure_data
    return {"player_id": player_id}


class OnesignalClient:
    def __init__(self, secrets: Dict[str, Any]):
        self.base_url = f"https://{secrets['domain']}"
        self.headers = (
            {
                "Authorization": f"Basic {secrets['api_key']}",
            },
        )
        self.api_key = f"Basic {secrets['api_key']}"
        self.app_id = secrets["app_id"]

    def create_device(self, email) -> str:
        response = requests.post(
            url=f"{self.base_url}/api/v1/players",
            headers={"Authorization": self.api_key},
            json={
                "app_id": self.app_id,
                "device_type": 11,
                "identifier": email,
                "test_type": "1",
                "language": "en",
                "external_user_id": "5088124543035",
                "timezone": "-28800",
                "game_version": "1.1.1",
                "device_model": "Mi Note 11",
                "device_os": "15.1.1",
                "session_count": 600,
                "tags": {
                    "first_name": "Erasure test",
                    "last_name": "Test request",
                    "level": "99",
                    "amount_spent": "6000",
                    "account_type": "VIP",
                    "key_to_delete": '""',
                },
                "amount_spent": "100.99",
                "created_at": 0,
                "playtime": 600,
                "last_active": 0,
                "notification_types": 1,
                "lat": 37.563,
                "long": 122.3255,
                "country": "US",
            },
        )
        return response.json()["id"]

    def get_device(self, player_id: str):
        response = requests.get(
            url=f"{self.base_url}/api/v1/players/{player_id}",
            headers={"Authorization": self.api_key},
            params={"app_id": self.app_id},
        )
        if response.ok:
            return response.json()["id"]


@pytest.fixture
def onesignal_client(onesignal_secrets) -> Generator:
    yield OnesignalClient(onesignal_secrets)


@pytest.fixture
def onesignal_erasure_data(
    onesignal_client: OnesignalClient,
    onesignal_erasure_identity_email: str,
) -> Generator:
    # create device
    player_id = onesignal_client.create_device(onesignal_erasure_identity_email)
    yield player_id


@pytest.fixture
def onesignal_runner(
    db,
    cache,
    onesignal_secrets,
    onesignal_external_references,
    onesignal_erasure_external_references,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "onesignal",
        onesignal_secrets,
        external_references=onesignal_external_references,
        erasure_external_references=onesignal_erasure_external_references,
    )
