"""Contains the nox sessions used during CI checks."""
from time import sleep

import nox
from constants_nox import (
    INTEGRATION_COMPOSE_FILE,
    COMPOSE_SERVICE_NAME,
    CI_ARGS,
    IMAGE_NAME,
    WITH_TEST_CONFIG,
    COMPOSE_FILE,
    RUN,
    RUN_NO_DEPS,
    START_APP,
)
from run_infrastructure import OPS_TEST_DIR, run_infrastructure
from utils_nox import install_requirements

RUN_STATIC_ANALYSIS = (*RUN_NO_DEPS, "nox", "-s")

@nox.session()
def ci_suite(session: nox.Session) -> None:
    """
    Runs the CI check suite.

    Excludes external tests so that no additional secrets/tooling are required.
    """
    # Use "notify" instead of direct calls here to provide better user feedback
    session.notify("teardown")
    session.notify("build", ["test"])
    session.notify("black")
    session.notify("isort")
    session.notify("xenon")
    session.notify("mypy")
    session.notify("pylint")
    session.notify("check_install")
    session.notify("check_migrations")
    session.notify("pytest_unit")
    session.notify("pytest_integration")
    session.notify("teardown")


# Static Checks
@nox.session()
def static_checks(session: nox.Session) -> None:
    """Run the static checks only."""
    session.notify("black")
    session.notify("isort")
    session.notify("xenon")
    session.notify("mypy")
    session.notify("pylint")


@nox.session()
def black(session: nox.Session) -> None:
    """Run the 'black' style linter."""
    install_requirements(session)
    command = (
        "black",
        "--check",
        "src",
        "tests",
        "noxfiles",
    )
    session.run(*command)


@nox.session()
def isort(session: nox.Session) -> None:
    """Run the 'isort' import linter."""
    install_requirements(session)
    command = ("isort", "src", "tests", "noxfiles", "--check")
    session.run(*command)


@nox.session()
def mypy(session: nox.Session) -> None:
    """Run the 'mypy' static type checker."""
    install_requirements(session)
    command = "mypy"
    session.run(command)


@nox.session()
def pylint(session: nox.Session) -> None:
    """Run the 'pylint' code linter."""
    install_requirements(session)
    command = ("pylint", "src", "noxfiles")
    session.run(*command)


@nox.session()
def xenon(session: nox.Session) -> None:
    """Run 'xenon' code complexity monitoring."""
    install_requirements(session)
    command = (
        "xenon",
        "noxfiles",
        "src",
        "tests",
        "--max-absolute B",
        "--max-modules B",
        "--max-average A",
        "--ignore 'data, docs'",
        "--exclude src/fidesops/_version.py",
    )
    session.run(*command)


# Fidesctl Checks
@nox.session()
def check_install(session: nox.Session) -> None:
    """Check that fidesctl is installed."""
    session.install(".")
    run_command = ("fides", *(WITH_TEST_CONFIG), "--version")
    session.run(*run_command)


@nox.session()
def fidesctl(session: nox.Session) -> None:
    """Run a fidesctl evaluation."""
    if session.posargs == ["docker"]:
        run_command = (*RUN_STATIC_ANALYSIS, "fides")
    else:
        run_command = ("fidesctl", "--local", *(WITH_TEST_CONFIG), "evaluate")
    session.run(*run_command, external=True)


@nox.session()
def fidesctl_db_scan(session: nox.Session) -> None:
    """Scan the fidesctl application database to check for dataset discrepancies."""
    session.notify("teardown")
    session.run(*START_APP, external=True)
    sleep(10)
    run_command = (
        *RUN,
        "fides",
        *(WITH_TEST_CONFIG),
        "scan",
        "dataset",
        "db",
        "--connection-string",
        "postgresql+psycopg2://postgres:fidesctl@fidesctl-db:5432/fidesctl_test",
    )
    session.run(*run_command, external=True)

@nox.session()
def check_migrations(session: nox.Session) -> None:
    """Check for missing migrations."""
    check_migration_command = (
        "python",
        "-c",
        "from fidesops.ops.db.database import check_missing_migrations; from fidesops.ops.core.config import config; check_missing_migrations(config.database.sqlalchemy_database_uri);",
    )
    session.run(*RUN, *check_migration_command, external=True)


# Pytest
@nox.session()
@nox.parametrize(
    "mark",
    [
        nox.param("unit", id="unit"),
        nox.param("integration", id="integration"),
        nox.param("not external", id="not-external"),
    ],
)
def pytest(session: nox.Session, mark: str) -> None:
    """Runs tests."""
    session.notify("teardown")
    session.run(*START_APP, external=True)
    run_command = (
        *RUN_NO_DEPS,
        "pytest",
        "-x",
        "-m",
        mark,
    )
    session.run(*run_command, external=True)

@nox.session()
def pytest_unit(session: nox.Session) -> None:
    """Runs tests."""
    session.notify("teardown")
    session.run(*START_APP, external=True)
    run_command = (
        *RUN_NO_DEPS,
        "pytest",
        OPS_TEST_DIR,
        "-m",
        "not integration and not integration_external and not integration_saas",
    )
    session.run(*run_command, external=True)


@nox.session()
def pytest_external(session: nox.Session) -> None:
    """Run all tests that rely on the third-party databases and services."""
    run_command = (
        "docker-compose",
        "run",
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
        "--rm",
        CI_ARGS,
        IMAGE_NAME,
        "pytest",
        "-x",
        "-m",
        "external",
    )
    session.run(*run_command, external=True)

@nox.session()
def pytest_integration(session: nox.Session) -> None:
    """Runs tests."""
    session.notify("teardown")
    run_infrastructure(
        run_tests=True,
        analytics_opt_out=True,
        datastores=[],
        pytest_path=OPS_TEST_DIR,
    )


@nox.session()
def pytest_integration_external(session: nox.Session) -> None:
    """Run all tests that rely on the third-party databases and services."""
    session.notify("teardown")
    run_command = (
        "docker-compose",
        "run",
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
        "--rm",
        CI_ARGS,
        COMPOSE_SERVICE_NAME,
        "pytest",
        OPS_TEST_DIR,
        "-m",
        "integration_external",
    )
    session.run(*run_command, external=True)


@nox.session()
def pytest_saas(session: nox.Session) -> None:
    """Run all saas tests that rely on the third-party databases and services."""
    session.notify("teardown")
    run_command = (
        "docker-compose",
        "run",
        "-e",
        "ANALYTICS_OPT_OUT",
        "-e",
        "VAULT_ADDR",
        "-e",
        "VAULT_NAMESPACE",
        "-e",
        "VAULT_TOKEN",
        "--rm",
        CI_ARGS,
        COMPOSE_SERVICE_NAME,
        "pytest",
        OPS_TEST_DIR,
        "-m",
        "integration_saas",
    )
    session.run(*run_command, external=True)
