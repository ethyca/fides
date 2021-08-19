import pytest
from click.testing import CliRunner

from fidesctl.cli import cli


@pytest.fixture()
def test_cli_runner() -> CliRunner:
    runner = CliRunner()
    yield runner


@pytest.mark.integration
def test_ping(test_config_path: str, test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(cli, ["-f", test_config_path, "ping"])
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_find(test_config_path: str, test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(
        cli, ["-f", test_config_path, "find", "system", "demoPassingSystem"]
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_delete(test_config_path: str, test_cli_runner: CliRunner):
    assert True


@pytest.mark.integration
def test_get(test_config_path: str, test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(
        cli, ["-f", test_config_path, "get", "organization", "1"]
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_show(test_config_path: str, test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(cli, ["-f", test_config_path, "show", "system"])
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_apply(test_config_path: str, test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(cli, ["-f", test_config_path, "apply", "data/"])
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_generate_dataset(test_config_path: str, test_cli_runner: CliRunner):
    assert True


@pytest.mark.integration
def test_failed_dry_evaluate(test_config_path: str, test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(
        cli,
        ["-f", test_config_path, "dry-evaluate", "data/sample/", "demoPassingSystem"],
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_success_dry_evaluate(test_config_path: str, test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(
        cli,
        ["-f", test_config_path, "dry-evaluate", "data/sample/", "demoFailingSystem"],
    )
    print(result.output)
    assert result.exit_code == 1


@pytest.mark.integration
def test_evaluate(test_config_path: str, test_cli_runner: CliRunner):
    assert True
