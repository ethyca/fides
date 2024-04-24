from typing import Any, Dict, Generator

import pydash
import pytest
import requests
import json
import hashlib
import urllib

from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("marigold_engage")

def payload_signature(secrets: Dict[str, Any], stringified_payload: str):
    values = [secrets["secret"], secrets["api_key"], "json", stringified_payload]
    return md5_any("".join(values)).hexdigest()

def md5_any(value_to_MD5) -> str:
    return hashlib.md5(value_to_MD5.encode())

def url_encode(value_to_encode) -> str:
    return urllib.parse.quote_plus(value_to_encode)


@pytest.fixture(scope="session")
def marigold_engage_secrets(saas_config) -> Dict[str, Any]:
    return {
        "domain": pydash.get(saas_config, "marigold_engage.domain")
        or secrets["domain"],
        "api_key": pydash.get(saas_config, "marigold_engage.api_key")
        or secrets["api_key"],
        "secret": pydash.get(saas_config, "marigold_engage.secret")
        or secrets["secret"],
    }


@pytest.fixture(scope="session")
def marigold_engage_identity_email(saas_config) -> str:
    return (
        pydash.get(saas_config, "marigold_engage.identity_email")
        or secrets["identity_email"]
    )


@pytest.fixture
def marigold_engage_erasure_identity_email() -> str:
    return generate_random_email()


@pytest.fixture
def marigold_engage_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def marigold_engage_erasure_external_references() -> Dict[str, Any]:
    return {}


@pytest.fixture
def marigold_engage_erasure_data(
    marigold_engage_secrets,
    marigold_engage_erasure_identity_email: str,
) -> Generator:
    # create the data needed for erasure tests here
    ### I need to post to the user endpoint with a randomized email e.g. marigold_engage_erasure_identity_email [secrets["secret"]
    base_url = f'https://api.sailthru.com/user'
    # stringified_payload = json.dumps(payload, separators=(",", ":"))
    # url_safe_payload = url_encode(stringified_payload)
    # sig = payload_signature(marigold_engage_secrets, stringified_payload)
    email_test = "neilmarc@aol.com"
    email_prep = '{"id":"'+email_test+'"}'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
        }   
    ### sig prep
    sig_prep = marigold_engage_secrets["secret"]+marigold_engage_secrets["api_key"]+"json"+email_prep
    sig_chk = md5_any(sig_prep)
    md5_readable = sig_chk.hexdigest()
    ### end sig prep
    payload = {
        "api_key": marigold_engage_secrets["api_key"],
        "sig": md5_readable,
        "format": "json",
        "json": email_prep,
    }
    response = requests.request("POST", base_url, headers=headers, data=payload)
    assert response.ok

    # headers = {}
    # url = base_url + url_suffix
    # payload = ""
    params = {
        "api_key": marigold_engage_secrets["api_key"],
        "sig": md5_readable,
        "format": "json",
        "json": email_prep
    }
    response = requests.request("GET", base_url, params=params)
    import pdb
    pdb.set_trace()
    assert response.ok
    


    #yield {}


@pytest.fixture
def marigold_engage_runner(
    db,
    cache,
    marigold_engage_secrets,
    marigold_engage_external_references,
    marigold_engage_erasure_external_references,
) -> ConnectorRunner:
    return ConnectorRunner(
        db,
        cache,
        "marigold_engage",
        marigold_engage_secrets,
        external_references=marigold_engage_external_references,
        erasure_external_references=marigold_engage_erasure_external_references,
    )
