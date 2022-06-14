"""Contains the nox sessions for running development environments."""
import nox
from constants_nox import (
    RUN,
    START_APP,
    START_APP_EXTERNAL,
)
from docker_nox import build


@nox.session()
def run(session: nox.Session) -> None:
    """Spin up the entire application and open a development shell."""
    build(session, "local")
    session.notify("teardown")
    if session.posargs == ["external"]:
        session.run(*START_APP_EXTERNAL, external=True)
    else:
        session.run(*START_APP, external=True)
    run_shell = (*RUN, "/bin/bash")
    session.run(*run_shell, external=True)
