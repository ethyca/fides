"""Contains the nox sessions for docker-related tasks."""

from typing import Callable, Dict, List, Optional, Tuple

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


def verify_git_tag(session: nox.Session) -> Optional[str]:
    """
    Get the git tag for HEAD and validate it before using it.
    Return `None` if no valid git tag is found on HEAD
    """
    existing_commit_tag = get_current_tag(existing=True)
    if existing_commit_tag is None:
        session.log(
            "Did not find an existing git tag on the current commit, not using git-tag image tag"
        )
        return None

    if not recognized_tag(existing_commit_tag):
        session.log(
            f"Existing git tag {existing_commit_tag} is not a recognized tag, not using git-tag image tag"
        )
        return None

    session.log(
        f"Found git tag {existing_commit_tag} on the current commit, pushing corresponding git-tag image tags!"
    )
    return existing_commit_tag


def generate_buildx_command(
    image_tags: List[str],
    docker_build_target: str,
    dockerfile_path: str = ".",
) -> Tuple[str, ...]:
    """
    Generate the command for building and publishing an image.

    See tests for example usage in `test_docker_nox.py`
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
        tag_name = None

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


@nox.session()
@nox.parametrize(
    "tag",
    [
        nox.param("prod", id="prod"),
        nox.param("dev", id="dev"),
        nox.param("rc", id="rc"),
        nox.param("prerelease", id="prerelease"),
    ],
)
@nox.parametrize(
    "app",
    [
        nox.param("fides", id="fides"),
        nox.param("privacy_center", id="privacy_center"),
        nox.param("sample_app", id="sample_app"),
    ],
)
def push(session: nox.Session, tag: str, app: str) -> None:
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

    Posargs:
    git_tag - Additionally tags images with the git tag of the current commit, if it exists

    Note:
    Due to how `buildx` works, all platform images need to be build in a
    single `buildx` command. Otherwise it will cause the images in
    Dockerhub to be overwritten.

    Example Calls:
    nox -s "push(fides, prod)"
    nox -s "push(sample_app, prerelease) -- git_tag"
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
        "prod": lambda: [get_current_tag(), "latest"],
    }

    app_info_map = {
        "fides": {"image": IMAGE, "target": "prod", "path": "."},
        "privacy_center": {
            "image": PRIVACY_CENTER_IMAGE,
            "target": "prod_pc",
            "path": ".",
        },
        "sample_app": {
            "image": SAMPLE_APP_IMAGE,
            "target": "prod",
            "path": "clients/sample-app",
        },
    }
    app_info: Dict[str, str] = app_info_map[app]

    # Get the list of Tupled commands to run
    tag_suffixes: List[str] = param_tag_map[tag]()
    # add a git tag based tag suffix, if requested
    if "git_tag" in session.posargs:
        # no-op if no git tag is found
        if git_tag_suffix := verify_git_tag(session):
            tag_suffixes.append(git_tag_suffix)

    full_tags: List[str] = [
        f"{app_info['image']}:{tag_suffix}" for tag_suffix in tag_suffixes
    ]

    # Parallel build the various images

    buildx_command: Tuple[str, ...] = generate_buildx_command(
        image_tags=full_tags,
        docker_build_target=app_info["target"],
        dockerfile_path=app_info["path"],
    )

    session.run(*buildx_command, external=True)
