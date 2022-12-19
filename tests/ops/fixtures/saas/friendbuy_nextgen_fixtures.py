from typing import Any, Dict, Generator

import pydash
import pytest
import requests

from sqlalchemy.orm import Session
from faker import Faker

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
from fides.lib.cryptography import cryptographic_util
from fides.lib.db import session
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("friendbuy_nextgen")
faker = Faker()


@pytest.fixture(scope="function")
def friendbuy_nextgen_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "friendbuy_nextgen.domain")
        or secrets["domain"],
        "client_id": pydash.get(saas_config, "friendbuy_nextgen.client_id")
        or secrets["client_id"],
        "client_secret": pydash.get(saas_config, "friendbuy_nextgen.client_secret")
        or secrets["client_secret"],
        "token": pydash.get(saas_config, "friendbuy_nextgen.token") or secrets["token"],
    }


@pytest.fixture(scope="function")
def friendbuy_nextgen_identity_email(saas_config):
    return (
        pydash.get(saas_config, "friendbuy_nextgen.identity_email")
        or secrets["identity_email"]
    )


@pytest.fixture(scope="function")
def friendbuy_nextgen_erasure_identity_id():
    return f"{cryptographic_util.generate_secure_random_string(13)}"


@pytest.fixture(scope="session")
def friendbuy_nextgen_erasure_identity_email():
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture
def friendbuy_nextgen_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/friendbuy_nextgen_config.yml",
        "<instance_fides_key>",
        "friendbuy_nextgen_instance",
    )


@pytest.fixture
def friendbuy_nextgen_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/friendbuy_nextgen_dataset.yml",
        "<instance_fides_key>",
        "friendbuy_nextgen_instance",
    )[0]


@pytest.fixture(scope="function")
def friendbuy_nextgen_connection_config(
    db: session, friendbuy_nextgen_config, friendbuy_nextgen_secrets
) -> Generator:
    fides_key = friendbuy_nextgen_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": friendbuy_nextgen_secrets,
            "saas_config": friendbuy_nextgen_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def friendbuy_nextgen_dataset_config(
    db: Session,
    friendbuy_nextgen_connection_config: ConnectionConfig,
    friendbuy_nextgen_dataset: Dict[str, Any],
) -> Generator:
    fides_key = friendbuy_nextgen_dataset["fides_key"]
    friendbuy_nextgen_connection_config.name = fides_key
    friendbuy_nextgen_connection_config.key = fides_key
    friendbuy_nextgen_connection_config.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": friendbuy_nextgen_connection_config.id,
            "fides_key": fides_key,
            "dataset": friendbuy_nextgen_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)


@pytest.fixture(scope="function")
def friendbuy_nextgen_erasure_data(
    friendbuy_nextgen_secrets,
    friendbuy_nextgen_erasure_identity_email,
    friendbuy_nextgen_erasure_identity_id,
) -> Generator:
    """
    Creates a dynamic test data record for erasure tests.
    Yields user ID as this may be useful to have in test scenarios
    """

    base_url = f"https://{friendbuy_nextgen_secrets['domain']}"
    header = {"Authorization": "Bearer " + friendbuy_nextgen_secrets["token"]}
    # Create user
    user_body = {
        "email": friendbuy_nextgen_erasure_identity_email,
        "customerId": friendbuy_nextgen_erasure_identity_id,
        "isNewCustomer": True,
        "firstName": "test",
        "lastName": "test",
        "age": 0,
        "gender": "male",
        "zipCode": "string",
        "state": "string",
        "city": "string",
        "category": "string",
        "country": "string",
        "language": "string",
        "ipAddress": "string",
        "userAgent": "Mozilla/5.0...",
        "timezone": "America/Los_Angeles",
        "birthday": {"day": 1, "month": 10, "year": 1980},
    }
    users_response = requests.post(
        url=f"{base_url}/v1/customer", json=user_body, headers=header
    )
    assert users_response.ok
    user = users_response.json()
    yield user
