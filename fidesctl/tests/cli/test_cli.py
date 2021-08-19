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
def test_dry_evaluate_registry_success(
    test_config_path: str, test_cli_runner: CliRunner
):
    result = test_cli_runner.invoke(
        cli,
        ["-f", test_config_path, "dry-evaluate", "data/sample/", "demo_registry"],
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_dry_evaluate_system_success(test_config_path: str, test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(
        cli,
        ["-f", test_config_path, "dry-evaluate", "data/sample/", "demoPassingSystem"],
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_dry_evaluate_system_failing(test_config_path: str, test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(
        cli,
        ["-f", test_config_path, "dry-evaluate", "data/sample/", "demoFailingSystem"],
    )
    print(result.output)
    assert result.exit_code == 1


@pytest.mark.integration
def test_evaluate_registry_success(test_config_path: str, test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(
        cli,
        ["-f", test_config_path, "evaluate", "registry", "default_registry"],
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_evaluate_system_success(test_config_path: str, test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(
        cli,
        ["-f", test_config_path, "evaluate", "system", "demoPassingSystem"],
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_evaluate_system_failing(test_config_path: str, test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(
        cli,
        ["-f", test_config_path, "evaluate", "system", "demoFailingSystem"],
    )
    print(result.output)
    assert result.exit_code == 1
