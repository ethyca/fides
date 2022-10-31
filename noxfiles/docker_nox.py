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
    IMAGE_SAMPLE,
    PRIVACY_CENTER_IMAGE,
    SAMPLE_APP_IMAGE,
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
        nox.param("prod", id="prod"),
        nox.param("sample", id="sample"),
        nox.param("test", id="test"),
        nox.param("admin_ui", id="admin-ui"),
        nox.param("privacy_center", id="privacy-center"),
    ],
)
def build(session: nox.Session, image: str, machine_type: str = "") -> None:
    """Build the Docker containers."""
    build_platform = get_platform(session.posargs)

    # This check needs to be here so it has access to the session to throw an error
    if image == "prod":
        try:
            import git  # pylint: disable=unused-import
        except ModuleNotFoundError:
            session.error(
                "Building the prod image requires the GitPython module! Please run 'pip install gitpython' and try again"
            )

    # The lambdas are a workaround to lazily evaluate get_current_image
    # This allows the dev deployment to run without requirements
    build_matrix = {
        "prod": {"tag": get_current_image, "target": "prod"},
        "dev": {"tag": lambda: IMAGE_LOCAL, "target": "dev"},
        "sample": {"tag": lambda: IMAGE_SAMPLE, "target": "prod"},
        "test": {"tag": lambda: IMAGE_LOCAL, "target": "prod"},
        "admin_ui": {"tag": lambda: IMAGE_LOCAL_UI, "target": "frontend"},
    }

    # When building an image for release (either the "prod" or "sample"
    # targets), ensure we also build the extra apps:
    #   ethyca/fides-privacy-center
    #   ethyca/fides-sample-app
    #
    # This is because these images aren't built via the regular build matrix,
    # which is used to produce various tags of the main ethyca/fides image
    #
    # TODO: this is messy, and could be integrated alongside ethyca/fides
    # instead
    if image in ("sample", "prod"):
        if image == "prod":
            tag_name = get_current_tag()
        if image == "sample":
            tag_name = "sample"
        privacy_center_image_tag = f"{PRIVACY_CENTER_IMAGE}:{tag_name}"
        sample_app_image_tag = f"{SAMPLE_APP_IMAGE}:{tag_name}"

        session.log("Building extra images:")
        session.log(f"  - {privacy_center_image_tag}")
        session.log(f"  - {sample_app_image_tag}")
        session.run(
            "docker",
            "build",
            "clients/privacy-center",
            "--tag",
            privacy_center_image_tag,
            external=True,
        )
        session.run(
            "docker",
            "build",
            "src/fides/data/sample_project/cookie_house",
            "--tag",
            sample_app_image_tag,
            external=True,
        )

    # Allow building the fides-privacy-center:local image directly when
    # requested (for development purposes)
    if image == "privacy_center":
        session.run(
            "docker",
            "build",
            "clients/privacy-center",
            "--tag",
            "ethyca/fides-privacy-center:local",
            external=True,
        )
    else:
        # Build the main ethyca/fides image
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
