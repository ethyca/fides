"""Contains the nox sessions utilities for git-related tasks"""

import re
from enum import Enum
from typing import List, Optional

from packaging.version import Version

import nox

RELEASE_BRANCH_REGEX = r"release-(([0-9]+\.)+[0-9]+)"
RC_TAG_REGEX = r"{release_version}rc([0-9]+)"
RELEASE_TAG_REGEX = r"(([0-9]+\.)+[0-9]+)"
VERSION_TAG_REGEX = r"{version}{tag_type}([0-9]+)"

INITIAL_TAG_INCREMENT = 0
TAG_INCREMENT = 1


class TagType(Enum):
    """
    The 'types' of git tags used for different types of branches in our repo
    """

    RC = "rc"  # used for release branches
    ALPHA = "a"  # used for feature branches
    BETA = "b"  # used for `main` branch


def get_all_tags(repo):
    """
    Returns a list of all tags in the repo, sorted by committed date, latest first
    """

    git_session = repo.git()
    git_session.fetch("--force", "--tags")
    return sorted(repo.tags, key=lambda t: t.commit.committed_datetime, reverse=True)


def get_current_tag(
    existing: bool = False, repo=None, all_tags: List = []
) -> Optional[str]:
    """
    Get the current git tag.

    If `existing` is true, this tag must already exist.
    Otherwise, a tag is generated via `git describe --tags --dirty --always`,
    which includes "dirty" tags if the working tree has local modifications.
    """
    if repo is None:
        from git.repo import Repo

        repo = Repo()
    if not all_tags:
        all_tags = get_all_tags(repo)
    if existing:  # checks for an existing tag on current commit
        return next(
            (tag.name for tag in all_tags if tag.commit == repo.head.commit),
            None,
        )
    git_session = repo.git()
    git_session.fetch("--force", "--tags")
    current_tag = git_session.describe("--tags", "--dirty", "--always")
    return current_tag


@nox.session()
def tag(session: nox.Session) -> str:
    """
    Generates and applies a git tag based on the currently checked out branch
    and existing tags in the repo.

    Positional Arguments:
    - dry_run = don't actually apply the tag or push, just show the tag that will be generated
    - push = push the generated tag
    - push_current = push the current tag
    """
    from git.repo import Repo

    repo = Repo()
    all_tags = get_all_tags(repo)
    current_tag = get_current_tag(
        existing=True,
        repo=repo,
        all_tags=all_tags,
    )  # first get an existing tag if we've got one
    generated_tag = generate_tag(
        session, repo.active_branch.name, all_tags
    )  # generate a tag based on the current repo state

    if "dry_run" in session.posargs:
        session.log(f"Dry-run -- would generate tag: {generated_tag}")
        return
    if "push_current" in session.posargs:
        session.log(f"Pushing current tag {current_tag} to remote (origin)")
        repo.remotes.origin.push(current_tag)
        return

    # generate and apply a tag if we haven't been told not to
    session.log(f"Tagging current HEAD commit with tag: {generated_tag}")
    repo.create_tag(generated_tag)

    # push the generated tag if we've been told to
    if "push" in session.posargs:
        session.log(f"Pushing generated tag {generated_tag} to remote (origin)")
        repo.remotes.origin.push(generated_tag)


def next_release_increment(session: nox.Session, all_tags: List):
    """Helper to generate the next release 'increment' based on latest release tag found"""
    latest_release = next(
        tag.name for tag in all_tags if re.fullmatch(RELEASE_TAG_REGEX, tag.name)
    )
    if not latest_release:  # this would be bad...
        session.error("Could not identify the latest release!")
    latest_release = Version(latest_release)
    return Version(
        f"{latest_release.major}.{latest_release.minor}.{latest_release.micro + 1}"
    )


def increment_tag(
    session: nox.Session,
    all_tags: List,
    version_number: str,
    tag_type: TagType,
):
    """
    Utility method to generate the "next" appropriate tag on the given version number
    with the given tag type.
    """
    version_branch_tag_pattern = VERSION_TAG_REGEX.format(
        version=version_number, tag_type=tag_type.value
    )
    # find our latest existing tag for this version/type
    latest_tag = next(
        (
            re.fullmatch(version_branch_tag_pattern, tag.name)
            for tag in all_tags
            if re.fullmatch(version_branch_tag_pattern, tag.name)
        ),
        None,
    )
    if latest_tag:  # if we have an existing tag for this version/type, increment it
        session.log(
            f"Found existing {tag_type.name.lower()} tag {latest_tag.group(0)}, incrementing it"
        )
        tag_increment = int(latest_tag.group(1)) + TAG_INCREMENT  # increment the tag
        return f"{version_number}{tag_type.value}{tag_increment}"
        # return the full {version_number}{tag_type}{increment}

    # we don't have an existing tag for this version/type, so start at our initial increment
    return f"{version_number}{tag_type.value}{INITIAL_TAG_INCREMENT}"


def generate_tag(session: nox.Session, branch_name: str, all_tags: List) -> str:
    """Generate a tag used for package deployment"""

    if release_branch_match := re.fullmatch(
        RELEASE_BRANCH_REGEX, branch_name
    ):  # release branch
        return increment_tag(
            session, all_tags, release_branch_match.group(1), TagType.RC
        )

    next_release = next_release_increment(session, all_tags)

    if branch_name == "main":  # main
        return increment_tag(session, all_tags, next_release, TagType.BETA)

    return increment_tag(session, all_tags, next_release, TagType.ALPHA)
