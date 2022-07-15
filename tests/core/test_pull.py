import pytest

from fidesctl.core.config import FidesctlConfig
from fidesctl.core.pull import pull_existing_resources


@pytest.mark.unit
def test_pull_existing_resources(test_config: FidesctlConfig) -> None:
    """Placeholder test."""
    pull_existing_resources("demo_resources/", test_config.cli.server_url, test_config.user.request_headers)
