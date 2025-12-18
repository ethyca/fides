from dataclasses import dataclass
from typing import Optional

from constants_nox import (
    CI_ARGS_EXEC,
    COMPOSE_FILE,
    CONTAINER_NAME,
    EXEC,
    IMAGE_NAME,
    INTEGRATION_COMPOSE_FILE,
    LOGIN,
    START_APP,
    START_APP_WITH_EXTERNAL_POSTGRES,
)
from nox import Session
from run_infrastructure import (
    API_TEST_DIR,
    OPS_API_TEST_DIRS,
    OPS_TEST_DIR,
    run_infrastructure,
)


@dataclass
class CoverageConfig:
    report_format: str = "xml"
    cov_name: str = "fides"
    branch_coverage: bool = True
    skip_on_fail: bool = True

    def __str__(self):
        return " ".join(self.args)

    @property
    def args(self) -> list[str]:
        return [
            f"--cov={self.cov_name}",
            f"--cov-report={self.report_format}",
            "--cov-branch" if self.branch_coverage else "",
            "--no-cov-on-fail" if self.skip_on_fail else "",
        ]


@dataclass
class XdistConfig:
    parallel_runners: str = "auto"

    def __str__(self):
        return " ".join(self.args)

    @property
    def args(self) -> list[str]:
        return ["-n", self.parallel_runners]


@dataclass
class ReportConfig:
    report_file: str = "test_report.xml"
    report_format: str = "xml"

    def __str__(self):
        return " ".join(self.args)

    @property
    def args(self) -> list[str]:
        if self.report_format == "xml":
            return [
                "--junitxml",
                self.report_file,
            ]

        return []


@dataclass
class PytestConfig:
    xdist_config: Optional[XdistConfig] = None
    coverage_config: Optional[CoverageConfig] = None
    report_config: Optional[ReportConfig] = None
    suppress_stdout: bool = True
    suppress_warnings: bool = True

    @property
    def args(self) -> list[str]:
        return [
            *self.xdist_config.args,
            *self.coverage_config.args,
            *self.report_config.args,
            "-x",
            "-s" if self.suppress_stdout else "",
            "-W ignore" if self.suppress_warnings else "",
        ]


def pytest_lib(session: Session, pytest_config: PytestConfig) -> None:
    """Runs lib tests."""
    session.notify("teardown")
    session.run(*START_APP, external=True)
    run_command = (
        *EXEC,
        "pytest",
        *pytest_config.args,
        "tests/lib/",
    )
    session.run(*run_command, external=True)


def pytest_nox(session: Session, pytest_config: PytestConfig) -> None:
    """Runs any tests of nox commands themselves."""
    # the nox tests don't run with coverage or xdist so just add the reporting config here
    run_command = ("pytest", *pytest_config.report_config.args, "noxfiles/")
    session.run(*run_command, external=True)


def pytest_ctl(session: Session, mark: str, pytest_config: PytestConfig) -> None:
    """Runs ctl tests."""
    session.notify("teardown")
    if mark == "external":
        start_command = (
            "docker",
            "compose",
            "-f",
            COMPOSE_FILE,
            "-f",
            INTEGRATION_COMPOSE_FILE,
            "up",
            "--wait",
            IMAGE_NAME,
        )
        session.run(*start_command, external=True)
        session.run(*LOGIN, external=True)
        run_command = (
            "docker",
            "exec",
            "-e",
            "SNOWFLAKE_FIDESCTL_PASSWORD",
            "-e",
            "REDSHIFT_FIDESCTL_PASSWORD",
            "-e",
            "AWS_ACCESS_KEY_ID",
            "-e",
            "AWS_SECRET_ACCESS_KEY",
            "-e",
            "AWS_DEFAULT_REGION",
            "-e",
            "OKTA_CLIENT_TOKEN",
            "-e",
            "BIGQUERY_CONFIG",
            "-e",
            "DYNAMODB_REGION",
            "-e",
            "DYNAMODB_ACCESS_KEY_ID",
            "-e",
            "DYNAMODB_ACCESS_KEY",
            CI_ARGS_EXEC,
            CONTAINER_NAME,
            "pytest",
            *pytest_config.coverage_config.args,
            *pytest_config.report_config.args,
            "-m",
            "external",
            "tests/ctl",
            "--tb=no",
        )
        session.run(*run_command, external=True)
    else:
        import copy

        # Don't use xdist for this one
        local_pytest_config = copy.copy(pytest_config)
        local_pytest_config.xdist_config.parallel_runners = "0"

        session.run(*START_APP, external=True)
        session.run(*LOGIN, external=True)
        run_command = (
            *EXEC,
            "pytest",
            *local_pytest_config.args,
            "tests/ctl/",
            "-m",
            mark,
            "--full-trace",
        )
        session.run(*run_command, external=True)


