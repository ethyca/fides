import pytest
from git.repo import Repo

from fides.config import FidesConfig
from fides.core.pull import pull_existing_resources


def git_reset(change_dir: str) -> None:
    """This fixture is used to reset the repo files to HEAD."""

    git_session = Repo().git()
    git_session.checkout("HEAD", change_dir)


@pytest.mark.unit
def test_pull_existing_resources(test_config: FidesConfig) -> None:
    """Placeholder test."""
    test_dir = ".fides/"
    existing_keys = pull_existing_resources(
        test_dir, test_config.cli.server_url, test_config.user.auth_header
    )
    git_reset(test_dir)
    assert len(existing_keys) > 1
