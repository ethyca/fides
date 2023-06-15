"""Contains the nox sessions for docker-related tasks."""
from typing import List, Tuple
from multiprocessing import Pool
from subprocess import run
from typing import Callable, Dict, List, Tuple

import nox

from constants_nox import (
    DEV_TAG_SUFFIX,
    IMAGE,
    IMAGE_LOCAL,
    IMAGE_LOCAL_PC,
    IMAGE_LOCAL_UI,
    PRERELEASE_TAG_SUFFIX,
    PRIVACY_CENTER_IMAGE,
    RC_TAG_SUFFIX,
    SAMPLE_APP_IMAGE,
)
from git_nox import get_current_tag, recognized_tag

DOCKER_PLATFORMS = "linux/amd64,linux/arm64"


def runner(args):
    args_str = " ".join(args)
    run(args_str, shell=True, check=True)


def verify_git_tag(session: nox.Session) -> str:
    """
    Get the git tag for HEAD and validate it before using it.
    """
    existing_commit_tag = get_current_tag(existing=True)
    if existing_commit_tag is None:
        session.skip(
            "Did not find an existing git tag on the current commit, not pushing git-tag images"
        )

    if not recognized_tag(existing_commit_tag):
        session.skip(
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
        "--tag",
        tag(),
        ".",
    )
    if "nocache" in session.posargs:
        build_command = (*build_command, "--no-cache")

    session.run(*build_command, external=True)


def get_buildx_commands(tag_suffixes: List[str]) -> List[Tuple[str, ...]]:
    """
    Build and publish each image to Dockerhub
    """
    fides_tags = [f"{IMAGE}:{tag_suffix}" for tag_suffix in tag_suffixes]
    fides_buildx_command = generate_multiplatform_buildx_command(
        image_tags=fides_tags, docker_build_target="prod"
    )

    privacy_center_tags = [
        f"{PRIVACY_CENTER_IMAGE}:{tag_suffix}" for tag_suffix in tag_suffixes
    ]
    privacy_center_buildx_command = generate_multiplatform_buildx_command(
        image_tags=privacy_center_tags,
        docker_build_target="prod_pc",
    )

    sample_app_tags = [
        f"{SAMPLE_APP_IMAGE}:{tag_suffix}" for tag_suffix in tag_suffixes
    ]
    sample_app_buildx_command = generate_multiplatform_buildx_command(
        image_tags=sample_app_tags,
        docker_build_target="prod",
        dockerfile_path="clients/sample-app",
    )

    buildx_commands = [
        fides_buildx_command,
        privacy_center_buildx_command,
        sample_app_buildx_command,
    ]
    return buildx_commands


@nox.session()
@nox.parametrize(
    "tag",
    [
        nox.param("prod", id="prod"),
        nox.param("dev", id="dev"),
        nox.param("rc", id="rc"),
        nox.param("prerelease", id="prerelease"),
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

    prod - Tags images with the current version of the application, and constant `latest` tag
    dev - Tags images with `dev`
    prerelease - Tags images with `prerelease` - used for alpha and beta tags
    rc - Tags images with `rc` - used for rc tags
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
        success_codes=[0, 1],  # Will fail if it already exists, but this is fine
    )

    # Use lambdas to force lazy evaluation
    param_tag_map: Dict[str, Callable] = {
        "dev": lambda: [DEV_TAG_SUFFIX],
        "prerelease": lambda: [PRERELEASE_TAG_SUFFIX],
        "rc": lambda: [RC_TAG_SUFFIX],
        "git-tag": lambda: [verify_git_tag(session)],
        "prod": lambda: [get_current_tag(), "latest"],
    }

    # Get the list of Tupled commands to run
    buildx_commands = get_buildx_commands(tag_suffixes=param_tag_map[tag]())

    # Parallel build the various images
    number_of_processes = len(buildx_commands)
    with Pool(number_of_processes) as process_pool:
        process_pool.map(runner, buildx_commands)
