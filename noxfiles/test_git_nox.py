from unittest import mock

import pytest
from git import Repo

from git_nox import generate_tag


class TestGitNox:
    """
    Tests for git nox commands and/or utilities
    """

    @pytest.fixture(scope="session")
    def repo(self):
        repo = Repo()
        git_session = repo.git()
        git_session.fetch("--force", "--tags")
        return repo

    @mock.patch("nox.Session.log")
    @pytest.mark.parametrize(
        "current_branch,tags,expected_tag",
        [
            ("main", ["2.9.0"], "2.9.1b0"),
            ("main", ["2.9.1", "2.9.0"], "2.9.2b0"),
            (
                "main",
                ["2.9.0", "2.9.1"],
                "2.9.2b0",
            ),  # releases _could_ be "out of order" chronological order, for e.g. hotfixes
            (
                "main",
                ["2.9.0", "2.10.0"],
                "2.10.1b0",
            ),  # out of order releases with version >= 10 to ensure numerical sort
            (
                "main",
                ["2.18.0", "2.17.0rc1", "2.19.1rc0", "2.19.0rc0"],
                "2.19.2b0",
            ),  # beta tags should be an increment ahead of rc tag version, if it is ahead of our newest release
            (
                "main",
                ["2.18.0", "2.17.0rc1", "2.16.0rc0"],
                "2.18.1b0",
            ),  # beta tags should ignore rc tags if they are not ahead of latest release
            (
                "main",
                ["2.9.0", "2.17.0rc1", "2.16.0rc0"],
                "2.17.1b0",
            ),  # ensure rc version check is robust with numerical sort
            (
                "main",
                ["2.9.0", "2.19.1rc0", "2.19.2b1", "2.16.0rc0"],
                "2.19.2b2",
            ),  # ensure we still increment well when using rc version check
            (
                "some-test-feature-branch",
                ["2.18.0", "2.17.0rc1", "2.19.0rc0"],
                "2.18.1a0",
            ),  # alpha tags should ignore rc tags when determining next increment
            ("some-test-feature-branch", ["2.9.1"], "2.9.2a0"),
            ("some-test-feature-branch", ["2.9.1", "2.9.0"], "2.9.2a0"),
            (
                "some-test-feature-branch",
                ["2.9.3a0", "2.9.2"],
                "2.9.3a1",
            ),  # our repo happens to already have a 2.9.3a0 tag, let's use it for testing here
            (
                "some-other-feature",
                ["2.14.1a0", "2.14.1a1", "2.14.0"],
                "2.14.1a2",
            ),  # unsorted tags
            (
                "some-other-feature",
                ["2.14.1a9", "2.14.1a10", "2.14.0"],
                "2.14.1a11",
            ),  # unsorted tags with current increment = 10 to ensure we're doing a numeric sort
            ("release-2.9.0", [], "2.9.0rc0"),
            ("release-2.9.0", ["2.9.0rc1"], "2.9.0rc2"),
            (
                "release-2.9.0",
                ["2.9.1"],
                "2.9.0rc0",
            ),  # even with a release further ahead, the RC tag generation relies on the release branch name
            # release branches MUST adhere to `release-n.n.n` convention
            # if not, they will be treated as any other "feature" branch
            ("release/2.9.0", ["2.9.0"], "2.9.1a0"),
            ("release_2.9.0", ["2.9.0"], "2.9.1a0"),
        ],
    )
    def test_generate_tag(
        self,
        mock_session,
        current_branch,
        tags,
        expected_tag,
        repo,
    ) -> None:
        """
        Test generate_tag function based on a given `current_branch` and set of existing repo tags

        No tag is actually applied to the repo! The generated tag string is just evaluated within the test runtime
        """

        # get the real tags from the repo because it's hard to instantiate tags from "scratch"

        all_tags = [repo.tags[tag] for tag in tags]

        # evaluate whether we generate the expected tag
        tag = generate_tag(mock_session, current_branch, all_tags)
        assert tag == expected_tag
