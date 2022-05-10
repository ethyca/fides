import os
import random
import time
from typing import Any, Dict, Generator

import pydash
import pytest
import requests
from faker import Faker
from sqlalchemy.orm import Session

from fidesops.core.config import load_toml
from fidesops.db import session
from fidesops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fidesops.models.datasetconfig import DatasetConfig
from tests.fixtures.application_fixtures import load_dataset
from tests.fixtures.saas_example_fixtures import load_config

saas_config = load_toml("saas_config.toml")


@pytest.fixture(scope="function")
def segment_secrets():
    return {
        "domain": pydash.get(saas_config, "segment.domain")
        or os.environ.get("SEGMENT_DOMAIN"),
        "personas_domain": pydash.get(saas_config, "segment.personas_domain")
        or os.environ.get("SEGMENT_PERSONAS_DOMAIN"),
        "workspace": pydash.get(saas_config, "segment.workspace")
        or os.environ.get("SEGMENT_WORKSPACE"),
        "access_token": pydash.get(saas_config, "segment.access_token")
        or os.environ.get("SEGMENT_ACCESS_TOKEN"),
        "namespace_id": pydash.get(saas_config, "segment.namespace_id")
        or os.environ.get("SEGMENT_NAMESPACE_ID"),
        "access_secret": pydash.get(saas_config, "segment.access_secret")
        or os.environ.get("SEGMENT_ACCESS_SECRET"),
        "api_domain": pydash.get(saas_config, "segment.api_domain")
        or os.environ.get("SEGMENT_API_DOMAIN"),
        "user_token": pydash.get(saas_config, "segment.user_token")
        or os.environ.get("SEGMENT_USER_TOKEN"),
    }


@pytest.fixture(scope="session")
def segment_identity_email():
    return pydash.get(saas_config, "segment.identity_email") or os.environ.get(
        "SEGMENT_IDENTITY_EMAIL"
    )


@pytest.fixture
def segment_config() -> Dict[str, Any]:
    return load_config("data/saas/config/segment_config.yml")


@pytest.fixture
def segment_dataset() -> Dict[str, Any]:
    return load_dataset("data/saas/dataset/segment_dataset.yml")[0]


@pytest.fixture(scope="function")
def segment_connection_config(
    db: session, segment_config, segment_secrets
) -> Generator:
    fides_key = segment_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": segment_secrets,
            "saas_config": segment_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def segment_dataset_config(
    db: Session,
    segment_connection_config: ConnectionConfig,
    segment_dataset: Dict[str, Any],
) -> Generator:
    fides_key = segment_dataset["fides_key"]
    segment_connection_config.name = fides_key
    segment_connection_config.key = fides_key
    segment_connection_config.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": segment_connection_config.id,
            "fides_key": fides_key,
            "dataset": segment_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)


@pytest.fixture(scope="session")
def segment_erasure_identity_email(segment_identity_email) -> str:
    timestamp = int(time.time())
    at_index: int = segment_identity_email.find("@")
    email = f"{segment_identity_email[0:at_index]}{timestamp}{segment_identity_email[at_index:]}"
    return email


def _get_user_id(email: str, secrets: Dict[str, Any]) -> str:
    personas_domain = secrets["personas_domain"]
    namespace_id = secrets["namespace_id"]
    access_secret = secrets["access_secret"]
    response = requests.get(
        f"https://{personas_domain}/v1/spaces/{namespace_id}/collections/users/profiles/user_id:{email}/metadata",
        auth=(access_secret, None),
    )
    if not response.ok:
        return None

    return response.json()["segment_id"]


def _get_track_events(segment_id: str, secrets: Dict[str, Any]) -> Dict[str, Any]:
    personas_domain = secrets["personas_domain"]
    namespace_id = secrets["namespace_id"]
    access_secret = secrets["access_secret"]

    response = requests.get(
        f"https://{personas_domain}/v1/spaces/{namespace_id}/collections/users/profiles/{segment_id}/events",
        auth=(access_secret, None),
    )
    if not response.ok or response.json()["data"] is None:
        return None

    return response.json()["data"][0]


@pytest.fixture(scope="function")
def segment_erasure_data(
    segment_connection_config, segment_erasure_identity_email
) -> str:
    """Seeds a segment user and event"""
    segment_secrets = segment_connection_config.secrets
    if not segment_identity_email:  # Don't run unnecessarily locally
        return

    api_domain = segment_secrets["api_domain"]
    user_token = segment_secrets["user_token"]

    faker = Faker()

    timestamp = int(time.time())
    email = segment_erasure_identity_email
    first_name = faker.first_name()
    last_name = faker.last_name()

    # Create user
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {user_token}",
    }
    body = {
        "userId": email,
        "traits": {
            "subscriptionStatus": "active",
            "address": {
                "city": faker.city(),
                "country": faker.country(),
                "postalCode": faker.postcode(),
                "state": "NY",
            },
            "age": random.randrange(18, 99),
            "avatar": "",
            "industry": "data",
            "description": faker.job(),
            "email": email,
            "firstName": first_name,
            "id": timestamp,
            "lastName": last_name,
            "name": f"{first_name} {last_name}",
            "phone": faker.phone_number(),
            "title": faker.prefix(),
            "username": f"test_fidesops_user_{timestamp}",
            "website": "www.example.com",
        },
    }
    response = requests.post(
        f"https://{api_domain}identify", headers=headers, json=body
    )
    assert response.ok

    # Wait until user returns data
    retries = 10
    while (segment_id := _get_user_id(email, segment_secrets)) is None:
        if not retries:
            raise Exception(
                "The user endpoint did not return the required data for testing during the time limit"
            )
        retries -= 1
        time.sleep(5)

    # Create event
    body = {
        "userId": email,
        "type": "track",
        "event": "User Registered",
        "properties": {"plan": "Free", "accountType": faker.company()},
        "context": {"ip": faker.ipv4()},
    }

    response = requests.post(f"https://{api_domain}track", headers=headers, json=body)
    assert response.ok

    # Wait until track_events returns data
    retries = 10
    while _get_track_events(segment_id, segment_secrets) is None:
        if not retries:
            raise Exception(
                "The track_events endpoint did not return the required data for testing during the time limit"
            )
        retries -= 1
        time.sleep(5)
