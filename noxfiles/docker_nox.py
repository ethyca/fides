"""Contains the nox sessions for docker-related tasks."""
import nox
from constants_nox import IMAGE, IMAGE_LATEST, IMAGE_LOCAL, get_current_tag


@nox.session()
def build(session: nox.Session) -> None:
    """Build the Docker container for fidesctl."""
    session.run(
        "docker",
        "build",
        "--target=prod",
        "--tag",
        f"{IMAGE}:{get_current_tag()}",
        ".",
        external=True,
    )


@nox.session()
def build_local(session: nox.Session) -> None:
    """Build the Docker container for fidesctl tagged 'local'."""
    session.run(
        "docker", "build", "--target=dev", "--tag", IMAGE_LOCAL, ".", external=True
    )


@nox.session()
def build_local_prod(session: nox.Session) -> None:
    """Build the Docker container for fidesctl tagged 'local' with the prod stage target."""
    session.run(
        "docker", "build", "--target=prod", "--tag", IMAGE_LOCAL, ".", external=True
    )


@nox.session()
def push(session: nox.Session) -> None:
    """Push the Docker container for fidesctl."""
    session.run("docker", "tag", IMAGE, IMAGE_LATEST, external=True)
    session.run("docker", "push", IMAGE, external=True)
    session.run("docker", "push", IMAGE_LATEST, external=True)
