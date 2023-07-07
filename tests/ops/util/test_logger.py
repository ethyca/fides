import os

import pytest

from fides.config import CONFIG
from fides.logging.handlers import MASKED, Pii, _log_exception, _log_warning


@pytest.mark.unit
class TestLoggerPii:
    @pytest.fixture(scope="function")
    def log_pii_true(self) -> None:
        original_value = CONFIG.logging.log_pii
        CONFIG.logging.log_pii = True
        yield
        CONFIG.logging.log_pii = original_value

    @pytest.fixture(scope="function")
    def log_pii_false(self) -> None:
        original_value = CONFIG.logging.log_pii
        CONFIG.logging.log_pii = False
        yield
        CONFIG.logging.log_pii = original_value

    @pytest.mark.usefixtures("log_pii_false")
    def test_logger_masks_pii(self) -> None:
        some_data = "some_data"
        result = "{}".format((Pii(some_data)))
        assert result == MASKED

    @pytest.mark.usefixtures("log_pii_true")
    def test_logger_doesnt_mask_pii(self) -> None:
        some_data = "some_data"
        result = "{}".format((Pii(some_data)))
        assert result == "some_data"
