"""Contains the nox sessions for running development environments."""
import nox
from constants_nox import ANALYTICS_OPT_OUT, COMPOSE_SERVICE_NAME, RUN, START_APP
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
    open_shell = "shell" in session.posargs
    if not datastores:
        if open_shell:
            session.run(*START_APP, external=True)
            session.run(*RUN, "/bin/bash", external=True)
        else:
            session.run("docker-compose", "up", COMPOSE_SERVICE_NAME, external=True)
    else:
        # Run the webserver with additional datastores
        run_infrastructure(
            open_shell=open_shell, run_application=True, datastores=datastores
        )


@nox.session()
def dev_with_worker(session: nox.Session) -> None:
    """Spin up the entire application and open a development shell."""
    build(session, "dev")
    session.notify("teardown")
    session.run("docker-compose", "up", "worker", "--wait", external=True)
    session.run(
        "docker-compose",
        "run",
        *ANALYTICS_OPT_OUT,
        "-e",
        "FIDESOPS__EXECUTION__WORKER_ENABLED=True",
        COMPOSE_SERVICE_NAME,
        external=True,
    )


@nox.session()
def quickstart(session: nox.Session) -> None:
    build(session, "dev")
    session.notify("teardown")
    run_infrastructure(datastores=["mongodb", "postgres"], run_quickstart=True)
