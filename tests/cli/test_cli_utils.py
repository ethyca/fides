# pylint: disable=missing-docstring, redefined-outer-name
import click
import pytest
from requests_mock import Mocker

import fidesctl.cli.utils as utils
from fidesapi.routes.util import API_PREFIX
from fidesctl.core.config import FidesctlConfig


@pytest.mark.unit
def test_check_server_bad_ping() -> None:
    "Check for an exception if the server isn't up."
    with pytest.raises(SystemExit):
        utils.check_server("foo", "http://fake_address:8080")


@pytest.mark.unit
@pytest.mark.parametrize(
    "server_version, cli_version, expected_output, quiet",
    [
        ("1.6.0+7.ge953df5", "1.6.0+7.ge953df5", "application versions match", False),
        ("1.6.0+7.ge953df5", "1.6.0+9.ge953df5", "Mismatched versions!", False),
        (
            "1.6.0+7.ge953df5",
            "1.6.0+7.ge953df5.dirty",
            "application versions match",
            False,
        ),
        (
            "1.6.0+7.ge953df5.dirty",
            "1.6.0+7.ge953df5",
            "application versions match",
            False,
        ),
        ("1.6.0+7.ge953df5", "1.6.0+7.ge953df5.dirty", None, True),
    ],
)
def test_check_server_version_comparisons(
    requests_mock: Mocker,
    capsys: pytest.CaptureFixture,
    server_version: str,
    cli_version: str,
    expected_output: str,
    quiet: bool,
) -> None:
    """Check that comparing versions works"""
    fake_url = "http://fake_address:8080"
    requests_mock.get(
        f"{fake_url}{API_PREFIX}/health", json={"version": server_version}
    )
    utils.check_server(cli_version, "http://fake_address:8080", quiet=quiet)
    captured = capsys.readouterr()
    if expected_output is None:
        assert captured.out == ""
    else:
        assert expected_output in captured.out


@pytest.mark.unit
class TestHandleDatabaseCredentialsOptions:
    def test_neither_option_supplied_raises(
        self,
        test_config: FidesctlConfig,
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
        test_config: FidesctlConfig,
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
        test_config: FidesctlConfig,
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
        test_config: FidesctlConfig,
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
        test_config: FidesctlConfig,
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
            == "postgresql+psycopg2://postgres:fidesctl@fidesctl-db:5432/fidesctl_test"
        )


def test_handle_okta_credentials_options_both_raises(
    test_config: FidesctlConfig,
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
        test_config: FidesctlConfig,
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
        test_config: FidesctlConfig,
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
        assert okta_config == {
            "orgUrl": "https://dev-78908748.okta.com",
            "token": "redacted_override_in_tests",
        }

    def test_returns_input_dict(
        self,
        test_config: FidesctlConfig,
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
        assert okta_config == {"orgUrl": input_org_url, "token": input_token}


@pytest.mark.unit
class TestHandleAWSCredentialsOptions:
    def test_both_raises(
        self,
        test_config: FidesctlConfig,
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
                region=input_region,
                credentials_id=input_credentials_id,
            )

    def test_config_dne_raises(
        self,
        test_config: FidesctlConfig,
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
                region=input_region,
                credentials_id=input_credentials_id,
            )

    def test_returns_config_dict(
        self,
        test_config: FidesctlConfig,
    ) -> None:
        "Check for an exception if credentials dont exist"
        input_access_key = ""
        input_access_key_id = ""
        input_region = ""
        input_credentials_id = "aws_1"
        aws_config = utils.handle_aws_credentials_options(
            fides_config=test_config,
            access_key_id=input_access_key_id,
            secret_access_key=input_access_key,
            region=input_region,
            credentials_id=input_credentials_id,
        )

        assert aws_config == {
            "aws_access_key_id": "redacted_id_override_in_tests",
            "aws_secret_access_key": "redacted_override_in_tests",
            "region_name": "us-east-1",
        }

    def test_returns_input_dict(
        self,
        test_config: FidesctlConfig,
    ) -> None:
        "Check for an exception if credentials dont exist"
        input_access_key = "access_key"
        input_access_key_id = "access_key_id"
        input_region = "us-east-1"
        input_credentials_id = ""
        aws_config = utils.handle_aws_credentials_options(
            fides_config=test_config,
            access_key_id=input_access_key_id,
            secret_access_key=input_access_key,
            region=input_region,
            credentials_id=input_credentials_id,
        )
        assert aws_config == {
            "aws_access_key_id": input_access_key_id,
            "aws_secret_access_key": input_access_key,
            "region_name": input_region,
        }
