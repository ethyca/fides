"""Contains the nox sessions for running development environments."""
import nox
from constants_nox import ANALYTICS_OPT_OUT, COMPOSE_SERVICE_NAME, RUN
from docker_nox import build
from run_infrastructure import run_infrastructure


@nox.session()
def dev(session: nox.Session) -> None:
    """Spin up the entire application and open a development shell."""
    build(session, "dev")
    session.notify("teardown")
    datastores = session.posargs or None
    if not datastores:
        # Run the webserver without integrations
        session.run(*RUN, "/bin/bash", external=True)
    else:
        # Run the webserver with additional datastores
        run_infrastructure(open_shell=True, datastores=datastores)


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
