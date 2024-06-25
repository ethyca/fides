# pylint: disable=missing-docstring, redefined-outer-name
import os
from unittest.mock import patch

import click
import pytest

import fides.cli.utils as utils
from fides.config import FidesConfig
from tests.ctl.conftest import orig_requests_get


@pytest.mark.unit
def test_check_server_bad_ping(test_client, monkeypatch) -> None:
    """Check for an exception if the server isn't up."""
    import requests

    monkeypatch.setattr(requests, "get", orig_requests_get)
    with pytest.raises(SystemExit):
        utils.check_server("foo", "http://fake_address:8080")
    monkeypatch.setattr(requests, "get", test_client.get)


@pytest.mark.unit
@pytest.mark.parametrize(
    "server_version, cli_version, expected_result",
    [
        ("1.6.0+7.ge953df5", "1.6.0+7.ge953df5", True),
        ("1.6.0+7.ge953df5", "1.6.0+9.ge953df5", False),
        (
            "1.6.0+7.ge953df5",
            "1.6.0+7.ge953df5.dirty",
            True,
        ),
        (
            "1.6.0+7.ge953df5.dirty",
            "1.6.0+7.ge953df5",
            True,
        ),
    ],
)
def test_check_server_version_comparisons(
    server_version: str,
    cli_version: str,
    expected_result: str,
) -> None:
    """Check that version comparison works."""
    actual_result = utils.compare_application_versions(server_version, cli_version)
    assert expected_result == actual_result


@pytest.mark.unit
class TestHandleDatabaseCredentialsOptions:
    def test_neither_option_supplied_raises(
        self,
        test_config: FidesConfig,
    ) -> None:
        "Check for an exception if neither option is supplied."
        with pytest.raises(click.UsageError):
            input_connection_string = ""
            input_credentials_id = ""
            utils.handle_database_credentials_options(
                fides_config=test_config,
                connection_string=input_connection_string,
                credentials_id=input_credentials_id,
            )

    def test_both_options_supplied_raises(
        self,
        test_config: FidesConfig,
    ) -> None:
        "Check for an exception if both options are supplied."
        with pytest.raises(click.UsageError):
            input_connection_string = "my_connection_string"
            input_credentials_id = "postgres_1"
            utils.handle_database_credentials_options(
                fides_config=test_config,
                connection_string=input_connection_string,
                credentials_id=input_credentials_id,
            )

    def test_config_does_not_exist_raises(
        self,
        test_config: FidesConfig,
    ) -> None:
        "Check for an exception if credentials dont exist"
        with pytest.raises(click.UsageError):
            input_connection_string = ""
            input_credentials_id = "UNKNOWN"
            utils.handle_database_credentials_options(
                fides_config=test_config,
                connection_string=input_connection_string,
                credentials_id=input_credentials_id,
            )

    def test_returns_input_connection_string(
        self,
        test_config: FidesConfig,
    ) -> None:
        "Checks if expected connection string is returned from input"
        input_connection_string = "my_connection_string"
        input_credentials_id = ""
        connection_string = utils.handle_database_credentials_options(
            fides_config=test_config,
            connection_string=input_connection_string,
            credentials_id=input_credentials_id,
        )
        assert connection_string == input_connection_string

    def test_returns_config_connection_string(
        self,
        test_config: FidesConfig,
    ) -> None:
        "Checks if expected connection string is returned from config"
        input_connection_string = ""
        input_credentials_id = "postgres_1"
        connection_string = utils.handle_database_credentials_options(
            fides_config=test_config,
            connection_string=input_connection_string,
            credentials_id=input_credentials_id,
        )
        assert (
            connection_string
            == "postgresql+psycopg2://postgres:fides@fides-db:5432/fides_test"
        )


def test_handle_okta_credentials_options_both_raises(
    test_config: FidesConfig,
) -> None:
    "Check for an exception if both credentials options are supplied."
    with pytest.raises(click.UsageError):
        input_org_url = "hello.com"
        input_token = "abcd12345"
        input_credentials_id = "okta_1"
        utils.handle_okta_credentials_options(
            fides_config=test_config,
            token=input_token,
            org_url=input_org_url,
            credentials_id=input_credentials_id,
        )


@pytest.mark.unit
class TestHandleOktaCredentialsOptions:
    def test_config_dne_raises(
        self,
        test_config: FidesConfig,
    ) -> None:
        "Check for an exception if credentials dont exist"
        with pytest.raises(click.UsageError):
            input_org_url = ""
            input_token = ""
            input_credentials_id = "UNKNOWN"
            utils.handle_okta_credentials_options(
                fides_config=test_config,
                token=input_token,
                org_url=input_org_url,
                credentials_id=input_credentials_id,
            )

    def test_returns_config_dict(
        self,
        test_config: FidesConfig,
    ) -> None:
        "Check for an exception if credentials dont exist"
        input_org_url = ""
        input_token = ""
        input_credentials_id = "okta_1"
        okta_config = utils.handle_okta_credentials_options(
            fides_config=test_config,
            token=input_token,
            org_url=input_org_url,
            credentials_id=input_credentials_id,
        )
        assert okta_config.model_dump() == {
            "orgUrl": "https://dev-78908748.okta.com",
            "token": "redacted_override_in_tests",
        }

    def test_returns_input_dict(
        self,
        test_config: FidesConfig,
    ) -> None:
        "Check for an exception if credentials dont exist"
        input_org_url = "hello.com"
        input_token = "abcd12345"
        input_credentials_id = ""
        okta_config = utils.handle_okta_credentials_options(
            fides_config=test_config,
            token=input_token,
            org_url=input_org_url,
            credentials_id=input_credentials_id,
        )
        assert okta_config.model_dump() == {
            "orgUrl": input_org_url,
            "token": input_token,
        }


