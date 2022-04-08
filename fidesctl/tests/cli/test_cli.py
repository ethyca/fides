import pytest
from click.testing import CliRunner

from fidesctl.cli import cli

OKTA_URL = "https://dev-78908748.okta.com"


@pytest.fixture()
def test_cli_runner() -> CliRunner:
    runner = CliRunner()
    yield runner


@pytest.mark.integration
def test_init(test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(
        cli, ["init"], env={"FIDESCTL__USER__ANALYTICS_OPT_OUT": "true"}
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.unit
def test_webserver():
    """
    This is specifically meant to catch when the webserver command breaks,
    without spinning up an additional instance.
    """
    from fidesapi.main import start_webserver

    assert True


@pytest.mark.unit
def test_parse(test_config_path: str, test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(
        cli, ["-f", test_config_path, "parse", "demo_resources/"]
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_reset_db(test_config_path: str, test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(cli, ["-f", test_config_path, "db", "reset", "-y"])
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_init_db(test_config_path: str, test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(cli, ["-f", test_config_path, "db", "init"])
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
@pytest.mark.parametrize(
    "export_resource", ["system", "dataset", "organization", "datamap"]
)
def test_export_resources(
    test_config_path: str, test_cli_runner: CliRunner, export_resource: str
):
    """
    Tests that each resource is successfully exported
    """

    result = test_cli_runner.invoke(
        cli,
        [
            "-f",
            test_config_path,
            "export",
            export_resource,
            "demo_resources/",
            "--dry",
        ],
    )
    assert result.exit_code == 0


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


@pytest.mark.integration
def test_generate_dataset_db(test_config_path: str, test_cli_runner: CliRunner, tmpdir):
    tmp_file = tmpdir.join("dataset.yml")
    result = test_cli_runner.invoke(
        cli,
        [
            "-f",
            test_config_path,
            "generate",
            "dataset",
            "db",
            "postgresql+psycopg2://postgres:fidesctl@fidesctl-db:5432/fidesctl_test",
            f"{tmp_file}",
        ],
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_scan_dataset_db(test_config_path: str, test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(
        cli,
        [
            "-f",
            test_config_path,
            "scan",
            "dataset",
            "db",
            "postgresql+psycopg2://postgres:fidesctl@fidesctl-db:5432/fidesctl_test",
            "--coverage-threshold",
            "0",
        ],
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.external
def test_generate_system_aws(test_config_path: str, test_cli_runner: CliRunner, tmpdir):
    tmp_file = tmpdir.join("system.yml")
    result = test_cli_runner.invoke(
        cli,
        ["-f", test_config_path, "generate", "system", "aws", f"{tmp_file}"],
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.external
def test_scan_system_aws(test_config_path: str, test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(
        cli,
        [
            "-f",
            test_config_path,
            "scan",
            "system",
            "aws",
            "--coverage-threshold",
            "0",
        ],
    )
    print(result.output)
    assert result.exit_code == 0

@pytest.mark.external
def test_generate_dataset_okta(test_config_path: str, test_cli_runner: CliRunner, tmpdir):
    tmp_file = tmpdir.join("dataset.yml")
    result = test_cli_runner.invoke(
        cli,
        ["-f", test_config_path, "generate", "dataset", "okta", OKTA_URL,f"{tmp_file}"],
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.external
def test_scan_system_okta(test_config_path: str, test_cli_runner: CliRunner):
    result = test_cli_runner.invoke(
        cli,
        [
            "-f",
            test_config_path,
            "scan",
            "dataset",
            "okta",
            OKTA_URL,
            "--coverage-threshold",
            "0",
        ],
    )
    print(result.output)
    assert result.exit_code == 0
