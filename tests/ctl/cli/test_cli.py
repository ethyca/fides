# pylint: disable=missing-docstring, redefined-outer-name
import os
from base64 import b64decode
from json import dump, loads
from typing import Generator

import pytest
import yaml
from click.testing import CliRunner
from git.repo import Repo
from py._path.local import LocalPath

from fides.api.oauth.roles import OWNER, VIEWER
from fides.cli import cli
from fides.common.api.scope_registry import SCOPE_REGISTRY
from fides.config import CONFIG
from fides.core.user import get_systems_managed_by_user, get_user_permissions
from fides.core.utils import get_auth_header, read_credentials_file

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
        cli, ["init"], env={"FIDES__USER__ANALYTICS_OPT_OUT": "true"}
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
def test_init_opt_in(test_cli_runner: CliRunner) -> None:
    result = test_cli_runner.invoke(
        cli,
        ["init", "--opt-in"],
    )
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.unit
def test_local_flag_invalid_command(test_cli_runner: CliRunner) -> None:
    result = test_cli_runner.invoke(
        cli,
        ["--local", "push"],
    )
    print(result.output)
    assert result.exit_code == 1


@pytest.mark.unit
def test_commands_print_help_text_even_on_invalid(
    test_config_path: str, test_cli_runner: CliRunner, credentials_path: str
) -> None:

    # the context needs to have a placeholder URL since these tests are testing for behavior when the server is invalid/shutdown
    result = test_cli_runner.invoke(
        cli,
        ["-f", test_config_path, "user", "permissions"],
        env={"FIDES_CREDENTIALS_PATH": "/root/notarealfile.credentials"},
    )
    assert result.exit_code == 1

    result = test_cli_runner.invoke(
        cli,
        ["-f", test_config_path, "user", "permissions", "--help"],
        env={"FIDES_CREDENTIALS_PATH": "/root/notarealfile.credentials"},
    )
    print(f"results output: {result.output}")
    assert result.exit_code == 0
    assert "Usage: fides user permissions [OPTIONS]" in result.output


@pytest.mark.unit
def test_cli_version(test_cli_runner: CliRunner) -> None:
    result = test_cli_runner.invoke(cli, ["--version"])
    import fides

    assert f"fides, version {fides.__version__}" in result.output
    assert result.exit_code == 0


class TestView:
    @pytest.mark.unit
    def test_view_config(self, test_cli_runner: CliRunner) -> None:
        result = test_cli_runner.invoke(
            cli, ["view", "config"], env={"FIDES__USER__ANALYTICS_OPT_OUT": "true"}
        )
        print(result.output)
        assert result.exit_code == 0

    @pytest.mark.unit
    def test_view_credentials(self, test_cli_runner: CliRunner) -> None:
        result = test_cli_runner.invoke(
            cli, ["view", "credentials"], env={"FIDES__USER__ANALYTICS_OPT_OUT": "true"}
        )
        print(result.output)
        assert result.exit_code == 0


@pytest.mark.unit
def test_webserver() -> None:
    """
    This is specifically meant to catch when the webserver command breaks,
    without spinning up an additional instance.
    """
    from fides.api.main import start_webserver  # pylint: disable=unused-import

    assert True


@pytest.mark.unit
def test_worker() -> None:
    """
    This is specifically meant to catch when the worker command breaks,
    without spinning up an additional instance.
    """
    from fides.api.worker import start_worker  # pylint: disable=unused-import

    assert True


@pytest.mark.unit
def test_parse(test_config_path: str, test_cli_runner: CliRunner) -> None:
    result = test_cli_runner.invoke(
        cli, ["-f", test_config_path, "parse", "demo_resources/"]
    )
    print(result.output)
    assert result.exit_code == 0


