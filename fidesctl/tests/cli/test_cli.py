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
def test_init(test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(cli, ["init"])
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.unit
def test_parse(test_config_path: str, test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(
        cli, ["-f", test_config_path, "parse", "demo_resources/"]
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_reset_db(test_config_path: str, test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(cli, ["-f", test_config_path, "reset-db", "-y"])
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_init_db(test_config_path: str, test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(cli, ["-f", test_config_path, "init-db"])
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_apply(test_config_path: str, test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(
        cli, ["-f", test_config_path, "apply", "demo_resources/"]
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_dry_apply(test_config_path: str, test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(
        cli, ["-f", test_config_path, "apply", "--dry", "demo_resources/"]
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_diff_apply(test_config_path: str, test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(
        cli, ["-f", test_config_path, "apply", "--diff", "demo_resources/"]
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_dry_diff_apply(test_config_path: str, test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(
        cli, ["-f", test_config_path, "apply", "--dry", "--diff", "demo_resources/"]
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_get(test_config_path: str, test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(
        cli,
        ["-f", test_config_path, "get", "data_category", "user.provided.identifiable"],
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_ls(test_config_path: str, test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(cli, ["-f", test_config_path, "ls", "system"])
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_evaluate_with_declaration_pass(
    test_config_path: str, test_cli_runner: CliRunner
):
    result = test_cli_runner.invoke(
        cli,
        [
            "-f",
            test_config_path,
            "evaluate",
            "tests/data/passing_declaration_taxonomy.yml",
        ],
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_evaluate_demo_resources_pass(
    test_config_path: str, test_cli_runner: CliRunner
):
    result = test_cli_runner.invoke(
        cli,
        ["-f", test_config_path, "evaluate", "demo_resources/"],
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_local_evaluate(test_invalid_config_path: str, test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(
        cli,
        [
            "--local",
            "-f",
            test_invalid_config_path,
            "evaluate",
            "tests/data/passing_declaration_taxonomy.yml",
        ],
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
            "-k",
            "primary_privacy_policy",
            "tests/data/passing_declaration_taxonomy.yml",
        ],
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_evaluate_with_declaration_failed(
    test_config_path: str, test_cli_runner: CliRunner
):
    result = test_cli_runner.invoke(
        cli,
        [
            "-f",
            test_config_path,
            "evaluate",
            "tests/data/failing_declaration_taxonomy.yml",
        ],
    )
    print(result.output)
    assert result.exit_code == 1


@pytest.mark.integration
def test_evaluate_with_dataset_failed(
    test_config_path: str, test_cli_runner: CliRunner
):
    result = test_cli_runner.invoke(
        cli,
        ["-f", test_config_path, "evaluate", "tests/data/failing_dataset_taxonomy.yml"],
    )
    print(result.output)
    assert result.exit_code == 1


@pytest.mark.integration
def test_evaluate_with_dataset_field_failed(
    test_config_path: str, test_cli_runner: CliRunner
):
    result = test_cli_runner.invoke(
        cli,
        [
            "-f",
            test_config_path,
            "evaluate",
            "tests/data/failing_dataset_collection_taxonomy.yml",
        ],
    )
    print(result.output)
    assert result.exit_code == 1


@pytest.mark.integration
def test_evaluate_with_dataset_collection_failed(
    test_config_path: str, test_cli_runner: CliRunner
):
    result = test_cli_runner.invoke(
        cli,
        [
            "-f",
            test_config_path,
            "evaluate",
            "tests/data/failing_dataset_field_taxonomy.yml",
        ],
    )
    print(result.output)
    assert result.exit_code == 1


@pytest.mark.integration
def test_nested_field_fails_evaluation(
    test_config_path: str, test_cli_runner: CliRunner
):
    """
    Tests a taxonomy that is rigged to fail only due to
    one of the nested fields violating the policy. Test
    will fail if the nested field is not discovered.
    """
    result = test_cli_runner.invoke(
        cli,
        [
            "-f",
            test_config_path,
            "evaluate",
            "tests/data/failing_nested_dataset.yml",
        ],
    )
    print(result.output)
    assert result.exit_code == 1
