"""Contains the nox sessions for docker-related tasks."""
import platform
from typing import List, Tuple

import nox

from constants_nox import (
    IMAGE,
    IMAGE_DEV,
    IMAGE_LATEST,
    IMAGE_LOCAL,
    IMAGE_LOCAL_PC,
    IMAGE_LOCAL_UI,
    PRIVACY_CENTER_IMAGE,
    SAMPLE_APP_IMAGE,
)
from git_nox import get_current_tag, recognized_tag

DOCKER_PLATFORM_MAP = {
    "amd64": "linux/amd64",
    "arm64": "linux/arm64",
    "x86_64": "linux/amd64",
}
DOCKER_PLATFORMS = "linux/amd64,linux/arm64"


def verify_git_tag(session: nox.Session) -> str:
    """
    Get the git tag for HEAD and validate it before using it.
    """
    existing_commit_tag = get_current_tag(existing=True)
    if existing_commit_tag is None:
        session.error(
            "Did not find an existing git tag on the current commit, not pushing git-tag images"
        )

    if not recognized_tag(existing_commit_tag):
        session.error(
            f"Existing git tag {existing_commit_tag} is not a recognized tag, not pushing git-tag images"
        )

    session.log(
        f"Found git tag {existing_commit_tag} on the current commit, pushing corresponding git-tag images!"
    )
    return existing_commit_tag


def generate_multiplatform_buildx_command(
    image_tags: List[str], docker_build_target: str, dockerfile_path: str = "."
) -> Tuple[str, ...]:
    """
    Generate the command for building and publishing a multiplatform image.

    See tests for example usage.
    """
    buildx_command: Tuple[str, ...] = (
        "docker",
        "buildx",
        "build",
        "--push",
        f"--target={docker_build_target}",
        "--platform",
        DOCKER_PLATFORMS,
        dockerfile_path,
    )

    for tag in image_tags:
        buildx_command += ("--tag", tag)

    return buildx_command


def get_current_image() -> str:
    """Returns the current image tag"""
    return f"{IMAGE}:{get_current_tag()}"


def get_platform(posargs: List[str]) -> str:
    """
    Calculate the CPU platform or get it from the
    positional arguments.
    """
    if "amd64" in posargs:
        return DOCKER_PLATFORM_MAP["amd64"]
    if "arm64" in posargs:
        return DOCKER_PLATFORM_MAP["arm64"]
    return DOCKER_PLATFORM_MAP[platform.machine().lower()]


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
        dev = Build the fides webserver/CLI, tagged as `local` and with an editable pip install of Fides.
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
        "privacy_center": {"tag": lambda: IMAGE_LOCAL_PC, "target": "frontend"},
    }

    # When building for release, there are additional images that need
    # to get built. These images are outside of the primary `ethyca/fides`
    # image so some additional logic is required.
    if image in ("test", "prod"):
        if image == "prod":
            tag_name = get_current_tag()
        if image == "test":
            tag_name = "local"
        session.log("Building extra images:")
        privacy_center_image_tag = f"{PRIVACY_CENTER_IMAGE}:{tag_name}"
        session.log(f"  - {privacy_center_image_tag}")
        session.run(
            "docker",
            "build",
            "--target=prod_pc",
            "--platform",
            build_platform,
            "--tag",
            privacy_center_image_tag,
            ".",
            external=True,
        )
        sample_app_image_tag = f"{SAMPLE_APP_IMAGE}:{tag_name}"
        session.log(f"  - {sample_app_image_tag}")
        session.run(
            "docker",
            "build",
            "clients/sample-app",
            "--platform",
            build_platform,
            "--tag",
            sample_app_image_tag,
            external=True,
        )

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


