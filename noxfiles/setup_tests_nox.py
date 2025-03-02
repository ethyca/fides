from typing import Optional

from nox import Session

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
from run_infrastructure import API_TEST_DIR, OPS_TEST_DIR, run_infrastructure


def pytest_lib(session: Session, coverage_arg: str) -> None:
    """Runs lib tests."""
    session.notify("teardown")
    session.run(*START_APP, external=True)
    run_command = (
        *EXEC,
        "pytest",
        coverage_arg,
        "tests/lib/",
    )
    session.run(*run_command, external=True)


def pytest_nox(session: Session, coverage_arg: str) -> None:
    """Runs any tests of nox commands themselves."""
    # the nox tests don't run with coverage, override the provided arg
    coverage_arg = "--no-cov"
    run_command = ("pytest", coverage_arg, "noxfiles/")
    session.run(*run_command, external=True)


def pytest_ctl(session: Session, mark: str, coverage_arg: str) -> None:
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
            coverage_arg,
            "-m",
            "external",
            "tests/ctl",
            "--tb=no",
        )
        session.run(*run_command, external=True)
    else:
        session.run(*START_APP, external=True)
        session.run(*LOGIN, external=True)
        run_command = (
            *EXEC,
            "pytest",
            coverage_arg,
            "tests/ctl/",
            "-m",
            mark,
            "--full-trace",
        )
        session.run(*run_command, external=True)


def pytest_ops(
    session: Session,
    mark: str,
    coverage_arg: str,
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
                coverage_arg,
                API_TEST_DIR,
                "-m",
                "not integration and not integration_external and not integration_saas",
            )
        elif subset_dir == "non-api":
            run_command = (
                *EXEC,
                "pytest",
                coverage_arg,
                OPS_TEST_DIR,
                f"--ignore={API_TEST_DIR}",
                "-m",
                "not integration and not integration_external and not integration_saas",
            )
        else:
            run_command = (
                *EXEC,
                "pytest",
                coverage_arg,
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
            pytest_path=OPS_TEST_DIR,
        )
    elif mark == "external_datastores":
        session.run(*START_APP, external=True)
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
            CI_ARGS_EXEC,
            CONTAINER_NAME,
            "pytest",
            coverage_arg,
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
            "VAULT_ADDR",
            "-e",
            "VAULT_NAMESPACE",
            "-e",
            "VAULT_TOKEN",
            "-e",
            "FIDES__DEV_MODE=false",
            CI_ARGS_EXEC,
            CONTAINER_NAME,
            "pytest",
            "--reruns",
            "3",
            coverage_arg,
            OPS_TEST_DIR,
            "-m",
            "integration_saas",
            "--tb=no",
        )
        session.run(*run_command, external=True)
