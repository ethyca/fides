"""Contains the nox sessions for docker-related tasks."""
import platform
from typing import List

import nox

from constants_nox import (
    IMAGE,
    IMAGE_DEV,
    IMAGE_LATEST,
    IMAGE_LOCAL,
    IMAGE_LOCAL_UI,
)


def get_current_tag() -> str:
    """Get the current git tag."""
    from git.repo import Repo

    repo = Repo()
    git_session = repo.git()
    git_session.fetch("--force", "--tags")
    current_tag = git_session.describe("--tags", "--dirty", "--always")
    return current_tag


def get_current_image() -> str:
    """Returns the current image tag"""
    return f"{IMAGE}:{get_current_tag()}"


def get_platform(posargs: List[str]) -> str:
    """
    Calculate the CPU platform or get it from the
    positional arguments.
    """
    # Support Intel Macs
    docker_platforms = {
        "amd64": "linux/amd64",
        "arm64": "linux/arm64",
        "x86_64": "linux/amd64",
    }
    if "amd64" in posargs:
        return docker_platforms["amd64"]
    if "arm64" in posargs:
        return docker_platforms["arm64"]
    return docker_platforms[platform.machine().lower()]


@nox.session()
@nox.parametrize(
    "image",
    [
        nox.param("dev", id="dev"),
        nox.param("pc", id="pc"),
        nox.param("prod", id="prod"),
        nox.param("test", id="test"),
        nox.param("ui", id="ui"),
    ],
)
def build(session: nox.Session, image: str, machine_type: str = "") -> None:
    """Build the Docker containers."""
    build_platform = get_platform(session.posargs)

    if image == "prod":
        try:
            import git
        except ModuleNotFoundError:
            session.error(
                "Building the prod image requires the GitPython module! Please run 'pip install gitpython' and try again"
            )

    # The lambdas are a workaround to lazily evaluate get_current_image
    # This allows the dev deployment to run without needing other dev requirements
    build_matrix = {
        "prod": {"tag": get_current_image, "target": "prod"},
        "dev": {"tag": lambda: IMAGE_LOCAL, "target": "dev"},
        "test": {"tag": lambda: IMAGE_LOCAL, "target": "prod"},
        "ui": {"tag": lambda: IMAGE_LOCAL_UI, "target": "frontend"},
    }
    if image == "pc":
        session.run(
            "docker",
            "build",
            "clients/privacy-center",
            "--tag",
            "ethyca/fides-privacy-center:local",
            external=True,
        )
    else:
        target = build_matrix[image]["target"]
        tag = build_matrix[image]["tag"]
        build_command = (
            "docker",
            "build",
            f"--target={target}",
            "--platform",
            build_platform,
            "--tag",
            tag(),
            ".",
        )
        if "nocache" in session.posargs:
            build_command = (*build_command, "--no-cache")

        session.run(*build_command, external=True)


@nox.session()
@nox.parametrize(
    "tag",
    [
        nox.param("prod", id="prod"),
        nox.param("dev", id="dev"),
    ],
)
def push(session: nox.Session, tag: str) -> None:
    """Push the fidesctl Docker image to Dockerhub."""

    tag_matrix = {"prod": IMAGE_LATEST, "dev": IMAGE_DEV}

    # Push either "ethyca/fidesctl:dev" or "ethyca/fidesctl:latest"
    session.run("docker", "tag", get_current_image(), tag_matrix[tag], external=True)
    session.run("docker", "push", tag_matrix[tag], external=True)

    # Only push the tagged version if its for prod
    # Example: "ethyca/ethyca-fides:1.7.0"
    if tag == "prod":
        session.run("docker", "push", f"{IMAGE}:{get_current_tag()}", external=True)
