"""Contains the nox sessions utilities for git-related tasks"""

import re
from enum import Enum
from typing import List, Optional

import nox
from packaging.version import Version

RELEASE_BRANCH_REGEX = r"release-(([0-9]+\.)+[0-9]+)"
RELEASE_TAG_REGEX = r"(([0-9]+\.)+[0-9]+)"
VERSION_TAG_REGEX = r"{version}{tag_type}([0-9]+)"
RC_TAG_REGEX = r"(([0-9]+\.)+[0-9]+)rc([0-9]+)"
GENERIC_TAG_REGEX = r"{tag_type}([0-9]+)$"

INITIAL_TAG_INCREMENT = 0
TAG_INCREMENT = 1


class TagType(Enum):
    """
    The 'types' of git tags used for different types of branches in our repo
    """

    RC = "rc"  # used for release branches
    ALPHA = "a"  # used for feature branches
    BETA = "b"  # used for `main` branch


def get_all_tags(repo) -> List[str]:
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
    if existing:  # checks for an existing tag on current commit
        if not all_tags:
            all_tags = get_all_tags(repo)
        return next(
            (tag.name for tag in all_tags if tag.commit == repo.head.commit),
            None,
        )
    git_session = repo.git()
    git_session.fetch("--force", "--tags")
    current_tag = git_session.describe("--tags", "--dirty", "--always")
    return current_tag


@nox.session()
@nox.parametrize(
    "action",
    [
        nox.param("dry", id="dry"),
        nox.param("push", id="push"),
    ],
)
def tag(session: nox.Session, action: str) -> None:
    """
    Generates and optionally applies and pushes a git tag for the current HEAD commit.

    Programmatically generates new tags based on the currently checked out
    branch and existing tags in the repo.

    Positional Arguments:
        N/A

    Parameters:
        - tag(dry) = Show the tag that would be applied.
        - tag(push) = Tag the current commit and push it. NOTE: This will trigger a new CI job to publish the tag.
    """
    # pip3.10 install GitPython
    from git.repo import Repo

    repo = Repo()
    all_tags = get_all_tags(repo)

    # generate a tag based on the current repo state
    generated_tag = generate_tag(session, repo.active_branch.name, all_tags)

    if action == "dry":
        session.log(f"Dry-run -- would generate tag: {generated_tag}")

    elif action == "push":
        repo.create_tag(generated_tag)
        session.log(f"Pushing tag {generated_tag} to remote (origin)")
        repo.remotes.origin.push(generated_tag)

    else:
        session.error(f"Invalid action: {action}")


def next_release_increment(
    session: nox.Session, all_tags: List, treat_rc_as_release: bool = False
) -> Version:
    """Helper to generate the next release 'increment' based on latest release tag found

    If `treat_rc_as_release` is `True`, also treat `rc` tags as releases
    """

    releases = sorted(  # sorted by Version - what we want!
        (
            Version(tag.name)
            for tag in all_tags
            if re.fullmatch(RELEASE_TAG_REGEX, tag.name)
        ),
        reverse=True,
    )
    latest_release = releases[0] if releases else None
    if not latest_release:  # this would be bad...
        session.error("Could not identify the latest release!")

    if treat_rc_as_release:
        rc_releases = sorted(  # sorted by Version - what we want!
            (
                Version(tag.name)
                for tag in all_tags
                if re.fullmatch(RC_TAG_REGEX, tag.name)
            ),
            reverse=True,
        )
        latest_rc_release = rc_releases[0] if rc_releases else None
        if latest_rc_release and latest_rc_release > latest_release:
            latest_release = latest_rc_release

    return Version(
        f"{latest_release.major}.{latest_release.minor}.{latest_release.micro + 1}"
    )


def recognized_tag(tag_to_check: str) -> bool:
    """Utility function to check whether the provided tag matches one of our recognized tag patterns"""
    for tag_type in TagType:
        pattern = GENERIC_TAG_REGEX.format(tag_type=tag_type.value)
        if re.search(pattern, tag_to_check):
            return True
    return False


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
    sorted_tag_matches = sorted(
        (
            re.fullmatch(version_branch_tag_pattern, tag.name)
            for tag in all_tags
            if re.fullmatch(version_branch_tag_pattern, tag.name)
        ),
        key=lambda match: int(
            match.group(1)
        ),  # numeric (not alphabetical) sort of the tag increment
        reverse=True,
    )

    latest_tag_match = sorted_tag_matches[0] if sorted_tag_matches else None
    if (
        latest_tag_match
    ):  # if we have an existing tag for this version/type, increment it
        session.log(
            f"Found existing {tag_type.name.lower()} tag {latest_tag_match.group(0)}, incrementing it"
        )
        tag_increment = (
            int(latest_tag_match.group(1)) + TAG_INCREMENT
        )  # increment the tag
        return f"{version_number}{tag_type.value}{tag_increment}"
        # return the full {version_number}{tag_type}{increment}

    # we don't have an existing tag for this version/type, so start at our initial increment
    return f"{version_number}{tag_type.value}{INITIAL_TAG_INCREMENT}"


def generate_tag(session: nox.Session, branch_name: str, all_tags: List) -> str:
    """Generate a tag used for package deployment"""
    session.log(
        f"Fetching current tags and branch to generate a new tag, branch = '{branch_name}'"
    )

    if release_branch_match := re.fullmatch(
        RELEASE_BRANCH_REGEX, branch_name
    ):  # release branch
        session.log(
            f"Current branch '{branch_name}' matched release branch, determined release '{release_branch_match.group(1)}'. Generating a new {TagType.RC.name.lower()} tag for this release"
        )
        return increment_tag(
            session, all_tags, release_branch_match.group(1), TagType.RC
        )

    if branch_name == "main":  # main
        # we consider `rc` tags as releases when generating beta tags while on `main``
        # this keeps our tags based off `main` _ahead_ of our `rc` tags
        next_release = next_release_increment(
            session, all_tags, treat_rc_as_release=True
        )
        session.log(
            f"Current branch '{branch_name}' matched main branch. Generating a new {TagType.BETA.name.lower()} tag"
        )
        return increment_tag(session, all_tags, next_release, TagType.BETA)

    next_release = next_release_increment(session, all_tags)
    # feature branch, if we've made it here
    if "release" in branch_name:
        session.warn(
            f"WARNING: Current branch '{branch_name}' does not follow release branch format ('release-n.n.n') and will be tagged as a feature branch."
        )
        session.warn("WARNING: Did you mean to name your branch differently?")
    session.log(
        f"Current branch '{branch_name}' matched feature branch. Generating a new {TagType.ALPHA.name.lower()} tag"
    )
    return increment_tag(session, all_tags, next_release, TagType.ALPHA)