def push_prod(session: nox.Session) -> None:
    """
    Contains the logic for pushing the suite of 'prod' images.

    Pushed Image Examples:
      - ethyca/fides:2.0.0
      - ethyca/fides:latest

      - ethyca/fides-privacy-center:2.0.0
      - ethyca/fides-privacy-center:latest

      - ethyca/fides-sample-app:2.0.0
      - ethyca/fides-sample-app:latest
    """
    fides_image_name = get_current_image()
    privacy_center_image_name = f"{PRIVACY_CENTER_IMAGE}:{get_current_tag()}"
    sample_app_image_name = f"{SAMPLE_APP_IMAGE}:{get_current_tag()}"

    privacy_center_latest = f"{PRIVACY_CENTER_IMAGE}:latest"
    sample_app_latest = f"{SAMPLE_APP_IMAGE}:latest"

    fides_buildx_command = generate_multiplatform_buildx_command(
        [fides_image_name, IMAGE_LATEST], docker_build_target="prod"
    )
    session.run(*fides_buildx_command, external=True)

    privacy_center_buildx_command = generate_multiplatform_buildx_command(
        [privacy_center_image_name, privacy_center_latest],
        docker_build_target="prod_pc",
    )
    session.run(*privacy_center_buildx_command, external=True)

    sample_app_buildx_command = generate_multiplatform_buildx_command(
        [sample_app_image_name, sample_app_latest],
        docker_build_target="prod",
        dockerfile_path="clients/sample-app",
    )
    session.run(*sample_app_buildx_command, external=True)


def push_dev(session: nox.Session) -> None:
    """
    Push the bleeding-edge `dev` images.

    Pushed Image Examples:
      - ethyca/fides:dev
      - ethyca/fides-privacy-center:dev
      - ethyca/fides-sample-app:dev
    """
    privacy_center_dev = f"{PRIVACY_CENTER_IMAGE}:dev"
    sample_app_dev = f"{SAMPLE_APP_IMAGE}:dev"

    fides_buildx_command = generate_multiplatform_buildx_command(
        [IMAGE_DEV], docker_build_target="prod"
    )
    session.run(*fides_buildx_command, external=True)

    privacy_center_buildx_command = generate_multiplatform_buildx_command(
        [privacy_center_dev],
        docker_build_target="prod_pc",
    )
    session.run(*privacy_center_buildx_command, external=True)

    sample_app_buildx_command = generate_multiplatform_buildx_command(
        [sample_app_dev],
        docker_build_target="prod",
        dockerfile_path="clients/sample-app",
    )
    session.run(*sample_app_buildx_command, external=True)


def push_git_tag(session: nox.Session) -> None:
    """
    Push an image with the tag of our current commit.

    If we have an existing git tag on the current commit, we push up
    a set of images that's tagged specifically with this git tag.

    This publishes images that correspond to commits that have been explicitly tagged,
    e.g. RC builds, `beta` tags on `main`, `alpha` tags for feature branch builds.

    Pushed Image Examples:
    - ethyca/fides:{current_head_git_tag}
    - ethyca/fides-privacy-center:{current_head_git_tag}
    - ethyca/fides-sample-app:{current_head_git_tag}
    """

    existing_commit_tag = verify_git_tag(session)
    custom_image_tag = f"{IMAGE}:{existing_commit_tag}"
    privacy_center_dev = f"{PRIVACY_CENTER_IMAGE}:{existing_commit_tag}"
    sample_app_dev = f"{SAMPLE_APP_IMAGE}:{existing_commit_tag}"

    # Publish
    fides_buildx_command = generate_multiplatform_buildx_command(
        [custom_image_tag], docker_build_target="prod"
    )
    session.run(*fides_buildx_command, external=True)

    privacy_center_buildx_command = generate_multiplatform_buildx_command(
        [privacy_center_dev],
        docker_build_target="prod_pc",
    )
    session.run(*privacy_center_buildx_command, external=True)

    sample_app_buildx_command = generate_multiplatform_buildx_command(
        [sample_app_dev],
        docker_build_target="prod",
        dockerfile_path="clients/sample-app",
    )
    session.run(*sample_app_buildx_command, external=True)


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

    NOTE: This command also handles building images, including for multiple supported architectures.
    """

    # Create the buildx builder
    session.run(
        "docker",
        "buildx",
        "create",
        "--name",
        "fides_builder",
        "--bootstrap",
        "--use",
        external=True,
        success_codes=[0, 1],
    )

    if tag == "dev":
        push_dev(session=session)

    if tag == "git-tag":
        push_git_tag(session=session)

    if tag == "prod":
        push_prod(session=session)
