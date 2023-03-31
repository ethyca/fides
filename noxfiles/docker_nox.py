"""Contains the nox sessions for docker-related tasks."""
import platform
import re
from typing import List, Optional

import nox
from packaging.version import Version

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

# from packaging import Version


RELEASE_BRANCH_REGEX = "release-(([0-9]+\.)+[0-9]+)"
RC_TAG_REGEX = "{release_version}rc([0-9]+)"
RELEASE_TAG_REGEX = "(([0-9]+\.)+[0-9]+)"
MAIN_BUILD_TAG_REGEX = "{release_version}b0"


def get_current_tag(existing: bool = False) -> Optional[str]:
    """
    Get the current git tag.

    If `exists` is true, this tag must already exist.
    Otherwise, a tag is generated via `git describe --tags --dirty --always`,
    which includes "dirty" tags if the working tree has local modifications.
    """
    from git.repo import Repo

    repo = Repo()
    if existing:  # checks for an existing tag on current commit
        return next(
            (tag.name for tag in get_all_tags(repo) if tag.commit == repo.head.commit),
            None,
        )
    git_session = repo.git()
    git_session.fetch("--force", "--tags")
    current_tag = git_session.describe("--tags", "--dirty", "--always")
    return current_tag


def get_all_tags(repo):
    """
    Returns a list of all tags in the repo, sorted by committed date, latest first
    """

    git_session = repo.git()
    git_session.fetch("--force", "--tags")
    return sorted(repo.tags, key=lambda t: t.commit.committed_datetime, reverse=True)


@nox.session()
def deploy_tag(session: nox.Session) -> str:
    """
    dry_run = don't actually tag or push, just show the tag that will be generated
    tag = generate and apply a tag locally
    push = push the generated tag
    push_current = push the current tag
    """
    from git.repo import Repo

    repo = Repo()
    current_tag = get_current_tag(
        existing=True
    )  # first get an existing tag if we've got one
    generated_tag = generate_tag(session, repo)
    if "dry_run" in session.posargs:
        session.log(f"Dry-run -- would generate deploy tag: {generated_tag}")
    if "push_current" in session.posargs:
        session.log(f"Pushing current tag {current_tag} to remote (origin)")
        repo.remotes.origin.push(current_tag)
        return
    if "tag" in session.posargs:  # generate and apply a tag if we've been told to tag
        session.log(f"Tagging current HEAD commit with tag: {current_tag}")
        repo.create_tag(generated_tag)
    if "push" in session.posargs:
        session.log(f"Pushing generated tag {generated_tag} to remote (origin)")
        repo.remotes.origin.push(generated_tag)


def next_release_increment(session, repo):
    """Helper to generate the next release 'increment' based on latest release tag found"""
    latest_release = next(
        tag.name
        for tag in get_all_tags(repo)
        if re.fullmatch(RELEASE_TAG_REGEX, tag.name)
    )
    if not latest_release:  # this would be bad...
        session.error("Could not identify the latest release!")
    latest_release = Version(latest_release)
    return Version(
        f"{latest_release.major}.{latest_release.minor}.{latest_release.micro + 1}"
    )


def generate_tag(session: nox.Session, repo) -> str:
    """Generate a tag used for package deployment"""

    # get current branch
    branch = repo.active_branch
    branch_name = branch.name

    if branch_name == "main":  # main
        next_release = next_release_increment(session, repo)
        # find our latest beta tag of "next" rleease
        latest_beta_tag = next(
            (
                re.fullmatch(f"{next_release}b([0-9]+)", tag.name)
                for tag in get_all_tags(repo)
                if re.fullmatch(f"{next_release}b([0-9]+)", tag.name)
            ),
            None,
        )
        if latest_beta_tag:  # if we have an existing beta tag, increment it
            session.log(
                f"Found existing beta tag {latest_beta_tag.group(0)}, incrementing it"
            )
            tag_increment = (
                int(latest_beta_tag.group(1)) + 1
            )  # increment the beta tag by 1
            return f"{next_release}b{tag_increment}"
            # return the full [version_number]a[increment

        # we don't have an existing beta tag, so start at 0!
        return f"{next_release}b0"

    if release_branch_match := re.fullmatch(
        RELEASE_BRANCH_REGEX, branch_name
    ):  # release branch

        # determine our release number based on branch name
        try:
            release_version = release_branch_match.group(1)
        except IndexError:  # we shouldn't hit this, but just to be safe
            session.error(
                f"Could not determine release number of release branch {branch_name}"
            )

        # find our latest rc tag of current rleease
        latest_rc_tag = next(
            (
                re.fullmatch(f"{release_version}rc([0-9]+)", tag.name)
                for tag in get_all_tags(repo)
                if re.fullmatch(f"{release_version}rc([0-9]+)", tag.name)
            ),
            None,
        )
        if latest_rc_tag:  # if we have an existing rc tag, increment it
            session.log(
                f"Found existing rc tag {latest_rc_tag.group(0)}, incrementing it"
            )
            tag_increment = int(latest_rc_tag.group(1)) + 1  # increment the rc tag by 1
            return f"{release_version}rc{tag_increment}"
            # return the full [version_number]rc[increment] tag

        # we don't have an existing rc tag, so start at 1!
        return f"{release_version}rc1"

    # assume feature branch as default case
    next_release = next_release_increment(session, repo)
    # find our latest alpha tag of "next" rleease
    latest_alpha_tag = next(
        (
            re.fullmatch(f"{next_release}a([0-9]+)", tag.name)
            for tag in get_all_tags(repo)
            if re.fullmatch(f"{next_release}a([0-9]+)", tag.name)
        ),
        None,
    )
    if latest_alpha_tag:  # if we have an existing alpha tag, increment it
        session.log(
            f"Found existing alpha tag {latest_alpha_tag.group(0)}, incrementing it"
        )
        tag_increment = (
            int(latest_alpha_tag.group(1)) + 1
        )  # increment the alpha tag by 1
        return f"{next_release}a{tag_increment}"
        # return the full [version_number]a[increment] tag

    # we don't have an existing alpha tag, so start at 0!
    return f"{next_release}a0"


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
        nox.param("sample", id="sample"),
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
        sample = Builds all components required for the sample application.
        test = Build the fides webserver/CLI the same as `prod`, but tag is as `local`.
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
        "dev": {"tag": lambda: IMAGE_LOCAL, "target": "dev"},
        "sample": {"tag": lambda: IMAGE_SAMPLE, "target": "prod"},
        "test": {"tag": lambda: IMAGE_LOCAL, "target": "prod"},
        "admin_ui": {"tag": lambda: IMAGE_LOCAL_UI, "target": "frontend"},
    }

    # When building for release, there are additional images that need
    # to get built. These images are outside of the primary `ethyca/fides`
    # image so some additional logic is required.
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
    """
    Push the main image & extra apps to DockerHub:
      - ethyca/fides
      - ethyca/fides-privacy-center
      - ethyca/fides-sample-app

    Params:

    prod - Tags images with the current version of the application
    dev - Tags images with `dev`

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
