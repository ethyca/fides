"""Contains the nox sessions for running development environments."""
import nox

from constants_nox import (
    COMPOSE_SERVICE_NAME,
    RUN,
    RUN_NO_DEPS,
    START_APP,
    START_APP_EXTERNAL,
)
from docker_nox import build
from utils_nox import COMPOSE_DOWN_VOLUMES
from run_infrastructure import ALL_DATASTORES, run_infrastructure


@nox.session()
def dev(session: nox.Session) -> None:
    """Spin up the application. Uses positional arguments for additional features."""

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

    session.log(
        "Tearing down existing containers & volumes to prepare test environment..."
    )
    try:
        session.run(*COMPOSE_DOWN_VOLUMES, external=True)
    except nox.command.CommandFailed:
        session.error(
            "Failed to cleanly teardown existing containers & volumes. Please exit out of all other nox sessions and try again"
        )
    session.notify("teardown", posargs=["volumes"])

    session.log("Building images...")
    build(session, "dev")
    build(session, "admin_ui")
    build(session, "privacy_center")

    session.log(
        "Starting the application with example databases defined in docker-compose.integration-tests.yml..."
    )
    session.run(*START_APP_EXTERNAL, "fides-ui", "fides-pc", external=True)

    session.log(
        "Running example setup scripts for DSR Automation tests... (scripts/load_examples.py)"
    )
    session.run(
        *RUN_NO_DEPS,
        "fides",
        "--load-only",
        external=True,
    )

    session.log(
        "Pushing example resources for Data Mapping tests... (demo_resources/*)"
    )
    session.run(*RUN_NO_DEPS, "fides", "push", "demo_resources/", external=True)

    session.log("****************************************")
    session.log("*                                      *")
    session.log("*        FIDES TEST ENVIRONMENT        *")
    session.log("*                                      *")
    session.log("****************************************")
    session.log("")
    session.log("Fides Admin UI running at http://localhost:3000")
    session.log("Fides Privacy Center running at http://localhost:3001")
    session.log("Example Postgres Database running at localhost:6432")
    session.log("Example Mongo Database running at localhost:27017")
    session.log("Username: 'fidestest', Password: 'Apassword1!")
    session.log("Opening Fides CLI shell...")
    session.run(*RUN_NO_DEPS, "/bin/bash", external=True)


@nox.session()
def quickstart(session: nox.Session) -> None:
    """Run the quickstart tutorial."""
    build(session, "dev")
    session.notify("teardown")
    run_infrastructure(datastores=["mongodb", "postgres"], run_quickstart=True)
