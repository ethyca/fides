import os

import pytest

from fides.api.ops.util.logger import MASKED, Pii
from fides.core.config import get_config

CONFIG = get_config()


@pytest.fixture(scope="function")
def log_pii_true() -> None:
    original_value = CONFIG.logging.log_pii
    CONFIG.logging.log_pii = True
    yield
    CONFIG.logging.log_pii = original_value


@pytest.fixture(scope="function")
def log_pii_false() -> None:
    original_value = CONFIG.logging.log_pii
    CONFIG.logging.log_pii = False
    yield
    CONFIG.logging.log_pii = original_value


@pytest.mark.usefixtures("log_pii_false")
def test_logger_masks_pii() -> None:
    some_data = "some_data"
    result = "{}".format((Pii(some_data)))
    assert result == MASKED


@pytest.mark.usefixtures("log_pii_true")
def test_logger_doesnt_mask_pii() -> None:
    some_data = "some_data"
    result = "{}".format((Pii(some_data)))
    assert result == "some_data"
