# pylint: disable=missing-docstring, redefined-outer-name
from json import dumps
from os import getenv

import pytest
from starlette.testclient import TestClient

from fides.api.ctl.routes.generate import GenerateResponse
from fides.api.ctl.routes.util import API_PREFIX
from fides.ctl.core.config import FidesctlConfig

EXTERNAL_CONFIG_BODY = {
    "aws": {
        "region_name": getenv("AWS_DEFAULT_REGION", ""),
        "aws_access_key_id": getenv("AWS_ACCESS_KEY_ID", ""),
        "aws_secret_access_key": getenv("AWS_SECRET_ACCESS_KEY", ""),
    },
    "db": {
        "connection_string": "postgresql+psycopg2://postgres:postgres@postgres-test:5432/postgres_example?"
    },
    "okta": {
        "orgUrl": "https://dev-78908748.okta.com",
        "token": getenv("OKTA_CLIENT_TOKEN", ""),
    },
}


@pytest.mark.external
@pytest.mark.parametrize(
    "generate_type, generate_target",
    [("systems", "aws"), ("systems", "okta"), ("datasets", "db")],
)
def test_generate(
    test_config: FidesctlConfig,
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
        headers=test_config.user.request_headers,
        data=dumps(data),
    )
    generate_response = GenerateResponse.parse_raw(response.text)
    assert len(generate_response.generate_results) > 0
    assert response.status_code == 200
