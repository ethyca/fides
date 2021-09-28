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


@pytest.mark.unit
def test_parse(test_config_path: str, test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(
        cli, ["-f", test_config_path, "parse", "default_taxonomy/"]
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_apply(test_config_path: str, test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(cli, ["-f", test_config_path, "apply", "default_taxonomy/"])
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_dry_apply(test_config_path: str, test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(
        cli, ["-f", test_config_path, "apply", "default_taxonomy/", "--dry"]
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_diff_apply(test_config_path: str, test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(
        cli, ["-f", test_config_path, "apply", "default_taxonomy/", "--diff"]
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_dry_diff_apply(test_config_path: str, test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(
        cli, ["-f", test_config_path, "apply", "default_taxonomy/", "--dry", "--diff"]
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_get(test_config_path: str, test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(
        cli, ["-f", test_config_path, "get", "data_category", "user.provided.identifiable"]
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_ls(test_config_path: str, test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(cli, ["-f", test_config_path, "ls", "system"])
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_generate_dataset(test_config_path: str, test_cli_runner: CliRunner):
    assert True


@pytest.mark.integration
def test_evaluate_pass(test_config_path: str, test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(
        cli,
        ["-f", test_config_path, "evaluate", "tests/data/passing_taxonomy.yml"],
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_evaluate_with_key_pass(test_config_path: str, test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(
        cli,
        [
            "-f",
            test_config_path,
            "evaluate",
            "tests/data/passing_taxonomy.yml",
            "-k",
            "primary_privacy_policy",
        ],
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_evaluate_failed(test_config_path: str, test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(
        cli,
        ["-f", test_config_path, "evaluate", "tests/data/failing_taxonomy.yml"],
    )
    print(result.output)
    assert result.exit_code == 1
