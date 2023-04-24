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
from run_infrastructure import OPS_TEST_DIR, run_infrastructure


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
    """Runs any tests of nox commands themselves"""
    # the nox tests don't run with coverage, override the provided arg
    coverage_arg = "--no-cov"
    session.notify("teardown")
    session.run(*START_APP, external=True)
    run_command = (*EXEC, "pytest", coverage_arg, "--noconftest", "tests/nox/")
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
        )
        session.run(*run_command, external=True)


def pytest_ops(session: Session, mark: str, coverage_arg: str) -> None:
    """Runs fidesops tests."""
    session.notify("teardown")
    if mark == "unit":
        session.run(*START_APP, external=True)
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
            "REDSHIFT_TEST_URI",
            "-e",
            "SNOWFLAKE_TEST_URI",
            "-e",
            "REDSHIFT_TEST_DB_SCHEMA",
            "-e",
            "BIGQUERY_KEYFILE_CREDS",
            "-e",
            "BIGQUERY_DATASET",
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
            coverage_arg,
            OPS_TEST_DIR,
            "-m",
            "integration_saas",
            "--tb=no",
        )
        session.run(*run_command, external=True)
