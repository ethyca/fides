# pylint: disable=missing-docstring, redefined-outer-name
from json import dumps
from os import getenv
from typing import Generator

import pytest
from starlette.testclient import TestClient

from fidesapi import main
from fidesapi.routes.generate import GenerateResponse
from fidesapi.routes.util import API_PREFIX, obscure_string
from fidesctl.core.config import FidesctlConfig


@pytest.fixture()
def test_client() -> Generator:
    """Starlette test client fixture. Easier to use mocks with when testing out API calls"""
    with TestClient(main.app) as test_client:
        yield test_client


EXTERNAL_CONFIG_BODY = {
    "aws": {
        "region_name": getenv("AWS_DEFAULT_REGION", ""),
        "aws_access_key_id": obscure_string(getenv("AWS_ACCESS_KEY_ID", "")),
        "aws_secret_access_key": obscure_string(getenv("AWS_SECRET_ACCESS_KEY", "")),
    }
}


@pytest.mark.external
@pytest.mark.parametrize("generate_type, generate_target", [("systems", "aws")])
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
