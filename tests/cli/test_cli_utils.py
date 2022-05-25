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


def test_handle_database_credentials_options_neither_raises(
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


def test_handle_database_credentials_options_both_raises(
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


def test_handle_database_credentials_options_credentials_dne_raises(
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


def test_handle_database_credentials_options_returns_connection_string(
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


def test_handle_database_credentials_returns_connection_string(
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
