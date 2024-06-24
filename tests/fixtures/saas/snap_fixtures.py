from typing import Any, Dict, Generator

import pydash
import pytest
import hashlib
import requests

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("snap")


@pytest.fixture(scope="session")
def snap_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "snap.domain")
        or secrets["domain"],
        "client_id": pydash.get(saas_config, "snap.client_id")
        or secrets["snap_client_id"],
        "client_secret": pydash.get(saas_config, "snap.client_secret")
        or secrets["snap_client_secret"],
        "ad_account_id": pydash.get(saas_config, "snap.ad_account_id")
        or secrets["ad_account_id"],
        "access_token": pydash.get(saas_config, "snap.access_token")
        or secrets["access_token"],
        "redirect_uri": pydash.get(saas_config, "snap.redirect_uri")
        or secrets["redirect_uri"]
    }


@pytest.fixture(scope="session")
def snap_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "snap.identity_email") or secrets["identity_email"]
    )


@pytest.fixture
def snap_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def snap_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def snap_erasure_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def snap_erasure_data(
    snap_erasure_identity_email: str,
    snap_secrets,
) -> Generator:
    # create the data needed for erasure tests here
    # in this case we just need to ensure that there is a user in a segment so the erasure has a valid target
    # we also need to ensure our test email address is all lower case and then sha256 it
    prep_hash = hashlib.new('sha256')
    to_lower_email = snap_erasure_identity_email
    lowered_email = to_lower_email.lower()
    hash_email = prep_hash.update(lowered_email.encode())
    processed = hash_email.hexdigest(())
    payload = {
        "users": [
            {
                "schema": [
                    "EMAIL_SHA256"
                ],
                "data": [
                    [
                        processed
                    ]
                ]
            }
        ]
    }
    # we could find these through the same kind of calls we do in the override but if this is only for testing would it be better to cut down on the number of requests by hardcoding this value?
    erasure_segment = "6569980996390811"

    base_url = f'https://{snap_secrets["domain"]}/v1/segments/{erasure_segment}/users'
    response = requests.request(
        "POST",
        base_url,
        # requires auth token generated from Postman
        headers={"Authorization": f"Bearer {snap_secrets['access_token']}"},
        data=payload,
    )
    assert response.ok

    yield {}


@pytest.fixture
def snap_runner(
    db,
    cache,
    snap_secrets,
    snap_external_references,
    snap_erasure_external_references,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "snap",
        snap_secrets,
        external_references=snap_external_references,
        erasure_external_references=snap_erasure_external_references,
    )
