"""Contains the nox sessions for running development environments."""
import nox

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
    session.notify("teardown", posargs=["volumes"])
    build(session, "test")
    build(session, "admin_ui")
    build(session, "privacy_center")

    # Run the quickstart to seed data
    run_infrastructure(datastores=["mongodb", "postgres"], run_quickstart=True)
    input("Quickstart complete, press any key to continue...")
    teardown(session)

    # Spin up the app + UI components and load ctl demo resources and a shell
    session.run(*START_APP_EXTERNAL, "fides-ui", "fides-pc", external=True)
    session.run(*RUN_NO_DEPS, "fides", "push", "demo_resources/", external=True)
    session.run(*RUN_NO_DEPS, "/bin/bash", external=True)


@nox.session()
def quickstart(session: nox.Session) -> None:
    """Run the quickstart tutorial."""
    build(session, "dev")
    session.notify("teardown")
    run_infrastructure(datastores=["mongodb", "postgres"], run_quickstart=True)
