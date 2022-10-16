"""Contains the nox sessions for running development environments."""
import nox
from os.path import isfile

from constants_nox import (
    COMPOSE_SERVICE_NAME,
    RUN,
    START_APP,
    START_APP_EXTERNAL,
    RUN_NO_DEPS,
)
from utils_nox import teardown
from docker_nox import build
from run_infrastructure import ALL_DATASTORES, run_infrastructure
from utils_nox import check_docker_compose_version, check_docker_version


@nox.session()
def dev(session: nox.Session) -> None:
    """Spin up the application. Uses positional arguments for additional features."""
    check_docker_compose_version(session)
    check_docker_version(session)

    build(session, "dev")
    session.notify("teardown")

    datastores = [
        datastore for datastore in session.posargs if datastore in ALL_DATASTORES
    ] or None

    if "ui" in session.posargs:
        build(session, "admin_ui")
        session.run("docker", "compose", "up", "-d", "fides-ui", external=True)

    if "pc" in session.posargs:
        build(session, "privacy_center")
        session.run("docker", "compose", "up", "-d", "fides-pc", external=True)

    open_shell = "shell" in session.posargs
    if not datastores:
        if open_shell:
            session.run(*START_APP, external=True)
            session.run(*RUN, "/bin/bash", external=True)
        else:
            session.run("docker", "compose", "up", COMPOSE_SERVICE_NAME, external=True)
    else:
        # Run the webserver with additional datastores
        run_infrastructure(
            open_shell=open_shell, run_application=True, datastores=datastores
        )


@nox.session()
def test_env(session: nox.Session) -> None:
    """Spins up a comprehensive test environment seeded with data."""
    secrets_file_path = "./scripts/setup/load_example_secrets.py"
    if not isfile(secrets_file_path):
        session.error(
            f"No secrets file found at {secrets_file_path}! The generic secrets file is available in 1Password by searching 'load_example_secrets.py'"
        )

    session.notify("teardown", posargs=["volumes"])

    session.log("Building images...")
    build(session, "dev")
    build(session, "admin_ui")
    build(session, "privacy_center")

    session.log("Starting the application with example databases...")
    # NOTE: Example databases must exist in docker-compose.integration-tests.yml
    session.run(*START_APP_EXTERNAL, "fides-ui", "fides-pc", external=True)

    session.log("Seeding example data for DSR Automation tests...")
    session.warn("WARNING: Stripe connector is disabled due to errors... (see load_examples.py)")
    session.run(
        *RUN_NO_DEPS,
        "python",
        f"/fides/scripts/load_examples.py",
        external=True,
    )

    session.log("Seeding example data for Data Mapping tests...")
    session.run(*RUN_NO_DEPS, "fides", "push", "demo_resources/", external=True)

    session.log("****************************************")
    session.log("*                                      *")
    session.log("*        FIDES TEST ENVIRONMENT        *")
    session.log("*                                      *")
    session.log("****************************************")
    session.log("")
    session.log("Fides Admin UI running at http://localhost:3000")
    session.log("Fides Privacy Center running at http://localhost:3001")
    session.log("Example Postgres Database running at postgres://localhost:6432")
    session.log("Example Mongo Database running at postgres://localhost:27017")
    session.log("Opening Fides CLI shell...")
    session.run(*RUN_NO_DEPS, "/bin/bash", external=True)


@nox.session()
def quickstart(session: nox.Session) -> None:
    """Run the quickstart tutorial."""
    build(session, "dev")
    session.notify("teardown")
    run_infrastructure(datastores=["mongodb", "postgres"], run_quickstart=True)
