"""Contains the nox sessions for running development environments."""
import nox
from constants_nox import (
    COMPOSE_FILE,
    IMAGE_NAME,
    INTEGRATION_COMPOSE_FILE,
    RUN,
    START_APP,
)
from docker_nox import build_local


@nox.session()
def reset_db(session: nox.Session) -> None:
    """Reset the database."""
    build_local(session)
    session.notify("teardown")
    session.run(*START_APP, external=True)
    reset_db_command = (*RUN, "fidesctl", "db", "reset", "-y")
    session.run(*reset_db_command, external=True)


@nox.session()
def api(session: nox.Session) -> None:
    """Spin up the webserver."""
    build_local(session)
    session.notify("teardown")
    run_in_background = ("docker-compose", "up", IMAGE_NAME)
    session.run(*run_in_background, external=True)

@nox.session()
def ui(session: nox.Session) -> None:
    """Spin up the frontend server in development mode"""
    npm_install = ("npm", "install")
    npm_run = ("npm","run", "dev")
    with session.chdir("clients/admin-ui"):
        session.run(*npm_install, external=True)
        session.run(*npm_run, external=True)

@nox.session()
def cli(session: nox.Session) -> None:
    """Spin up a local development shell."""
    build_local(session)
    session.notify("teardown")
    session.run(*START_APP, external=True)
    run_shell = (*RUN, "/bin/bash")
    session.run(*run_shell, external=True)


@nox.session()
def cli_integration(session: nox.Session) -> None:
    """Spin up a local development shell with integration images spun up."""
    build_local(session)
    session.notify("teardown")
    session.run(
        "docker-compose",
        "-f",
        COMPOSE_FILE,
        "-f",
        INTEGRATION_COMPOSE_FILE,
        "up",
        "-d",
        IMAGE_NAME,
        external=True,
    )
    run_shell = (*RUN, "/bin/bash")
    session.run(*run_shell, external=True)


@nox.session()
def db_up(session: nox.Session) -> None:
    """Spin up the application database in the background."""
    run_command = ("docker-compose", "up", "-d", "fidesctl-db")
    session.run(*run_command, external=True)
