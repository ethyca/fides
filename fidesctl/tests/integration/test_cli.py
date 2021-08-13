import pytest
from click.testing import CliRunner

from fidesctl.cli import cli


def test_ping(test_config_path):
    runner = CliRunner()
    result = runner.invoke(cli, ["ping", "-f", test_config_path])

    print(result.exc_info)
    assert result.exit_code == 0