@pytest.mark.unit
class TestHandleAWSCredentialsOptions:
    def test_both_raises(
        self,
        test_config: FidesConfig,
    ) -> None:
        "Check for an exception if both credentials options are supplied."
        with pytest.raises(click.UsageError):
            input_access_key = "access_key"
            input_access_key_id = "access_key_id"
            input_region = "us-east-1"
            input_credentials_id = "aws_1"
            utils.handle_aws_credentials_options(
                fides_config=test_config,
                access_key_id=input_access_key_id,
                secret_access_key=input_access_key,
                session_token=None,
                region=input_region,
                credentials_id=input_credentials_id,
            )

    def test_config_dne_raises(
        self,
        test_config: FidesConfig,
    ) -> None:
        "Check for an exception if credentials dont exist"
        with pytest.raises(click.UsageError):
            input_access_key = ""
            input_access_key_id = ""
            input_region = ""
            input_credentials_id = "UNKNOWN"
            utils.handle_aws_credentials_options(
                fides_config=test_config,
                access_key_id=input_access_key_id,
                secret_access_key=input_access_key,
                session_token=None,
                region=input_region,
                credentials_id=input_credentials_id,
            )

    def test_returns_config_dict(
        self,
        test_config: FidesConfig,
    ) -> None:
        "Verify credentials specified in config dict"
        input_access_key = ""
        input_access_key_id = ""
        input_region = ""
        input_credentials_id = "aws_1"
        aws_config = utils.handle_aws_credentials_options(
            fides_config=test_config,
            access_key_id=input_access_key_id,
            secret_access_key=input_access_key,
            session_token=None,
            region=input_region,
            credentials_id=input_credentials_id,
        )

        assert aws_config.model_dump(mode="json") == {
            "aws_access_key_id": "redacted_id_override_in_tests",
            "aws_secret_access_key": "redacted_override_in_tests",
            "region_name": "us-east-1",
            "aws_session_token": None,
        }

    def test_returns_input_dict(
        self,
        test_config: FidesConfig,
    ) -> None:
        "Verify credentials specified directly as an input args"
        input_access_key = "access_key"
        input_access_key_id = "access_key_id"
        input_region = "us-east-1"
        input_credentials_id = ""
        aws_config = utils.handle_aws_credentials_options(
            fides_config=test_config,
            access_key_id=input_access_key_id,
            secret_access_key=input_access_key,
            session_token=None,
            region=input_region,
            credentials_id=input_credentials_id,
        )
        assert aws_config.model_dump(mode="json") == {
            "aws_access_key_id": input_access_key_id,
            "aws_secret_access_key": input_access_key,
            "region_name": input_region,
            "aws_session_token": None,
        }

    def test_session_token_temporary_credentials(
        self,
        test_config: FidesConfig,
    ) -> None:
        "Verify AWS temporary credential support, i.e. passing a session token"
        input_access_key = "access_key"
        input_access_key_id = "access_key_id"
        input_region = "us-east-1"
        session_token = "session_token"
        input_credentials_id = ""
        aws_config = utils.handle_aws_credentials_options(
            fides_config=test_config,
            access_key_id=input_access_key_id,
            secret_access_key=input_access_key,
            session_token=session_token,
            region=input_region,
            credentials_id=input_credentials_id,
        )
        assert aws_config.model_dump(mode="json") == {
            "aws_access_key_id": input_access_key_id,
            "aws_secret_access_key": input_access_key,
            "region_name": input_region,
            "aws_session_token": session_token,
        }


@pytest.mark.unit
class TestHandleBigQueryCredentialsOptions:
    def test_multiple_config_options_raises(
        self,
        test_config: FidesConfig,
    ) -> None:
        with pytest.raises(click.UsageError):
            utils.handle_bigquery_config_options(
                fides_config=test_config,
                dataset="dataset",
                keyfile_path="path/to/keyfile.json",
                credentials_id="bigquery_1",
            )

    def test_missing_credential_id(
        self,
        test_config: FidesConfig,
    ) -> None:
        with pytest.raises(click.UsageError):
            utils.handle_bigquery_config_options(
                fides_config=test_config,
                dataset="dataset",
                keyfile_path="",
                credentials_id="UNKNOWN",
            )
