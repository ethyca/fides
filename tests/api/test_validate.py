# pylint: disable=missing-docstring, redefined-outer-name
from json import dumps
from os import getenv

import pytest
from starlette.testclient import TestClient

from fidesapi.routes.util import API_PREFIX
from fidesapi.routes.validate import ValidateResponse
from fidesctl.core.config import FidesctlConfig

EXTERNAL_CONFIG_BODY = {
    "aws": {
        "region_name": getenv("AWS_DEFAULT_REGION", ""),
        "aws_access_key_id": getenv("AWS_ACCESS_KEY_ID", ""),
        "aws_secret_access_key": getenv("AWS_SECRET_ACCESS_KEY", ""),
    },
    "okta": {
        "orgUrl": "https://dev-78908748.okta.com",
        "token": getenv("OKTA_CLIENT_TOKEN", ""),
    },
}


@pytest.mark.external
@pytest.mark.parametrize("validate_target", ["aws", "okta"])
def test_validate_success(
    test_config: FidesctlConfig,
    validate_target: str,
    test_client: TestClient,
) -> None:

    data = {
        "config": EXTERNAL_CONFIG_BODY[validate_target],
        "target": validate_target,
    }

    response = test_client.post(
        test_config.cli.server_url + API_PREFIX + "/validate/",
        headers=test_config.user.request_headers,
        data=dumps(data),
    )

    validate_response = ValidateResponse.parse_raw(response.text)
    assert validate_response.status == "success"
    assert validate_response.message == "Config validation succeeded"
    assert response.status_code == 200


EXTERNAL_FAILURE_CONFIG_BODY = {
    "aws": {
        "region_name": getenv("AWS_DEFAULT_REGION", ""),
        "aws_access_key_id": "ILLEGAL_ACCESS_KEY_ID",
        "aws_secret_access_key": "ILLEGAL_SECRET_ACCESS_KEY_ID",
    },
    "okta": {
        "orgUrl": "https://dev-78908748.okta.com",
        "token": "INVALID_TOKEN",
    },
}

EXPECTED_FAILURE_MESSAGES = {
    "aws": "Authentication failed validating config. The security token included in the request is invalid.",
    "okta": "Authentication failed validating config. Invalid token provided",
}


@pytest.mark.external
@pytest.mark.parametrize("validate_target", ["aws", "okta"])
def test_validate_failure(
    test_config: FidesctlConfig,
    validate_target: str,
    test_client: TestClient,
) -> None:

    data = {
        "config": EXTERNAL_FAILURE_CONFIG_BODY[validate_target],
        "target": validate_target,
    }

    response = test_client.post(
        test_config.cli.server_url + API_PREFIX + "/validate/",
        headers=test_config.user.request_headers,
        data=dumps(data),
    )

    validate_response = ValidateResponse.parse_raw(response.text)
    assert validate_response.status == "failure"
    assert validate_response.message == EXPECTED_FAILURE_MESSAGES[validate_target]
    assert response.status_code == 200
