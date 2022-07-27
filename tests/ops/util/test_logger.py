import os

import pytest

from fidesops.util import logger
from fidesops.util.logger import MASKED, NotPii


@pytest.fixture(scope="function")
def toggle_testing_envvar() -> None:
    original_value = os.getenv("TESTING")
    del os.environ["TESTING"]
    yield
    os.environ["TESTING"] = original_value


def test_logger_masks_pii(toggle_testing_envvar) -> None:
    some_data = "some_data"
    result = logger._mask_pii_for_logs(some_data)
    assert result == MASKED


def test_logger_does_not_mask_whitelist() -> None:
    some_data = NotPii("some_data")
    result = logger._mask_pii_for_logs(some_data)
    assert result == some_data
