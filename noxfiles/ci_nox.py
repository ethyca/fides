"""Contains the nox sessions used during CI checks."""
from functools import partial
from os import environ
from typing import Callable, Dict

import nox

from constants_nox import IMAGE_NAME, RUN, RUN_NO_DEPS, START_APP, WITH_TEST_CONFIG
from test_setup_nox import pytest_ctl, pytest_lib, pytest_ops
from utils_nox import install_requirements


###################
## Static Checks ##
###################
@nox.session()
def static_checks(session: nox.Session) -> None:
    """Run the static checks only."""
    session.notify("black")
    session.notify("isort")
    session.notify("xenon")
    session.notify("mypy")
    session.notify("pylint")


@nox.session()
@nox.parametrize(
    "mode",
    [
        nox.param("fix", id="fix"),
        nox.param("check", id="check"),
    ],
)
def black(session: nox.Session, mode: str) -> None:
    """Run the 'black' style linter."""
    install_requirements(session)
    command = ("black", "src", "tests", "noxfiles", "scripts", "noxfile.py")
    if mode == "check":
        command = (*command, "--check")
    session.run(*command)


@nox.session()
@nox.parametrize(
    "mode",
    [
        nox.param("fix", id="fix"),
        nox.param("check", id="check"),
    ],
)
def isort(session: nox.Session, mode: str) -> None:
    """Run the 'isort' import linter."""
    install_requirements(session)
    command = ("isort", "src", "tests", "noxfiles", "scripts", "noxfile.py")
    if mode == "check":
        command = (*command, "--check")
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
    command = ("pylint", "src", "noxfiles", "noxfile.py")
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


##################
## Fides Checks ##
##################
@nox.session()
def check_install(session: nox.Session) -> None:
    """Check that fides installs works correctly."""
    session.install(".")

    REQUIRED_ENV_VARS = {
        "FIDES__SECURITY__APP_ENCRYPTION_KEY": "OLMkv91j8DHiDAULnK5Lxx3kSCov30b3",
        "FIDES__SECURITY__OAUTH_ROOT_CLIENT_ID": "fidesadmin",
        "FIDES__SECURITY__OAUTH_ROOT_CLIENT_SECRET": "fidesadminsecret",
        "FIDES__SECURITY__DRP_JWT_SECRET": "secret",
    }

    run_command = ("fides", "--version")
    session.run(*run_command, env=REQUIRED_ENV_VARS)

    run_command = ("python", "-c", "from fides.api.main import start_webserver")
    session.run(*run_command, env=REQUIRED_ENV_VARS)


@nox.session()
def check_fides_annotations(session: nox.Session) -> None:
    """Run a fides evaluation."""
    run_command = (*RUN_NO_DEPS, "fides", "--local", *(WITH_TEST_CONFIG), "evaluate")
    session.run(*run_command, external=True)


@nox.session()
def fides_db_scan(session: nox.Session) -> None:
    """Scan the fides application database to check for dataset discrepancies."""
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


@nox.session()
def minimal_config_startup(session: nox.Session) -> None:
    """
    Check that the server can start successfully with a minimal
    configuration set through environment vairables.
    """
    session.notify("teardown")
    compose_file = "docker/docker-compose.minimal-config.yml"
    start_command = (
        "docker",
        "compose",
        "-f",
        compose_file,
        "up",
        "--wait",
        "-d",
        IMAGE_NAME,
    )
    session.run(*start_command, external=True)


############
## Pytest ##
############
TEST_GROUPS = [
    nox.param("ctl-unit", id="ctl-unit"),
    nox.param("ctl-not-external", id="ctl-not-external"),
    nox.param("ctl-integration", id="ctl-integration"),
    nox.param("ctl-external", id="ctl-external"),
    nox.param("ops-unit", id="ops-unit"),
    nox.param("ops-integration", id="ops-integration"),
    nox.param("ops-external-datastores", id="ops-external-datastores"),
    nox.param("ops-saas", id="ops-saas"),
    nox.param("lib", id="lib"),
]

TEST_MATRIX: Dict[str, Callable] = {
    "ctl-unit": partial(pytest_ctl, mark="unit"),
    "ctl-not-external": partial(pytest_ctl, mark="not external"),
    "ctl-integration": partial(pytest_ctl, mark="integration"),
    "ctl-external": partial(pytest_ctl, mark="external"),
    "ops-unit": partial(pytest_ops, mark="unit"),
    "ops-integration": partial(pytest_ops, mark="integration"),
    "ops-external-datastores": partial(pytest_ops, mark="external_datastores"),
    "ops-saas": partial(pytest_ops, mark="saas"),
    "lib": pytest_lib,
}
TEST_REPORTER_URL = (
    "https://codeclimate.com/downloads/test-reporter/test-reporter-latest-linux-amd64"
)


def validate_test_matrix(session: nox.Session) -> None:
    """
    Validates that all test groups are represented in the test matrix.
    """
    test_group_ids = sorted([str(param) for param in TEST_GROUPS])
    test_matrix_keys = sorted(TEST_MATRIX.keys())

    if not test_group_ids == test_matrix_keys:
        session.error("TEST_GROUPS and TEST_MATRIX do not match")


@nox.session()
def collect_tests(session: nox.Session) -> None:
    """
    Collect all pytests as a validity check.
    """
    session.install(".")
    install_requirements(session)
    command = ("pytest", "tests/", "--collect-only")
    session.run(*command)


@nox.session()
@nox.parametrize(
    "test_group",
    TEST_GROUPS,
)
def pytest(session: nox.Session, test_group: str) -> None:
    """
    Runs Pytests.

    As new TEST_GROUPS are added, the TEST_MATRIX must also be updated.
    """
    session.notify("teardown")

    validate_test_matrix(session)
    coverage_arg = "--cov-report=xml"
    TEST_MATRIX[test_group](session=session, coverage_arg=coverage_arg)


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
