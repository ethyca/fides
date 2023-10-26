import uuid
from time import sleep
from typing import Any, Dict, Generator

import pydash
import pytest
import requests
from sqlalchemy.orm import Session

from fides.api.cryptography import cryptographic_util
from fides.api.db import session
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

secrets = get_secrets("braze")


@pytest.fixture(scope="session")
def braze_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "braze.domain") or secrets["domain"],
        "api_key": pydash.get(saas_config, "braze.api_key") or secrets["api_key"],
    }


@pytest.fixture(scope="session")
def braze_identity_email(saas_config):
    return pydash.get(saas_config, "braze.identity_email") or secrets["identity_email"]


@pytest.fixture(scope="session")
def braze_identity_phone_number(saas_config):
    return (
        pydash.get(saas_config, "braze.identity_phone_number")
        or secrets["identity_phone_number"]
    )


@pytest.fixture(scope="session")
def braze_erasure_identity_email():
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture
def braze_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/braze_config.yml",
        "<instance_fides_key>",
        "braze_instance",
    )


@pytest.fixture
def braze_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/braze_dataset.yml",
        "<instance_fides_key>",
        "braze_instance",
    )[0]


@pytest.fixture(scope="function")
def braze_connection_config(db: session, braze_config, braze_secrets) -> Generator:
    fides_key = braze_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": braze_secrets,
            "saas_config": braze_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def braze_dataset_config(
    db: Session,
    braze_connection_config: ConnectionConfig,
    braze_dataset,
    braze_config,
) -> Generator:
    fides_key = braze_config["fides_key"]
    braze_connection_config.name = fides_key
    braze_connection_config.key = fides_key
    braze_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, braze_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": braze_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture(scope="function")
def braze_erasure_data(
    braze_connection_config, braze_erasure_identity_email, braze_secrets
) -> Generator:
    base_url = f"https://{braze_secrets['domain']}"
    external_id = uuid.uuid4().hex
    body = {
        "attributes": [
            {
                "external_id": external_id,
                "first_name": "Walter",
                "last_name": "White",
                "email": braze_erasure_identity_email,
                "country": "US",
                "date_of_first_session": "2022-09-14T16:14:56+00:00",
                "dob": "1980-12-21",
                "email_subscribe": "opted_in",
                "gender": "M",
                "home_city": "New York",
                "language": "en",
                "time_zone": "US/Eastern",
                "user_aliases": [
                    {
                        "external_id": external_id,
                        "alias_name": "Breaking",
                        "alias_label": "Bad",
                    }
                ],
                "app_id": f"app_identifier.{external_id}",
            }
        ],
        "events": [
            {
                "external_id": external_id,
                "app_id": f"app_identifier.{external_id}",
                "name": "watched_trailer",
                "time": "2013-07-16T19:20:30+1:00",
            },
            {
                "external_id": external_id,
                "app_id": "app_identifier.{{external_id}}",
                "name": "this is test event to create",
                "time": "2022-07-16T19:20:30+1:00",
            },
        ],
        "purchases": [
            {
                "external_id": external_id,
                "product_id": "Car",
                "currency": "USD",
                "price": 12.12,
                "quantity": 6,
                "time": "2017-05-12T18:47:12Z",
                "properties": {
                    "integer_property": 3,
                    "string_property": "Some Property",
                    "date_property": "2014-02-02T00:00:00Z",
                },
            }
        ],
    }

    headers = {"Authorization": f"Bearer {braze_secrets['api_key']}"}

    response = requests.post(url=f"{base_url}/users/track", json=body, headers=headers)
    response_data = response.json()

    assert response.ok

    error_message = (
        f"User with email {braze_erasure_identity_email} could not be added to Braze"
    )
    poll_for_existence(
        _user_exists,
        (braze_erasure_identity_email, braze_secrets),
        error_message=error_message,
        interval=60,
        verification_count=10,
    )

    yield response_data

    # Remove Data

    export_data = requests.post(
        url=f"{base_url}/users/export/ids",
        json={
            "external_ids": [
                external_id,
            ],
            "fields_to_export": [
                "braze_id",
            ],
        },
        headers=headers,
    )
    assert export_data.ok

    braze_ids = [i["braze_id"] for i in export_data.json().get("users")]
    delete_user = requests.post(
        url=f"{base_url}/users/delete", json={"braze_ids": braze_ids}, headers=headers
    )
    assert delete_user.status_code == 201


def _user_exists(braze_erasure_identity_email: str, braze_secrets):
    """
    Confirm whether user exists by calling user search by email api and comparing resulting firstname str.
    Returns user ID if it exists, returns None if it does not.
    """
    base_url = f"https://{braze_secrets['domain']}"
    headers = {
        "Authorization": f"Bearer {braze_secrets['api_key']}",
    }
    body = {
        "email_address": braze_erasure_identity_email,
        "fields_to_export": ["email", "first_name"],
    }

    response = requests.post(
        url=f"{base_url}/users/export/ids",
        json=body,
        headers=headers,
    )
    users = response.json().get("users")

    return response if users and users[0]["first_name"] != "MASKED" else None
