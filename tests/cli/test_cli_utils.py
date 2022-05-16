# pylint: disable=missing-docstring, redefined-outer-name
import pytest
from requests_mock import Mocker

import fidesctl.cli.utils as utils
from fidesapi.routes.util import API_PREFIX


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
