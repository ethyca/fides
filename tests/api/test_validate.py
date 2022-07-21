# pylint: disable=missing-docstring, redefined-outer-name
from base64 import b64decode
from json import dumps, loads
from os import getenv

import pytest
from starlette.testclient import TestClient

from fidesctl.api.routes.util import API_PREFIX
from fidesctl.api.routes.validate import ValidateResponse
from fidesctl.core.config import FidesctlConfig

EXTERNAL_CONFIG_BODY = {
    "aws": {
        "region_name": getenv("AWS_DEFAULT_REGION", ""),
        "aws_access_key_id": getenv("AWS_ACCESS_KEY_ID", ""),
        "aws_secret_access_key": getenv("AWS_SECRET_ACCESS_KEY", ""),
    },
    "bigquery": {
        "dataset": "fidesopstest",
        "keyfile_creds": loads(
            b64decode(getenv("BIGQUERY_CONFIG", "e30=").encode("utf-8")).decode("utf-8")
        ),
    },
    "okta": {
        "orgUrl": "https://dev-78908748.okta.com",
        "token": getenv("OKTA_CLIENT_TOKEN", ""),
    },
}


@pytest.mark.external
@pytest.mark.parametrize("validate_target", ["aws", "okta", "bigquery"])
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
    "bigquery": {
        "dataset": "fidesopstest",
        "keyfile_creds": loads(
            b64decode(getenv("BIGQUERY_CONFIG", "e30=").encode("utf-8")).decode("utf-8")
        ),
    },
}

EXTERNAL_FAILURE_CONFIG_BODY["bigquery"]["keyfile_creds"][
    "project_id"
] = "INVALID_PROJECT_ID"

EXPECTED_FAILURE_MESSAGES = {
    "aws": "Authentication failed validating config. The security token included in the request is invalid.",
    "okta": "Authentication failed validating config. Invalid token provided",
    "bigquery": "Unexpected failure validating config. Invalid project ID 'INVALID_PROJECT_ID'. Project IDs must contain 6-63 lowercase letters, digits, or dashes. Some project IDs also include domain name separated by a colon. IDs must start with a letter and may not end with a dash.",
}


@pytest.mark.external
@pytest.mark.parametrize("validate_target", ["aws", "okta", "bigquery"])
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
