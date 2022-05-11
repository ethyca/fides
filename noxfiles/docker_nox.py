"""Contains the nox sessions for docker-related tasks."""
import nox
from constants_nox import IMAGE, IMAGE_LATEST, IMAGE_LOCAL, get_current_tag


def get_current_image() -> str:
    """Returns the current image tag"""
    return f"{IMAGE}:{get_current_tag()}"


@nox.session()
def build(session: nox.Session) -> None:
    """Build the Docker container for fidesctl."""
    session.run(
        "docker",
        "build",
        "--target=prod",
        "--tag",
        get_current_image(),
        ".",
        external=True,
    )


@nox.session()
def build_local(session: nox.Session) -> None:
    """Build the Docker container for fidesctl tagged 'local'."""
    session.run(
        "docker",
        "build",
        "--target=dev",
        "--tag",
        IMAGE_LOCAL,
        ".",
        "--build-arg",
        "PYTHON_VERSION=3.9",
        external=True,
    )


@nox.session()
def build_local_prod(session: nox.Session) -> None:
    """Build the Docker container for fidesctl tagged 'local' with the prod stage target."""
    session.run(
        "docker", "build", "--target=prod", "--tag", IMAGE_LOCAL, ".", external=True
    )


@nox.session()
@nox.parametrize(
    "python_version",
    [
        nox.param("3.8", id="3.8"),
        nox.param("3.9", id="3.9"),
        nox.param("3.10", id="3.10"),
    ],
)
def build_local_prod_python_versions(session: nox.Session, python_version: str) -> None:
    """Build the Docker container for fidesctl tagged 'local' with the prod stage target."""
    IMAGE_VERSION = f"{IMAGE}:local" + python_version
    session.run(
        "docker",
        "build",
        "--build-arg",
        f"PYTHON_VERSION={python_version}",
        "--target=prod",
        "--tag",
        IMAGE_VERSION,
        ".",
        external=True,
    )


@nox.session()
def push(session: nox.Session) -> None:
    """Push the fidesctl Docker image to Dockerhub."""
    session.run("docker", "tag", get_current_image(), IMAGE_LATEST, external=True)
    session.run("docker", "push", IMAGE, external=True)
    session.run("docker", "push", IMAGE_LATEST, external=True)
