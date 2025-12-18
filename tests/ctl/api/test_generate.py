# pylint: disable=missing-docstring, redefined-outer-name
from base64 import b64decode
from json import dumps, loads
from os import getenv

import pytest
from starlette.testclient import TestClient

from fides.api.api.v1.endpoints.generate import GenerateResponse
from fides.api.util.endpoint_utils import API_PREFIX
from fides.config import FidesConfig

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
    "db": {
        "connection_string": "postgresql+psycopg2://postgres:postgres@postgres-test:5432/postgres_example?"
    },
    "okta": {
        "orgUrl": "https://dev-78908748.okta.com",
        "token": getenv("OKTA_CLIENT_TOKEN", ""),
    },
    "dynamodb": {
        "region_name": getenv("DYNAMODB_REGION", ""),
        "aws_access_key_id": getenv("DYNAMODB_ACCESS_KEY_ID", ""),
        "aws_secret_access_key": getenv("DYNAMODB_ACCESS_KEY", ""),
    },
}

EXTERNAL_FAILURE_CONFIG_BODY = {
    "aws": {
        "region_name": getenv("AWS_DEFAULT_REGION", ""),
        "aws_access_key_id": "ILLEGAL_ACCESS_KEY_ID",
        "aws_secret_access_key": "ILLEGAL_SECRET_ACCESS_KEY_ID",
    },
    "bigquery": {
        "dataset": "fidesopstest",
        "keyfile_creds": loads(
            b64decode(getenv("BIGQUERY_CONFIG", "e30=").encode("utf-8")).decode("utf-8")
        ),
    },
    "db": {
        "connection_string": "postgresql+psycopg2://postgres:postgres@postgres-test:5432/INVALID_DB"
    },
    "okta": {
        "orgUrl": "https://dev-78908748.okta.com",
        "token": "INVALID_TOKEN",
    },
    "dynamodb": {
        "region_name": getenv("DYNAMODB_REGION", ""),
        "aws_access_key_id": "ILLEGAL_ACCESS_KEY_ID",
        "aws_secret_access_key": "ILLEGAL_SECRET_ACCESS_KEY_ID",
    },
}
EXTERNAL_FAILURE_CONFIG_BODY["bigquery"]["keyfile_creds"][
    "project_id"
] = "INVALID_PROJECT_ID"

EXPECTED_FAILURE_MESSAGES = {
    "aws": "The security token included in the request is invalid.",
    "okta": "Invalid token provided",
    "db": 'FATAL:  database "INVALID_DB" does not exist\n\n(Background on this error at: https://sqlalche.me/e/14/e3q8)',
    "bigquery": "Invalid project ID 'INVALID_PROJECT_ID'. Project IDs must contain 6-63 lowercase letters, digits, or dashes. Some project IDs also include domain name separated by a colon. IDs must start with a letter and may not end with a dash.",
    "dynamodb": "The security token included in the request is invalid.",
}


@pytest.mark.external
@pytest.mark.parametrize(
    "generate_type, generate_target",
    [
        ("systems", "aws"),
        ("systems", "okta"),
        ("datasets", "db"),
        ("datasets", "bigquery"),
        ("datasets", "dynamodb"),
    ],
)
@pytest.mark.usefixtures("default_organization")
def test_generate(
    test_config: FidesConfig,
    generate_type: str,
    generate_target: str,
    test_client: TestClient,
) -> None:
    data = {
        "organization_key": "default_organization",
        "generate": {
            "config": EXTERNAL_CONFIG_BODY[generate_target],
            "target": generate_target,
            "type": generate_type,
        },
    }

    response = test_client.post(
        test_config.cli.server_url + API_PREFIX + "/generate/",
        headers=test_config.user.auth_header,
        data=dumps(data),
    )
    generate_response = GenerateResponse.parse_raw(response.text)
    assert len(generate_response.generate_results) > 0
    assert response.status_code == 200


@pytest.mark.external
@pytest.mark.parametrize(
    "generate_type, generate_target",
    [
        ("systems", "aws"),
        ("systems", "okta"),
        ("datasets", "db"),
        ("datasets", "bigquery"),
        ("datasets", "dynamodb"),
    ],
)
@pytest.mark.usefixtures("default_organization")
def test_generate_failure(
    test_config: FidesConfig,
    generate_type: str,
    generate_target: str,
    test_client: TestClient,
) -> None:
    data = {
        "organization_key": "default_organization",
        "generate": {
            "config": EXTERNAL_FAILURE_CONFIG_BODY[generate_target],
            "target": generate_target,
            "type": generate_type,
        },
    }

    response = test_client.post(
        test_config.cli.server_url + API_PREFIX + "/generate/",
        headers=test_config.user.auth_header,
        data=dumps(data),
    )

    actual_failure_message = loads(response.text)["detail"]
    print(actual_failure_message)
    assert EXPECTED_FAILURE_MESSAGES[generate_target] in actual_failure_message
