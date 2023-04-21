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
    PRIVACY_CENTER_IMAGE,
    SAMPLE_APP_IMAGE,
)
from git_nox import get_current_tag, recognized_tag


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
        nox.param("admin_ui", id="admin-ui"),
        nox.param("dev", id="dev"),
        nox.param("privacy_center", id="privacy-center"),
        nox.param("prod", id="prod"),
        nox.param("test", id="test"),
    ],
)
def build(session: nox.Session, image: str, machine_type: str = "") -> None:
    """
    Build various Docker images.

    Params:
        admin-ui = Build the Next.js Admin UI application.
        dev = Build the fides webserver/CLI, tagged as `local`.
        privacy-center = Build the Next.js Privacy Center application.
        prod = Build the fides webserver/CLI and tag it as the current application version.
        test = Build the fides webserver/CLI the same as `prod`, but tag it as `local`.
    """
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
        "test": {"tag": lambda: IMAGE_LOCAL, "target": "prod"},
        "dev": {"tag": lambda: IMAGE_LOCAL, "target": "dev"},
        "admin_ui": {"tag": lambda: IMAGE_LOCAL_UI, "target": "frontend"},
    }

    # When building for release, there are additional images that need
    # to get built. These images are outside of the primary `ethyca/fides`
    # image so some additional logic is required.
    if image in ("test", "prod"):
        if image == "prod":
            tag_name = get_current_tag()
        if image == "test":
            tag_name = "local"
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
            "clients/sample-app",
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
        nox.param("git-tag", id="git-tag"),
    ],
)
def push(session: nox.Session, tag: str) -> None:
    """
    Push the main image & extra apps to DockerHub:
      - ethyca/fides
      - ethyca/fides-privacy-center
      - ethyca/fides-sample-app

    Params:

    prod - Tags images with the current version of the application
    dev - Tags images with `dev`
    git-tag - Tags images with the git tag of the current commit, if it exists

    NOTE: Expects these to first be built via 'build(prod)'
    """
    fides_image_prod = get_current_image()
    privacy_center_prod = f"{PRIVACY_CENTER_IMAGE}:{get_current_tag()}"
    sample_app_prod = f"{SAMPLE_APP_IMAGE}:{get_current_tag()}"

    if tag == "dev":
        # Push the ethyca/fides image, tagging with :dev
        session.run("docker", "tag", fides_image_prod, IMAGE_DEV, external=True)
        session.run("docker", "push", IMAGE_DEV, external=True)

        # Push the extra images, tagging with :dev
        #   - ethyca/fides-privacy-center:dev
        #   - ethyca/fides-sample-app:dev
        privacy_center_dev = f"{PRIVACY_CENTER_IMAGE}:dev"
        sample_app_dev = f"{SAMPLE_APP_IMAGE}:dev"
        session.run(
            "docker", "tag", privacy_center_prod, privacy_center_dev, external=True
        )
        session.run("docker", "push", privacy_center_dev, external=True)
        session.run("docker", "tag", sample_app_prod, sample_app_dev, external=True)
        session.run("docker", "push", sample_app_dev, external=True)

    if tag == "git-tag":
        # if we have an existing git tag on the current commit, we push up
        # a set of images that's tagged specifically with this git tag.
        # this publishes images that correspond to commits that have been explicitly tagged,
        # e.g. RC builds, `beta` tags on `main`, `alpha` tags for feature branch builds.
        existing_commit_tag = get_current_tag(existing=True)
        if existing_commit_tag is None:
            session.log(
                "Did not find an existing git tag on the current commit, not pushing git-tag images"
            )
            return

        if not recognized_tag(existing_commit_tag):
            session.log(
                f"Existing git tag {existing_commit_tag} is not a recognized tag, not pushing git-tag images"
            )
            return

        session.log(
            f"Found git tag {existing_commit_tag} on the current commit, pushing corresponding git-tag images!"
        )
        custom_image_tag = f"{IMAGE}:{existing_commit_tag}"
        # Push the ethyca/fides image, tagging with :{current_head_git_tag}
        session.run("docker", "tag", fides_image_prod, custom_image_tag, external=True)
        session.run("docker", "push", custom_image_tag, external=True)

        # Push the extra images, tagging with :{current_head_git_tag}
        #   - ethyca/fides-privacy-center:{current_head_git_tag}
        #   - ethyca/fides-sample-app:{current_head_git_tag}
        privacy_center_dev = f"{PRIVACY_CENTER_IMAGE}:{existing_commit_tag}"
        sample_app_dev = f"{SAMPLE_APP_IMAGE}:{existing_commit_tag}"
        session.run(
            "docker", "tag", privacy_center_prod, privacy_center_dev, external=True
        )
        session.run("docker", "push", privacy_center_dev, external=True)
        session.run("docker", "tag", sample_app_prod, sample_app_dev, external=True)
        session.run("docker", "push", sample_app_dev, external=True)

    if tag == "prod":
        # Example: "ethyca/fides:2.0.0" and "ethyca/fides:latest"
        session.run("docker", "tag", fides_image_prod, IMAGE_LATEST, external=True)
        session.run("docker", "push", IMAGE_LATEST, external=True)
        session.run("docker", "push", fides_image_prod, external=True)

        # Example:
        #   - ethyca/fides-privacy-center:2.0.0
        #   - ethyca/fides-privacy-center:latest
        #   - ethyca/fides-sample-app:2.0.0
        #   - ethyca/fides-sample-app:latest
        privacy_center_latest = f"{PRIVACY_CENTER_IMAGE}:latest"
        sample_app_latest = f"{SAMPLE_APP_IMAGE}:latest"
        session.run(
            "docker", "tag", privacy_center_prod, privacy_center_latest, external=True
        )
        session.run("docker", "push", privacy_center_latest, external=True)
        session.run("docker", "push", privacy_center_prod, external=True)
        session.run("docker", "tag", sample_app_prod, sample_app_latest, external=True)
        session.run("docker", "push", sample_app_latest, external=True)
        session.run("docker", "push", sample_app_prod, external=True)
