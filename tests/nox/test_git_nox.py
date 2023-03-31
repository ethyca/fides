from unittest import mock

import pytest
from git import Repo

from noxfiles.git_nox import generate_tag


class TestGitNox:
    """
    Tests for git nox commands and/or utilities
    """

    @mock.patch("nox.Session.log")
    @pytest.mark.parametrize(
        "current_branch,tags,expected_tag",
        [
            ("main", ["2.9.0"], "2.9.1b0"),
            ("main", ["2.9.1", "2.9.0"], "2.9.2b0"),
            ("some-test-feature-branch", ["2.9.1"], "2.9.2a0"),
            ("some-test-feature-branch", ["2.9.1", "2.9.0"], "2.9.2a0"),
            (
                "some-test-feature-branch",
                ["2.9.3a0", "2.9.2"],
                "2.9.3a1",
            ),  # our repo happens to already have a 2.9.3a0 tag, let's use it for testing here
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
    ) -> None:
        """
        Test generate_tag function based on a given `current_branch` and set of existing repo tags

        No tag is actually applied to the repo! The generated tag string is just evaluated within the test runtime
        """

        # get the real tags from the repo because it's hard to instantiate tags from "scratch"
        repo = Repo()
        all_tags = [repo.tags[tag] for tag in tags]

        # evaluate whether we generate the expected tag
        tag = generate_tag(mock_session, current_branch, all_tags)
        assert tag == expected_tag
