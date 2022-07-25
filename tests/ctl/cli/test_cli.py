# pylint: disable=missing-docstring, redefined-outer-name
import os
from base64 import b64decode
from json import dump, loads
from typing import Generator

import pytest
from click.testing import CliRunner
from git.repo import Repo
from py._path.local import LocalPath

from fidesctl.cli import cli

OKTA_URL = "https://dev-78908748.okta.com"


def git_reset(change_dir: str) -> None:
    """This fixture is used to reset the repo files to HEAD."""

    git_session = Repo().git()
    git_session.checkout("HEAD", change_dir)


@pytest.fixture()
def test_cli_runner() -> Generator:
    runner = CliRunner()
    yield runner


@pytest.mark.integration
def test_init(test_cli_runner: CliRunner) -> None:
    result = test_cli_runner.invoke(
        cli, ["init"], env={"FIDESCTL__USER__ANALYTICS_OPT_OUT": "true"}
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.unit
def test_webserver() -> None:
    """
    This is specifically meant to catch when the webserver command breaks,
    without spinning up an additional instance.
    """
    from fidesctl.api.main import start_webserver  # pylint: disable=unused-import

    assert True


@pytest.mark.unit
def test_parse(test_config_path: str, test_cli_runner: CliRunner) -> None:
    result = test_cli_runner.invoke(
        cli, ["-f", test_config_path, "parse", "demo_resources/"]
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_reset_db(test_config_path: str, test_cli_runner: CliRunner) -> None:
    result = test_cli_runner.invoke(cli, ["-f", test_config_path, "db", "reset", "-y"])
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_init_db(test_config_path: str, test_cli_runner: CliRunner) -> None:
    result = test_cli_runner.invoke(cli, ["-f", test_config_path, "db", "init"])
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_apply(test_config_path: str, test_cli_runner: CliRunner) -> None:
    result = test_cli_runner.invoke(
        cli, ["-f", test_config_path, "apply", "demo_resources/"]
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_dry_apply(test_config_path: str, test_cli_runner: CliRunner) -> None:
    result = test_cli_runner.invoke(
        cli, ["-f", test_config_path, "apply", "--dry", "demo_resources/"]
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_diff_apply(test_config_path: str, test_cli_runner: CliRunner) -> None:
    result = test_cli_runner.invoke(
        cli, ["-f", test_config_path, "apply", "--diff", "demo_resources/"]
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_dry_diff_apply(test_config_path: str, test_cli_runner: CliRunner) -> None:
    result = test_cli_runner.invoke(
        cli, ["-f", test_config_path, "apply", "--dry", "--diff", "demo_resources/"]
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
class TestPull:
    def test_pull(
        self,
        test_config_path: str,
        test_cli_runner: CliRunner,
    ) -> None:
        """
        Due to the fact that this command checks the real git status, a pytest
        tmp_dir can't be used. Consequently a real directory must be tested against
        and then reset.
        """
        test_dir = ".fides/"
        result = test_cli_runner.invoke(cli, ["-f", test_config_path, "pull", test_dir])
        git_reset(test_dir)
        print(result.output)
        assert result.exit_code == 0

    def test_pull_all(
        self,
        test_config_path: str,
        test_cli_runner: CliRunner,
    ) -> None:
        """
        Due to the fact that this command checks the real git status, a pytest
        tmp_dir can't be used. Consequently a real directory must be tested against
        and then reset.
        """
        test_dir = ".fides/"
        test_file = ".fides/test_resources.yml"
        result = test_cli_runner.invoke(
            cli,
            [
                "-f",
                test_config_path,
                "pull",
                test_dir,
                "-a",
                ".fides/test_resources.yml",
            ],
        )
        git_reset(test_dir)
        os.remove(test_file)
        print(result.output)
        assert result.exit_code == 0


@pytest.mark.integration
def test_audit(test_config_path: str, test_cli_runner: CliRunner) -> None:
    result = test_cli_runner.invoke(cli, ["-f", test_config_path, "evaluate", "-a"])
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_get(test_config_path: str, test_cli_runner: CliRunner) -> None:
    result = test_cli_runner.invoke(
        cli,
        ["-f", test_config_path, "get", "data_category", "user"],
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_ls(test_config_path: str, test_cli_runner: CliRunner) -> None:
    result = test_cli_runner.invoke(cli, ["-f", test_config_path, "ls", "system"])
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_evaluate_with_declaration_pass(
    test_config_path: str, test_cli_runner: CliRunner
) -> None:
    result = test_cli_runner.invoke(
        cli,
        [
            "-f",
            test_config_path,
            "evaluate",
            "tests/ctl/data/passing_declaration_taxonomy.yml",
        ],
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_evaluate_demo_resources_pass(
    test_config_path: str, test_cli_runner: CliRunner
) -> None:
    result = test_cli_runner.invoke(
        cli,
        ["-f", test_config_path, "evaluate", "demo_resources/"],
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_local_evaluate(
    test_invalid_config_path: str, test_cli_runner: CliRunner
) -> None:
    result = test_cli_runner.invoke(
        cli,
        [
            "--local",
            "-f",
            test_invalid_config_path,
            "evaluate",
            "tests/ctl/data/passing_declaration_taxonomy.yml",
        ],
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_local_evaluate_demo_resources(
    test_invalid_config_path: str, test_cli_runner: CliRunner
) -> None:
    result = test_cli_runner.invoke(
        cli,
        [
            "--local",
            "-f",
            test_invalid_config_path,
            "evaluate",
            "demo_resources/",
        ],
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_evaluate_with_key_pass(
    test_config_path: str, test_cli_runner: CliRunner
) -> None:
    result = test_cli_runner.invoke(
        cli,
        [
            "-f",
            test_config_path,
            "evaluate",
            "-k",
            "primary_privacy_policy",
            "tests/ctl/data/passing_declaration_taxonomy.yml",
        ],
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_evaluate_with_declaration_failed(
    test_config_path: str, test_cli_runner: CliRunner
) -> None:
    result = test_cli_runner.invoke(
        cli,
        [
            "-f",
            test_config_path,
            "evaluate",
            "tests/ctl/data/failing_declaration_taxonomy.yml",
        ],
    )
    print(result.output)
    assert result.exit_code == 1


@pytest.mark.integration
def test_evaluate_with_dataset_failed(
    test_config_path: str, test_cli_runner: CliRunner
) -> None:
    result = test_cli_runner.invoke(
        cli,
        [
            "-f",
            test_config_path,
            "evaluate",
            "tests/ctl/data/failing_dataset_taxonomy.yml",
        ],
    )
    print(result.output)
    assert result.exit_code == 1


@pytest.mark.integration
def test_evaluate_with_dataset_field_failed(
    test_config_path: str, test_cli_runner: CliRunner
) -> None:
    result = test_cli_runner.invoke(
        cli,
        [
            "-f",
            test_config_path,
            "evaluate",
            "tests/ctl/data/failing_dataset_collection_taxonomy.yml",
        ],
    )
    print(result.output)
    assert result.exit_code == 1


@pytest.mark.integration
def test_evaluate_with_dataset_collection_failed(
    test_config_path: str, test_cli_runner: CliRunner
) -> None:
    result = test_cli_runner.invoke(
        cli,
        [
            "-f",
            test_config_path,
            "evaluate",
            "tests/ctl/data/failing_dataset_field_taxonomy.yml",
        ],
    )
    print(result.output)
    assert result.exit_code == 1


@pytest.mark.integration
@pytest.mark.parametrize(
    "export_resource", ["system", "dataset", "organization", "datamap"]
)
def test_export_resources(
    test_config_path: str,
    test_cli_runner: CliRunner,
    export_resource: str,
) -> None:
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
            "--dry",
        ],
    )
    assert result.exit_code == 0


@pytest.mark.integration
def test_nested_field_fails_evaluation(
    test_config_path: str, test_cli_runner: CliRunner
) -> None:
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
            "tests/ctl/data/failing_nested_dataset.yml",
        ],
    )
    print(result.output)
    assert result.exit_code == 1


@pytest.mark.integration
def test_generate_dataset_db_with_connection_string(
    test_config_path: str,
    test_cli_runner: CliRunner,
    tmpdir: LocalPath,
) -> None:
    tmp_file = tmpdir.join("dataset.yml")
    result = test_cli_runner.invoke(
        cli,
        [
            "-f",
            test_config_path,
            "generate",
            "dataset",
            "db",
            f"{tmp_file}",
            "--connection-string",
            "postgresql+psycopg2://postgres:fidesctl@fidesctl-db:5432/fidesctl_test",
        ],
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_generate_dataset_db_with_credentials_id(
    test_config_path: str,
    test_cli_runner: CliRunner,
    tmpdir: LocalPath,
) -> None:
    tmp_file = tmpdir.join("dataset.yml")
    result = test_cli_runner.invoke(
        cli,
        [
            "-f",
            test_config_path,
            "generate",
            "dataset",
            "db",
            f"{tmp_file}",
            "--credentials-id",
            "postgres_1",
        ],
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_scan_dataset_db_input_connection_string(
    test_config_path: str, test_cli_runner: CliRunner
) -> None:
    result = test_cli_runner.invoke(
        cli,
        [
            "-f",
            test_config_path,
            "scan",
            "dataset",
            "db",
            "--connection-string",
            "postgresql+psycopg2://postgres:fidesctl@fidesctl-db:5432/fidesctl_test",
            "--coverage-threshold",
            "0",
        ],
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_scan_dataset_db_input_credentials_id(
    test_config_path: str, test_cli_runner: CliRunner
) -> None:
    result = test_cli_runner.invoke(
        cli,
        [
            "-f",
            test_config_path,
            "scan",
            "dataset",
            "db",
            "--credentials-id",
            "postgres_1",
            "--coverage-threshold",
            "0",
        ],
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.external
def test_generate_system_aws_environment_credentials(
    test_config_path: str,
    test_cli_runner: CliRunner,
    tmpdir: LocalPath,
) -> None:
    tmp_file = tmpdir.join("system.yml")
    result = test_cli_runner.invoke(
        cli,
        ["-f", test_config_path, "generate", "system", "aws", f"{tmp_file}"],
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.external
def test_scan_system_aws_environment_credentials(
    test_config_path: str, test_cli_runner: CliRunner
) -> None:
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
def test_generate_system_aws_input_credential_options(
    test_config_path: str,
    test_cli_runner: CliRunner,
    tmpdir: LocalPath,
) -> None:
    tmp_file = tmpdir.join("system.yml")
    result = test_cli_runner.invoke(
        cli,
        [
            "-f",
            test_config_path,
            "generate",
            "system",
            "aws",
            f"{tmp_file}",
            "--access_key_id",
            os.environ["AWS_ACCESS_KEY_ID"],
            "--secret_access_key",
            os.environ["AWS_SECRET_ACCESS_KEY"],
            "--region",
            os.environ["AWS_DEFAULT_REGION"],
        ],
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.external
def test_scan_system_aws_input_credential_options(
    test_config_path: str, test_cli_runner: CliRunner
) -> None:
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
            "--access_key_id",
            os.environ["AWS_ACCESS_KEY_ID"],
            "--secret_access_key",
            os.environ["AWS_SECRET_ACCESS_KEY"],
            "--region",
            os.environ["AWS_DEFAULT_REGION"],
        ],
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.external
def test_generate_system_aws_input_credentials_id(
    test_config_path: str,
    test_cli_runner: CliRunner,
    tmpdir: LocalPath,
) -> None:
    os.environ["FIDESCTL__CREDENTIALS__AWS_1__AWS_ACCESS_KEY_ID"] = os.environ[
        "AWS_ACCESS_KEY_ID"
    ]
    os.environ["FIDESCTL__CREDENTIALS__AWS_1__AWS_SECRET_ACCESS_KEY"] = os.environ[
        "AWS_SECRET_ACCESS_KEY"
    ]
    tmp_file = tmpdir.join("system.yml")
    result = test_cli_runner.invoke(
        cli,
        [
            "-f",
            test_config_path,
            "generate",
            "system",
            "aws",
            f"{tmp_file}",
            "--credentials-id",
            "aws_1",
        ],
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.external
def test_scan_system_aws_input_credentials_id(
    test_config_path: str, test_cli_runner: CliRunner
) -> None:
    os.environ["FIDESCTL__CREDENTIALS__AWS_1__AWS_ACCESS_KEY_ID"] = os.environ[
        "AWS_ACCESS_KEY_ID"
    ]
    os.environ["FIDESCTL__CREDENTIALS__AWS_1__AWS_SECRET_ACCESS_KEY"] = os.environ[
        "AWS_SECRET_ACCESS_KEY"
    ]

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
            "--credentials-id",
            "aws_1",
        ],
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.external
def test_generate_system_okta_input_credential_options(
    test_config_path: str,
    test_cli_runner: CliRunner,
    tmpdir: LocalPath,
) -> None:
    tmp_file = tmpdir.join("system.yml")
    token = os.environ["OKTA_CLIENT_TOKEN"]
    result = test_cli_runner.invoke(
        cli,
        [
            "-f",
            test_config_path,
            "generate",
            "system",
            "okta",
            f"{tmp_file}",
            "--org-url",
            OKTA_URL,
            "--token",
            token,
        ],
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.external
def test_scan_system_okta_input_credential_options(
    test_config_path: str, test_cli_runner: CliRunner
) -> None:
    token = os.environ["OKTA_CLIENT_TOKEN"]
    result = test_cli_runner.invoke(
        cli,
        [
            "-f",
            test_config_path,
            "scan",
            "system",
            "okta",
            "--org-url",
            OKTA_URL,
            "--token",
            token,
            "--coverage-threshold",
            "0",
        ],
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.external
def test_generate_system_okta_environment_credentials(
    test_config_path: str,
    test_cli_runner: CliRunner,
    tmpdir: LocalPath,
) -> None:
    tmp_file = tmpdir.join("system.yml")
    os.environ["OKTA_CLIENT_ORGURL"] = OKTA_URL
    result = test_cli_runner.invoke(
        cli,
        ["-f", test_config_path, "generate", "system", "okta", f"{tmp_file}"],
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.external
def test_scan_system_okta_environment_credentials(
    test_config_path: str,
    test_cli_runner: CliRunner,
) -> None:
    os.environ["OKTA_CLIENT_ORGURL"] = OKTA_URL
    result = test_cli_runner.invoke(
        cli,
        [
            "-f",
            test_config_path,
            "scan",
            "system",
            "okta",
            "--coverage-threshold",
            "0",
        ],
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.external
def test_generate_system_okta_input_credentials_id(
    test_config_path: str,
    test_cli_runner: CliRunner,
    tmpdir: LocalPath,
) -> None:
    tmp_file = tmpdir.join("system.yml")
    os.environ["FIDESCTL__CREDENTIALS__OKTA_1__TOKEN"] = os.environ["OKTA_CLIENT_TOKEN"]
    result = test_cli_runner.invoke(
        cli,
        [
            "-f",
            test_config_path,
            "generate",
            "system",
            "okta",
            f"{tmp_file}",
            "--credentials-id",
            "okta_1",
        ],
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.external
def test_scan_system_okta_input_credentials_id(
    test_config_path: str,
    test_cli_runner: CliRunner,
) -> None:
    os.environ["FIDESCTL__CREDENTIALS__OKTA_1__TOKEN"] = os.environ["OKTA_CLIENT_TOKEN"]
    result = test_cli_runner.invoke(
        cli,
        [
            "-f",
            test_config_path,
            "scan",
            "system",
            "okta",
            "--credentials-id",
            "okta_1",
            "--coverage-threshold",
            "0",
        ],
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.external
def test_generate_dataset_bigquery_credentials_id(
    test_config_path: str,
    test_cli_runner: CliRunner,
    tmpdir: LocalPath,
) -> None:

    tmp_output_file = tmpdir.join("dataset.yml")
    config_data = os.getenv("BIGQUERY_CONFIG", "")
    config_data_decoded = loads(b64decode(config_data.encode("utf-8")).decode("utf-8"))
    os.environ["FIDESCTL__CREDENTIALS__BIGQUERY_1__PROJECT_ID"] = config_data_decoded[
        "project_id"
    ]
    os.environ[
        "FIDESCTL__CREDENTIALS__BIGQUERY_1__PRIVATE_KEY_ID"
    ] = config_data_decoded["private_key_id"]
    os.environ["FIDESCTL__CREDENTIALS__BIGQUERY_1__PRIVATE_KEY"] = config_data_decoded[
        "private_key"
    ]
    os.environ["FIDESCTL__CREDENTIALS__BIGQUERY_1__CLIENT_EMAIL"] = config_data_decoded[
        "client_email"
    ]
    os.environ["FIDESCTL__CREDENTIALS__BIGQUERY_1__CLIENT_ID"] = config_data_decoded[
        "client_id"
    ]
    os.environ[
        "FIDESCTL__CREDENTIALS__BIGQUERY_1__CLIENT_X509_CERT_URL"
    ] = config_data_decoded["client_x509_cert_url"]
    dataset_name = "fidesopstest"
    result = test_cli_runner.invoke(
        cli,
        [
            "-f",
            test_config_path,
            "generate",
            "dataset",
            "gcp",
            "bigquery",
            dataset_name,
            f"{tmp_output_file}",
            "--credentials-id",
            "bigquery_1",
        ],
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.external
def test_generate_dataset_bigquery_keyfile_path(
    test_config_path: str,
    test_cli_runner: CliRunner,
    tmpdir: LocalPath,
) -> None:

    tmp_output_file = tmpdir.join("dataset.yml")
    tmp_keyfile = tmpdir.join("bigquery.json")
    config_data = os.getenv("BIGQUERY_CONFIG", "")
    config_data_decoded = loads(b64decode(config_data.encode("utf-8")).decode("utf-8"))
    with open(tmp_keyfile, "w", encoding="utf-8") as keyfile:
        dump(config_data_decoded, keyfile)
    dataset_name = "fidesopstest"
    result = test_cli_runner.invoke(
        cli,
        [
            "-f",
            test_config_path,
            "generate",
            "dataset",
            "gcp",
            "bigquery",
            dataset_name,
            f"{tmp_output_file}",
            "--keyfile-path",
            f"{tmp_keyfile}",
        ],
    )
    print(result.output)
    assert result.exit_code == 0
