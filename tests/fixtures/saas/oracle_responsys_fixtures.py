from typing import Any, Dict, Generator

import pydash
import pytest
import requests
from requests import post

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
    generate_random_phone_number,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("oracle_responsys")


@pytest.fixture(scope="session")
def oracle_responsys_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "oracle_responsys.domain")
        or secrets["domain"],
        "username": pydash.get(saas_config, "oracle_responsys.username")
        or secrets["username"],
        "password": pydash.get(saas_config, "oracle_responsys.password")
        or secrets["password"],
        "profile_lists": pydash.get(saas_config, "oracle_responsys.profile_lists")
        or secrets["profile_lists"],
        "profile_extensions": pydash.get(
            saas_config, "oracle_responsys.profile_extensions"
        )
        or secrets["profile_extensions"],
        "test_list": pydash.get(saas_config, "oracle_responsys.test_list")
        or secrets["test_list"],
    }


@pytest.fixture(scope="session")
def oracle_responsys_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "oracle_responsys.identity_email")
        or secrets["identity_email"]
    )


@pytest.fixture(scope="session")
def oracle_responsys_identity_phone_number(saas_config):
    return (
        pydash.get(saas_config, "oracle_responsys.identity_phone_number")
        or secrets["identity_phone_number"]
    )


@pytest.fixture
def oracle_responsys_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def oracle_responsys_erasure_identity_phone_number() -> str:
    return generate_random_phone_number()


@pytest.fixture(scope="function")
def oracle_responsys_token(oracle_responsys_secrets) -> Generator:
    secrets = oracle_responsys_secrets
    response = post(
        url=f"https://{secrets['domain']}/rest/api/v1.3/auth/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "user_name": secrets["username"],
            "password": secrets["password"],
            "auth_type": "password",
        },
    )
    yield response.json()["authToken"]


@pytest.fixture
def oracle_responsys_erasure_data(
    oracle_responsys_erasure_identity_email: str,
    oracle_responsys_erasure_identity_phone_number: str,
    oracle_responsys_token: str,
    oracle_responsys_secrets,
) -> Generator:
    """
    Creates a dynamic test data record for profile_list_recipient for erasure tests.
    A profile_extension_recipient is not created, because they take a while to be queryable after being created.
    Yields RIID as this may be useful to have in test scenarios
    """
    base_url = f"https://{oracle_responsys_secrets['domain']}"
    headers = {
        "Authorization": oracle_responsys_token,
    }
    member_body = {
        "recordData": {
            "fieldNames": ["email_address_", "mobile_number_"],
            "records": [
                [
                    oracle_responsys_erasure_identity_email,
                    oracle_responsys_erasure_identity_phone_number[
                        1:
                    ],  # Omit the + prefix
                ]
            ],
            "mapTemplateName": None,
        },
        "mergeRule": {
            "htmlValue": "H",
            "optinValue": "I",
            "textValue": "T",
            "insertOnNoMatch": True,
            "matchColumnName1": "email_address_",
            "updateOnMatch": "UPDATE",
            "defaultPermissionStatus": "OPTIN",
        },
    }

    create_member_response = requests.post(
        url=f"{base_url}/rest/api/v1.3/lists/{oracle_responsys_secrets['test_list']}/members",
        json=member_body,
        headers=headers,
    )
    assert create_member_response.ok
    member_riid = create_member_response.json()["recordData"]["records"][0]

    yield member_riid


@pytest.fixture
def oracle_responsys_runner(
    db,
    cache,
    oracle_responsys_secrets,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "oracle_responsys",
        oracle_responsys_secrets,
    )
