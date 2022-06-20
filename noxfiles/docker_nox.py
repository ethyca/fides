"""Contains the nox sessions for docker-related tasks."""
import nox
from constants_nox import (
    IMAGE,
    IMAGE_LATEST,
    IMAGE_LOCAL,
    IMAGE_LOCAL_UI,
    get_current_tag,
)


def get_current_image() -> str:
    """Returns the current image tag"""
    return f"{IMAGE}:{get_current_tag()}"


@nox.session()
@nox.parametrize(
    "image",
    [
        nox.param("prod", id="prod"),
        nox.param("dev", id="dev"),
        nox.param("test", id="test"),
        nox.param("ui", id="ui"),
    ],
)
def build(session: nox.Session, image: str) -> None:
    """Build the Docker container for fidesctl."""

    # The lambdas are a workaround to lazily evaluate get_current_image
    # This allows the dev deployment to run without needing other dev requirements
    build_matrix = {
        "prod": {"tag": get_current_image, "target": "prod"},
        "dev": {"tag": lambda: IMAGE_LOCAL, "target": "dev"},
        "test": {"tag": lambda: IMAGE_LOCAL, "target": "prod"},
        "ui": {"tag": lambda: IMAGE_LOCAL_UI, "target": "frontend"},
    }
    target = build_matrix[image]["target"]
    tag = build_matrix[image]["tag"]
    session.run(
        "docker",
        "build",
        f"--target={target}",
        "--tag",
        tag(),
        ".",
        external=True,
    )


@nox.session()
def push(session: nox.Session) -> None:
    """Push the fidesctl Docker image to Dockerhub."""
    session.run("docker", "tag", get_current_image(), IMAGE_LATEST, external=True)
    session.run("docker", "push", IMAGE, external=True)
    session.run("docker", "push", IMAGE_LATEST, external=True)
