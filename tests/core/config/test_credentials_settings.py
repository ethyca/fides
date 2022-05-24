# pylint: disable=missing-docstring, redefined-outer-name
import os
from typing import Dict
from unittest.mock import patch

import pytest

from fidesctl.core.config.credentials_settings import merge_credentials_environment


@patch.dict(
    os.environ,
    {
        "FIDESCTL__CREDENTIALS__POSTGRES_1__CONNECTION_STRING": "postgresql+psycopg2://fidesctl:env_variable.com:5439/fidesctl_test",
        "FIDESCTL__CREDENTIALS__AWS_ACCOUNT_1__REGION": "us-east-1",
        "FIDESCTL__CREDENTIALS__AWS_ACCOUNT_1__ACCESS_KEY_ID": "ACCESS_KEY_ID_1",
        "FIDESCTL__CREDENTIALS__AWS_ACCOUNT_1__ACCESS_KEY": "ACCESS_KEY_1",
    },
    clear=True,
)
@pytest.mark.unit
def test_merge_credentials_environment() -> None:
    "Test merging environment variables into a settings dict."
    credentials_dict: Dict = dict()
    merge_credentials_environment(credentials_dict)

    assert credentials_dict == {
        "postgres_1": {
            "connection_string": "postgresql+psycopg2://fidesctl:env_variable.com:5439/fidesctl_test"
        },
        "aws_account_1": {
            "region": "us-east-1",
            "access_key_id": "ACCESS_KEY_ID_1",
            "access_key": "ACCESS_KEY_1",
        },
    }


@patch.dict(
    os.environ,
    {
        "FIDESCTL__CREDENTIALS__POSTGRES_1__CONNECTION_STRING": "postgresql+psycopg2://fidesctl:env_variable.com:5439/fidesctl_test",
        "FIDESCTL__CREDENTIALS__AWS_ACCOUNT_1__ACCESS_KEY_ID": "ACCESS_KEY_ID_1",
        "FIDESCTL__CREDENTIALS__AWS_ACCOUNT_1__ACCESS_KEY": "ACCESS_KEY_1",
    },
    clear=True,
)
@pytest.mark.unit
def test_merge_credentials_environment_mixed_configs() -> None:
    "Test that merging environment variables works with mixed configs"
    credentials_dict = {"aws_account_1": {"region": "us-east-1"}}
    merge_credentials_environment(credentials_dict)

    assert credentials_dict == {
        "postgres_1": {
            "connection_string": "postgresql+psycopg2://fidesctl:env_variable.com:5439/fidesctl_test"
        },
        "aws_account_1": {
            "region": "us-east-1",
            "access_key_id": "ACCESS_KEY_ID_1",
            "access_key": "ACCESS_KEY_1",
        },
    }


@patch.dict(
    os.environ,
    {
        "FIDESCTL__CREDENTIALS__AWS_ACCOUNT_1__ACCESS_KEY_ID": "ACCESS_KEY_ID_OVERRIDE",
        "FIDESCTL__CREDENTIALS__AWS_ACCOUNT_1__ACCESS_KEY": "ACCESS_KEY_OVERRIDE",
    },
    clear=True,
)
@pytest.mark.unit
def test_merge_credentials_environment_environment_override() -> None:
    "Test merging environment variable works as an override."
    credentials_dict = {
        "aws_account_1": {
            "region": "us-east-1",
            "access_key_id": "ACCESS_KEY_ID_1",
            "access_key": "ACCESS_KEY_1",
        }
    }
    merge_credentials_environment(credentials_dict)

    assert credentials_dict == {
        "aws_account_1": {
            "region": "us-east-1",
            "access_key_id": "ACCESS_KEY_ID_OVERRIDE",
            "access_key": "ACCESS_KEY_OVERRIDE",
        }
    }
