"""Contains the nox sessions used during CI checks."""
import nox

from constants_nox import (
    CI_ARGS,
    COMPOSE_FILE,
    COMPOSE_SERVICE_NAME,
    IMAGE_NAME,
    INTEGRATION_COMPOSE_FILE,
    RUN,
    RUN_NO_DEPS,
    START_APP,
    START_APP_WITH_EXTERNAL_POSTGRES,
    WITH_TEST_CONFIG,
)
from run_infrastructure import OPS_TEST_DIR, run_infrastructure
from utils_nox import install_requirements

RUN_STATIC_ANALYSIS = (*RUN_NO_DEPS, "nox", "-s")

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
        "scripts",
    )
    session.run(*command)


@nox.session()
def isort(session: nox.Session) -> None:
    """Run the 'isort' import linter."""
    install_requirements(session)
    command = ("isort", "src", "tests", "noxfiles", "scripts", "--check")
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
        "scripts",
        "--max-absolute B",
        "--max-modules B",
        "--max-average A",
        "--ignore 'data, docs'",
        "--exclude src/fides/_version.py",
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
def check_fides_annotations(session: nox.Session) -> None:
    """Run a fidesctl evaluation."""
    if session.posargs == ["docker"]:
        run_command = (*RUN_STATIC_ANALYSIS, "check_fides_annotations")
    else:
        run_command = ("fides", "--local", *(WITH_TEST_CONFIG), "evaluate")
    session.run(*run_command, external=True)


@nox.session()
def fides_db_scan(session: nox.Session) -> None:
    """Scan the fidesctl application database to check for dataset discrepancies."""
    session.notify("teardown")
    session.run(*START_APP, external=True)
    run_command = (
        *RUN,
        "fides",
        "scan",
        "dataset",
        "db",
        "--credentials-id",
        "app_postgres",
    )
    session.run(*run_command, external=True)


# Pytest
@nox.session()
@nox.parametrize(
    "mark",
    [
        nox.param("unit", id="unit"),
        nox.param("integration", id="integration"),
        nox.param("not external", id="not-external"),
        nox.param("external", id="external"),
    ],
)
def pytest_ctl(session: nox.Session, mark: str) -> None:
    """Runs fidesctl tests."""
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
            "-d",
            IMAGE_NAME,
        )
        session.run(*start_command, external=True)
        run_command = (
            "docker",
            "compose",
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
            "-m",
            "external",
            "tests/ctl",
        )
        session.run(*run_command, external=True)
    else:
        session.run(*START_APP, external=True)
        run_command = (
            *RUN_NO_DEPS,
            "pytest",
            "tests/ctl/",
            "-m",
            mark,
        )
        session.run(*run_command, external=True)


@nox.session()
@nox.parametrize(
    "mark",
    [
        nox.param("unit", id="unit"),
        nox.param("integration", id="integration"),
        nox.param("external_datastores", id="external-datastores"),
        nox.param("saas", id="saas"),
    ],
)
def pytest_ops(session: nox.Session, mark: str) -> None:
    """Runs fidesops tests."""
    session.notify("teardown")
    if mark == "unit":
        session.run(*START_APP, external=True)
        run_command = (
            *RUN_NO_DEPS,
            "pytest",
            OPS_TEST_DIR,
            "-m",
            "not integration and not integration_external and not integration_saas",
        )
        session.run(*run_command, external=True)
    elif mark == "integration":
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
            "compose",
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
            "compose",
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


@nox.session()
@nox.parametrize(
    "dist",
    [
        nox.param("sdist", id="source"),
        nox.param("bdist_wheel", id="wheel"),
    ],
)
def python_build(session: nox.Session, dist: str) -> None:
    "Build the Python distribution."
    session.run(
        *RUN_NO_DEPS,
        "python",
        "setup.py",
        dist,
        external=True,
    )
