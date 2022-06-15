"""Contains the nox sessions for running development environments."""
import nox
from constants_nox import RUN, START_APP_EXTERNAL, START_APP_UI
from docker_nox import build


@nox.session()
def dev(session: nox.Session) -> None:
    """Spin up the entire application and open a development shell."""
    build(session, "dev")
    build(session, "ui")
    session.notify("teardown")
    if session.posargs == ["external"]:
        session.run(*START_APP_EXTERNAL, external=True)
    else:
        session.run(*START_APP_UI, external=True)
    run_shell = (*RUN, "/bin/bash")
    session.run(*run_shell, external=True)