def pytest_ops(
    session: Session,
    mark: str,
    pytest_config: PytestConfig,
    subset_dir: Optional[str] = None,
) -> None:
    """Runs fidesops tests."""
    session.notify("teardown")
    if mark == "unit":
        session.run(*START_APP, external=True)
        if subset_dir == "api":
            run_command = (
                *EXEC,
                "pytest",
                *pytest_config.args,
                *OPS_API_TEST_DIRS,
                "-m",
                "not integration and not integration_external and not integration_saas",
            )
        elif subset_dir == "non-api":
            ignore_args = [f"--ignore={dir}" for dir in OPS_API_TEST_DIRS]
            run_command = (
                *EXEC,
                "pytest",
                *pytest_config.args,
                OPS_TEST_DIR,
                *ignore_args,
                "-m",
                "not integration and not integration_external and not integration_saas",
            )
        else:
            run_command = (
                *EXEC,
                "pytest",
                *pytest_config.args,
                OPS_TEST_DIR,
                "-m",
                "not integration and not integration_external and not integration_saas",
            )
        session.run(*run_command, external=True)
    elif mark == "integration":
        # The coverage_arg is hardcoded in 'run_infrastructure.py'
        run_infrastructure(
            run_tests=True,
            analytics_opt_out=True,
            datastores=[],
            pytest_path=f"{OPS_TEST_DIR} tests/integration/",
        )
    elif mark == "external_datastores":
        session.run(*START_APP_WITH_EXTERNAL_POSTGRES, external=True)
        run_command = (
            "docker",
            "exec",
            "-e",
            "ANALYTICS_OPT_OUT",
            "-e",
            "REDSHIFT_TEST_HOST",
            "-e",
            "REDSHIFT_TEST_PORT",
            "-e",
            "REDSHIFT_TEST_USER",
            "-e",
            "REDSHIFT_TEST_PASSWORD",
            "-e",
            "REDSHIFT_TEST_DATABASE",
            "-e",
            "REDSHIFT_TEST_DB_SCHEMA",
            "-e",
            "SNOWFLAKE_TEST_ACCOUNT_IDENTIFIER",
            "-e",
            "SNOWFLAKE_TEST_USER_LOGIN_NAME",
            "-e",
            "SNOWFLAKE_TEST_PASSWORD",
            "-e",
            "SNOWFLAKE_TEST_PRIVATE_KEY",
            "-e",
            "SNOWFLAKE_TEST_PRIVATE_KEY_PASSPHRASE",
            "-e",
            "SNOWFLAKE_TEST_WAREHOUSE_NAME",
            "-e",
            "SNOWFLAKE_TEST_DATABASE_NAME",
            "-e",
            "SNOWFLAKE_TEST_SCHEMA_NAME",
            "-e",
            "BIGQUERY_KEYFILE_CREDS",
            "-e",
            "BIGQUERY_DATASET",
            "-e",
            "BIGQUERY_ENTERPRISE_KEYFILE_CREDS",
            "-e",
            "BIGQUERY_ENTERPRISE_DATASET",
            "-e",
            "GOOGLE_CLOUD_SQL_MYSQL_DB_IAM_USER",
            "-e",
            "GOOGLE_CLOUD_SQL_MYSQL_INSTANCE_CONNECTION_NAME",
            "-e",
            "GOOGLE_CLOUD_SQL_MYSQL_DATABASE_NAME",
            "-e",
            "GOOGLE_CLOUD_SQL_MYSQL_KEYFILE_CREDS",
            "-e",
            "GOOGLE_CLOUD_SQL_POSTGRES_DB_IAM_USER",
            "-e",
            "GOOGLE_CLOUD_SQL_POSTGRES_INSTANCE_CONNECTION_NAME",
            "-e",
            "GOOGLE_CLOUD_SQL_POSTGRES_DATABASE_NAME",
            "-e",
            "GOOGLE_CLOUD_SQL_POSTGRES_DATABASE_SCHEMA_NAME",
            "-e",
            "GOOGLE_CLOUD_SQL_POSTGRES_KEYFILE_CREDS",
            "-e",
            "OKTA_ORG_URL",
            "-e",
            "OKTA_API_TOKEN",
            "-e",
            "RDS_MYSQL_AWS_ACCESS_KEY_ID",
            "-e",
            "RDS_MYSQL_AWS_SECRET_ACCESS_KEY",
            "-e",
            "RDS_MYSQL_DB_USERNAME",
            "-e",
            "RDS_MYSQL_DB_INSTANCE",
            "-e",
            "RDS_MYSQL_DB_NAME",
            "-e",
            "RDS_MYSQL_REGION",
            "-e",
            "RDS_POSTGRES_AWS_ACCESS_KEY_ID",
            "-e",
            "RDS_POSTGRES_AWS_SECRET_ACCESS_KEY",
            "-e",
            "RDS_POSTGRES_DB_USERNAME",
            "-e",
            "RDS_POSTGRES_REGION",
            "-e",
            "DYNAMODB_REGION",
            "-e",
            "DYNAMODB_ACCESS_KEY_ID",
            "-e",
            "DYNAMODB_ACCESS_KEY",
            "-e",
            "DYNAMODB_ASSUME_ROLE_ARN",
            "-e",
            "S3_AWS_ACCESS_KEY_ID",
            "-e",
            "S3_AWS_SECRET_ACCESS_KEY",
            "-e",
            "MONGODB_ATLAS_HOST",
            "-e",
            "MONGODB_ATLAS_DEFAULT_AUTH_DB",
            "-e",
            "MONGODB_ATLAS_USERNAME",
            "-e",
            "MONGODB_ATLAS_PASSWORD",
            "-e",
            "MONGODB_ATLAS_USE_SRV",
            "-e",
            "MONGODB_ATLAS_SSL_ENABLED",
            CI_ARGS_EXEC,
            CONTAINER_NAME,
            "pytest",
            # Don't use xdist for these
            *pytest_config.coverage_config.args,
            *pytest_config.report_config.args,
            OPS_TEST_DIR,
            "-m",
            "integration_external",
        )
        session.run(*run_command, external=True)
    elif mark == "saas":
        # This test runs an additional integration Postgres database.
        # Some connectors cannot be traversed with the standard email
        # identity and require another dataset to provide a starting value.
        #
        #         ┌────────┐                 ┌────────┐
        # email──►│postgres├──►delivery_id──►│doordash│
        #         └────────┘                 └────────┘
        #
        session.run(*START_APP_WITH_EXTERNAL_POSTGRES, external=True)
        run_command = (
            "docker",
            "exec",
            "-e",
            "ANALYTICS_OPT_OUT",
            "-e",
            "SAAS_OP_SERVICE_ACCOUNT_TOKEN",
            "-e",
            "SAAS_SECRETS_OP_VAULT_ID",
            "-e",
            "FIDES__DEV_MODE=false",
            CI_ARGS_EXEC,
            CONTAINER_NAME,
            "pytest",
            "--reruns",
            "3",
            # Don't use xdist for these
            *pytest_config.coverage_config.args,
            *pytest_config.report_config.args,
            OPS_TEST_DIR,
            "-m",
            "integration_saas",
            "--tb=no",
        )
        session.run(*run_command, external=True)


