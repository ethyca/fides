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


@pytest.fixture(scope="session")
def onesignal_erasure_data(
    onesignal_secrets,
    onesignal_erasure_identity_email: str,
) -> Generator:
    # create the data needed for erasure tests here
    response = requests.post(
        url="https://onesignal.com/api/v1/players",
        headers={
            "Authorization": f"Basic {onesignal_secrets['api_key']}",
        },
        json={
            "app_id": onesignal_secrets["app_id"],
            "device_type": 11,
            "identifier": onesignal_erasure_identity_email,
            "test_type": "1",
            "language": "en",
            "external_user_id": "5088124543035",
            "timezone": "-28800",
            "game_version": "1.1.1",
            "device_model": "Mi Note 11",
            "device_os": "15.1.1",
            "session_count": 600,
            "tags": {
                "first_name": "Vivek",
                "last_name": "Thiyagarajan",
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
    yield response.json()["id"]


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
