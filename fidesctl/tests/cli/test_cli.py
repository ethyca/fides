import pytest
from click.testing import CliRunner

from fidesctl.cli import cli


@pytest.fixture()
def test_cli_runner() -> CliRunner:
    runner = CliRunner()
    yield runner


@pytest.mark.integration
def test_ping(test_config_path, test_cli_runner):
    result = test_cli_runner.invoke(cli, ["-f", test_config_path, "ping"])

    print(result.exc_info)
    assert result.exit_code == 0