def pytest_api(session: Session, pytest_config: PytestConfig) -> None:
    """Runs tests under /tests/api/"""
    session.notify("teardown")
    session.run(*START_APP, external=True)
    run_command = (
        *EXEC,
        "pytest",
        *pytest_config.args,
        API_TEST_DIR,
        "-m",
        "not integration and not integration_external and not integration_saas",
    )
    session.run(*run_command, external=True)


def pytest_misc_unit(session: Session, pytest_config: PytestConfig) -> None:
    """Runs unit tests from smaller test directories."""
    session.notify("teardown")
    session.run(*START_APP, external=True)
    run_command = (
        *EXEC,
        "pytest",
        *pytest_config.args,
        "tests/service/",
        "tests/task/",
        "tests/util/",
        "-m",
        "not integration and not integration_external and not integration_saas and not integration_snowflake and not integration_bigquery and not integration_postgres",
    )
    session.run(*run_command, external=True)


def pytest_misc_integration(
    session: Session, mark: str, pytest_config: PytestConfig
) -> None:
    """Runs integration tests from smaller test directories."""
    session.notify("teardown")
    if mark == "external":
        session.run(*START_APP, external=True)
        # Use the integration infrastructure to run all tests from multiple directories
        # Need PostgreSQL for service integration tests, BigQuery for QA tests, and Snowflake for service tests
        run_command = (
            "docker",
            "exec",
            "-e",
            "SNOWFLAKE_TEST_ACCOUNT_IDENTIFIER",
            "-e",
            "SNOWFLAKE_TEST_USER_LOGIN_NAME",
            "-e",
            "SNOWFLAKE_TEST_PASSWORD",
            "-e",
            "SNOWFLAKE_TEST_PRIVATE_KEY",
            "-e",
            "SNOWFLAKE_TEST_PRIVATE_KEY_PASSPHRASE",
            "-e",
            "SNOWFLAKE_TEST_WAREHOUSE_NAME",
            "-e",
            "SNOWFLAKE_TEST_DATABASE_NAME",
            "-e",
            "SNOWFLAKE_TEST_SCHEMA_NAME",
            "-e",
            "BIGQUERY_KEYFILE_CREDS",
            "-e",
            "BIGQUERY_DATASET",
            "-e",
            "BIGQUERY_ENTERPRISE_KEYFILE_CREDS",
            "-e",
            "BIGQUERY_ENTERPRISE_DATASET",
            "-e",
            "MONGODB_ATLAS_HOST",
            "-e",
            "MONGODB_ATLAS_USERNAME",
            "-e",
            "MONGODB_ATLAS_PASSWORD",
            "-e",
            "MONGODB_ATLAS_DEFAULT_AUTH_DB",
            CI_ARGS_EXEC,
            CONTAINER_NAME,
            "pytest",
            *pytest_config.args,
            "tests/qa/",
            "tests/service/",
            "tests/task/",
            "tests/util/",
            "-m",
            mark,
        )
        session.run(*run_command, external=True)
    else:
        # Use the mark parameter for non-external integration tests
        session.run(*START_APP, external=True)
        run_infrastructure(
            run_tests=True,
            analytics_opt_out=True,
            datastores=["postgres", "bigquery", "snowflake"],
            pytest_path="tests/qa/ tests/service/ tests/task/ tests/util/",
        )