class TestDB:
    @pytest.mark.skip(
        "This test is timing out only in CI: Safe-Tests (3.10.13, ctl-not-external)"
    )
    @pytest.mark.integration
    def test_reset_db(self, test_config_path: str, test_cli_runner: CliRunner) -> None:
        result = test_cli_runner.invoke(
            cli, ["-f", test_config_path, "db", "reset", "-y"]
        )
        print(result.output)
        assert result.exit_code == 0, result.output

    @pytest.mark.integration
    def test_init_db(self, test_config_path: str, test_cli_runner: CliRunner) -> None:
        result = test_cli_runner.invoke(cli, ["-f", test_config_path, "db", "init"])
        print(result.output)
        assert result.exit_code == 0

    @pytest.mark.integration
    def test_upgrade_db(
        self, test_config_path: str, test_cli_runner: CliRunner
    ) -> None:
        result = test_cli_runner.invoke(cli, ["-f", test_config_path, "db", "upgrade"])
        print(result.output)
        assert result.exit_code == 0


class TestPush:
    @pytest.mark.integration
    def test_push(self, test_config_path: str, test_cli_runner: CliRunner) -> None:
        result = test_cli_runner.invoke(
            cli, ["-f", test_config_path, "push", "demo_resources/"]
        )
        print(result.output)
        assert result.exit_code == 0

    @pytest.mark.integration
    def test_dry_push(self, test_config_path: str, test_cli_runner: CliRunner) -> None:
        result = test_cli_runner.invoke(
            cli, ["-f", test_config_path, "push", "--dry", "demo_resources/"]
        )
        print(result.output)
        assert result.exit_code == 0

    @pytest.mark.integration
    def test_diff_push(self, test_config_path: str, test_cli_runner: CliRunner) -> None:
        result = test_cli_runner.invoke(
            cli, ["-f", test_config_path, "push", "--diff", "demo_resources/"]
        )
        print(result.output)
        assert result.exit_code == 0

    @pytest.mark.integration
    def test_dry_diff_push(
        self, test_config_path: str, test_cli_runner: CliRunner
    ) -> None:
        result = test_cli_runner.invoke(
            cli, ["-f", test_config_path, "push", "--dry", "--diff", "demo_resources/"]
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

    def test_pull_one_resource(
        self,
        test_config_path: str,
        test_cli_runner: CliRunner,
    ) -> None:
        """
        Pull only one dataset into an empty dir and check if the file is created.
        """
        test_dir = ".fides/"
        result = test_cli_runner.invoke(
            cli, ["-f", test_config_path, "pull", "data_category", "system"]
        )
        git_reset(test_dir)
        print(result.output)
        assert result.exit_code == 0
        assert "not found" not in result.output


@pytest.mark.integration
class TestAnnotate:

    def test_annotate(
        self,
        test_config_path: str,
        test_cli_runner: CliRunner,
    ) -> None:
        """
        Test annotating dataset allowing you to interactively annotate the dataset with data categories
        """
        with open(
            "tests/ctl/data/dataset_missing_categories.yml", "r"
        ) as current_dataset_yml:
            dataset_yml = yaml.safe_load(current_dataset_yml)
            # Confirm starting state, that the first field has no data categories
            assert (
                "data_categories"
                not in dataset_yml["dataset"][0]["collections"][0]["fields"][0]
            )

        result = test_cli_runner.invoke(
            cli,
            [
                "-f",
                test_config_path,
                "annotate",
                "dataset",
                "tests/ctl/data/dataset_missing_categories.yml",
            ],
            input="user\n",
        )
        print(result.output)
        with open("tests/ctl/data/dataset_missing_categories.yml", "r") as dataset_yml:
            # Helps assert that the data category was output correctly
            dataset_yml = yaml.safe_load(dataset_yml)
            assert dataset_yml["dataset"][0]["collections"][0]["fields"][0][
                "data_categories"
            ] == ["user"]

            # Now remove the data category that was written by annotate dataset
            del dataset_yml["dataset"][0]["collections"][0]["fields"][0][
                "data_categories"
            ]

        with open(
            "tests/ctl/data/dataset_missing_categories.yml", "w"
        ) as current_dataset_yml:
            # Restore the original contents to the file
            yaml.safe_dump(dataset_yml, current_dataset_yml)

        assert result.exit_code == 0
        print(result.output)

    def test_regression_annotate_dataset(
        self,
        test_config_path: str,
        test_cli_runner: CliRunner,
    ):
        test_cli_runner.invoke(
            cli,
            [
                "-f",
                test_config_path,
                "annotate",
                "dataset",
                "tests/ctl/data/failing_direction.yml",
            ],
            input="user\n",
        )
        with open("tests/ctl/data/failing_direction.yml", "r") as dataset_yml:
            try:
                dataset_yml = yaml.safe_load(dataset_yml)
            except yaml.constructor.ConstructorError:
                assert False, "The yaml file is not valid"


@pytest.mark.integration
def test_audit(test_config_path: str, test_cli_runner: CliRunner) -> None:
    result = test_cli_runner.invoke(cli, ["-f", test_config_path, "evaluate", "-a"])
    print(result.output)
    assert result.exit_code == 0


@pytest.mark.integration
class TestCRUD:
    def test_get(self, test_config_path: str, test_cli_runner: CliRunner) -> None:
        result = test_cli_runner.invoke(
            cli,
            ["-f", test_config_path, "get", "data_category", "user"],
        )
        print(result.output)
        assert result.exit_code == 0

    def test_delete(self, test_config_path: str, test_cli_runner: CliRunner) -> None:
        result = test_cli_runner.invoke(
            cli,
            ["-f", test_config_path, "delete", "system", "demo_marketing_system"],
        )
        print(result.output)
        assert result.exit_code == 0

    def test_ls(self, test_config_path: str, test_cli_runner: CliRunner) -> None:
        result = test_cli_runner.invoke(cli, ["-f", test_config_path, "ls", "system"])
        print(result.output)
        assert result.exit_code == 0

    def test_ls_verbose(
        self, test_config_path: str, test_cli_runner: CliRunner
    ) -> None:
        result = test_cli_runner.invoke(
            cli, ["-f", test_config_path, "ls", "system", "--verbose"]
        )
        print(result.output)
        assert result.exit_code == 0

    def test_ls_no_resources_found(
        self, test_config_path: str, test_cli_runner: CliRunner
    ) -> None:
        """This test only works because we don't have any system resources by default."""
        result = test_cli_runner.invoke(cli, ["-f", test_config_path, "ls", "system"])
        print(result.output)
        assert result.exit_code == 0


class TestEvaluate:
    @pytest.mark.integration
    def test_evaluate_with_declaration_pass(
        self, test_config_path: str, test_cli_runner: CliRunner
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
        self, test_config_path: str, test_cli_runner: CliRunner
    ) -> None:
        result = test_cli_runner.invoke(
            cli,
            ["-f", test_config_path, "evaluate", "demo_resources/"],
        )
        print(result.output)
        assert result.exit_code == 0

    @pytest.mark.integration
    def test_local_evaluate(
        self, test_invalid_config_path: str, test_cli_runner: CliRunner
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
        self, test_invalid_config_path: str, test_cli_runner: CliRunner
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
        self, test_config_path: str, test_cli_runner: CliRunner
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
        self, test_config_path: str, test_cli_runner: CliRunner
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
        self, test_config_path: str, test_cli_runner: CliRunner
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
        self, test_config_path: str, test_cli_runner: CliRunner
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
        self, test_config_path: str, test_cli_runner: CliRunner
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
    def test_evaluate_nested_field_fails(
        self, test_config_path: str, test_cli_runner: CliRunner
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


class TestScan:
    @pytest.mark.integration
    def test_scan_dataset_db_input_connection_string(
        self, test_config_path: str, test_cli_runner: CliRunner
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
                "postgresql+psycopg2://postgres:fides@fides-db:5432/fides_test",
                "--coverage-threshold",
                "0",
            ],
        )
        print(result.output)
        assert result.exit_code == 0

    @pytest.mark.integration
    def test_scan_dataset_db_input_credentials_id(
        self, test_config_path: str, test_cli_runner: CliRunner
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

    @pytest.mark.integration
    def test_scan_dataset_db_local_flag(
        self, test_config_path: str, test_cli_runner: CliRunner
    ) -> None:
        result = test_cli_runner.invoke(
            cli,
            [
                "-f",
                test_config_path,
                "--local",
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
    def test_scan_system_aws_environment_credentials(
        self, test_config_path: str, test_cli_runner: CliRunner
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
    def test_scan_system_aws_input_credential_options(
        self, test_config_path: str, test_cli_runner: CliRunner
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
    def test_scan_system_aws_input_credentials_id(
        self, test_config_path: str, test_cli_runner: CliRunner
    ) -> None:
        os.environ["FIDES__CREDENTIALS__AWS_1__AWS_ACCESS_KEY_ID"] = os.environ[
            "AWS_ACCESS_KEY_ID"
        ]
        os.environ["FIDES__CREDENTIALS__AWS_1__AWS_SECRET_ACCESS_KEY"] = os.environ[
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
    def test_scan_system_okta_input_credential_options(
        self, test_config_path: str, test_cli_runner: CliRunner
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
    def test_scan_system_okta_input_credentials_id(
        self,
        test_config_path: str,
        test_cli_runner: CliRunner,
    ) -> None:
        os.environ["FIDES__CREDENTIALS__OKTA_1__TOKEN"] = os.environ[
            "OKTA_CLIENT_TOKEN"
        ]
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
    def test_scan_system_okta_environment_credentials(
        self,
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


class TestGenerate:
    @pytest.mark.integration
    def test_generate_dataset_db_with_connection_string(
        self,
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
                "postgresql+psycopg2://postgres:fides@fides-db:5432/fides_test",
            ],
        )
        print(result.output)
        assert result.exit_code == 0

        with open(tmp_file, "r") as dataset_yml:
            # Helps assert that the file was output correctly, namely, fides_keys were serialized as strings
            # and not a FidesKey python object
            dataset = yaml.safe_load(dataset_yml).get("dataset", [])
            assert isinstance(dataset[0]["fides_key"], str)

    @pytest.mark.integration
    def test_generate_dataset_db_with_credentials_id(
        self,
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

    @pytest.mark.external
    def test_generate_system_aws_input_credential_options(
        self,
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
    def test_generate_system_aws_environment_credentials(
        self,
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
    def test_generate_system_aws_input_credentials_id(
        self,
        test_config_path: str,
        test_cli_runner: CliRunner,
        tmpdir: LocalPath,
    ) -> None:
        os.environ["FIDES__CREDENTIALS__AWS_1__AWS_ACCESS_KEY_ID"] = os.environ[
            "AWS_ACCESS_KEY_ID"
        ]
        os.environ["FIDES__CREDENTIALS__AWS_1__AWS_SECRET_ACCESS_KEY"] = os.environ[
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
    def test_generate_system_okta_input_credential_options(
        self,
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
    def test_generate_system_okta_input_credentials_id(
        self,
        test_config_path: str,
        test_cli_runner: CliRunner,
        tmpdir: LocalPath,
    ) -> None:
        tmp_file = tmpdir.join("system.yml")
        os.environ["FIDES__CREDENTIALS__OKTA_1__TOKEN"] = os.environ[
            "OKTA_CLIENT_TOKEN"
        ]
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
    def test_generate_dataset_bigquery_credentials_id(
        self,
        test_config_path: str,
        test_cli_runner: CliRunner,
        tmpdir: LocalPath,
    ) -> None:
        tmp_output_file = tmpdir.join("dataset.yml")
        config_data = os.getenv("BIGQUERY_CONFIG", "e30=")
        config_data_decoded = loads(
            b64decode(config_data.encode("utf-8")).decode("utf-8")
        )
        os.environ["FIDES__CREDENTIALS__BIGQUERY_1__PROJECT_ID"] = config_data_decoded[
            "project_id"
        ]
        os.environ["FIDES__CREDENTIALS__BIGQUERY_1__PRIVATE_KEY_ID"] = (
            config_data_decoded["private_key_id"]
        )
        os.environ["FIDES__CREDENTIALS__BIGQUERY_1__PRIVATE_KEY"] = config_data_decoded[
            "private_key"
        ]
        os.environ["FIDES__CREDENTIALS__BIGQUERY_1__CLIENT_EMAIL"] = (
            config_data_decoded["client_email"]
        )
        os.environ["FIDES__CREDENTIALS__BIGQUERY_1__CLIENT_ID"] = config_data_decoded[
            "client_id"
        ]
        os.environ["FIDES__CREDENTIALS__BIGQUERY_1__CLIENT_X509_CERT_URL"] = (
            config_data_decoded["client_x509_cert_url"]
        )
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
        self,
        test_config_path: str,
        test_cli_runner: CliRunner,
        tmpdir: LocalPath,
    ) -> None:
        tmp_output_file = tmpdir.join("dataset.yml")
        tmp_keyfile = tmpdir.join("bigquery.json")
        config_data = os.getenv("BIGQUERY_CONFIG", "e30=")
        config_data_decoded = loads(
            b64decode(config_data.encode("utf-8")).decode("utf-8")
        )
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


@pytest.fixture(scope="class")
def credentials_path(tmp_path_factory) -> str:
    credentials_dir = tmp_path_factory.mktemp("credentials")
    credentials_path = credentials_dir / ".fides_credentials"
    return str(credentials_path)


@pytest.mark.integration
class TestUser:
    """
    Test the "user" command group.

    Most tests rely on previous tests.
    """

    def test_user_login_provide_credentials(
        self, test_config_path: str, test_cli_runner: CliRunner, credentials_path: str
    ) -> None:
        """Test logging in as a user with a provided username and password."""
        print(credentials_path)
        result = test_cli_runner.invoke(
            cli,
            [
                "-f",
                test_config_path,
                "user",
                "login",
                "-u",
                "root_user",
                "-p",
                "Testpassword1!",
            ],
            env={"FIDES_CREDENTIALS_PATH": credentials_path},
        )
        print(result.output)
        assert result.exit_code == 0

    def test_user_login_env_var_failed(
        self, test_config_path: str, test_cli_runner: CliRunner, credentials_path: str
    ) -> None:
        """
        Test logging in as a user with a provided username and password
        provided via env vars, but the username is invalid.
        """
        print(credentials_path)
        result = test_cli_runner.invoke(
            cli,
            [
                "-f",
                test_config_path,
                "user",
                "login",
            ],
            env={
                "FIDES_CREDENTIALS_PATH": credentials_path,
                "FIDES__USER__USERNAME": "fakeuser",
                "FIDES__USER__PASSWORD": "Testpassword1!",
            },
        )
        print(result.output)
        assert result.exit_code == 1

    def test_user_login_env_var_password(
        self, test_config_path: str, test_cli_runner: CliRunner, credentials_path: str
    ) -> None:
        """
        Test logging in as a user with a provided username but password
        provided via env vars.
        """
        print(credentials_path)
        result = test_cli_runner.invoke(
            cli,
            ["-f", test_config_path, "user", "login", "-u", "root_user"],
            env={
                "FIDES_CREDENTIALS_PATH": credentials_path,
                "FIDES__USER__PASSWORD": "Testpassword1!",
            },
        )
        print(result.output)
        assert result.exit_code == 0

    def test_user_login_env_var_credentials(
        self, test_config_path: str, test_cli_runner: CliRunner, credentials_path: str
    ) -> None:
        """
        Test logging in as a user with a provided username and password
        provided via env vars.
        """
        print(credentials_path)
        result = test_cli_runner.invoke(
            cli,
            [
                "-f",
                test_config_path,
                "user",
                "login",
            ],
            env={
                "FIDES_CREDENTIALS_PATH": credentials_path,
                "FIDES__USER__USERNAME": "root_user",
                "FIDES__USER__PASSWORD": "Testpassword1!",
            },
        )
        print(result.output)
        assert result.exit_code == 0

    def test_user_create(
        self, test_config_path: str, test_cli_runner: CliRunner, credentials_path: str
    ) -> None:
        """Test creating a user with the current credentials."""
        print(credentials_path)
        result = test_cli_runner.invoke(
            cli,
            [
                "-f",
                test_config_path,
                "user",
                "create",
                "newuser",
                "Newpassword1!",
                "test@ethyca.com",
            ],
            env={"FIDES_CREDENTIALS_PATH": credentials_path},
        )
        print(result.output)
        assert result.exit_code == 0

        test_cli_runner.invoke(
            cli,
            [
                "-f",
                test_config_path,
                "user",
                "login",
                "-u",
                "newuser",
                "-p",
                "Newpassword1!",
            ],
            env={"FIDES_CREDENTIALS_PATH": credentials_path},
        )

        credentials = read_credentials_file(credentials_path)
        total_scopes, roles = get_user_permissions(
            credentials.user_id, get_auth_header(), CONFIG.cli.server_url
        )
        assert set(total_scopes) == set(SCOPE_REGISTRY)
        assert roles == [OWNER]

    def test_user_permissions_valid(
        self, test_config_path: str, test_cli_runner: CliRunner, credentials_path: str
    ) -> None:
        """Test getting user permissions for the current user."""
        print(credentials_path)
        result = test_cli_runner.invoke(
            cli,
            ["-f", test_config_path, "user", "permissions"],
            env={"FIDES_CREDENTIALS_PATH": credentials_path},
        )
        print(result.output)
        assert result.exit_code == 0

    def test_get_self_user_permissions(
        self, test_config_path, test_cli_runner, credentials_path
    ) -> None:
        """Test getting user permissions"""
        test_cli_runner.invoke(
            cli,
            [
                "-f",
                test_config_path,
                "user",
                "login",
                "-u",
                "root_user",
                "-p",
                "Testpassword1!",
            ],
            env={"FIDES_CREDENTIALS_PATH": credentials_path},
        )
        total_scopes, roles = get_user_permissions(
            CONFIG.security.oauth_root_client_id,
            get_auth_header(),
            CONFIG.cli.server_url,
        )
        assert set(total_scopes) == set(SCOPE_REGISTRY)
        assert roles == [OWNER]

    @pytest.mark.unit
    def test_get_self_user_systems(
        self, test_config_path, test_cli_runner, credentials_path
    ) -> None:
        """Test getting user permissions"""
        test_cli_runner.invoke(
            cli,
            [
                "-f",
                test_config_path,
                "user",
                "login",
                "-u",
                "root_user",
                "-p",
                "Testpassword1!",
            ],
            env={"FIDES_CREDENTIALS_PATH": credentials_path},
        )
        systems = get_systems_managed_by_user(
            CONFIG.security.oauth_root_client_id,
            get_auth_header(),
            CONFIG.cli.server_url,
        )
        assert systems == []

    def test_get_other_user_perms_and_systems(
        self, test_config_path, test_cli_runner, credentials_path, system_manager
    ) -> None:
        """Test getting another user's permissions and systems"""
        test_cli_runner.invoke(
            cli,
            [
                "-f",
                test_config_path,
                "user",
                "login",
                "-u",
                "root_user",
                "-p",
                "Testpassword1!",
            ],
            env={"FIDES_CREDENTIALS_PATH": credentials_path},
        )
        total_scopes, roles = get_user_permissions(
            system_manager.id,
            get_auth_header(),
            CONFIG.cli.server_url,
        )
        assert roles == [VIEWER]

        systems = get_systems_managed_by_user(
            system_manager.id,
            get_auth_header(),
            CONFIG.cli.server_url,
        )
        assert systems == [system_manager.systems[0].fides_key]

    def test_user_permissions_not_found(
        self, test_config_path: str, test_cli_runner: CliRunner, credentials_path: str
    ) -> None:
        """Test getting user permissions but the credentials file doesn't exit."""
        print(credentials_path)
        result = test_cli_runner.invoke(
            cli,
            ["-f", test_config_path, "user", "permissions"],
            env={"FIDES_CREDENTIALS_PATH": "/root/notarealfile.credentials"},
        )
        print(result.output)
        assert result.exit_code == 1
