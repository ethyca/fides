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


@pytest.mark.unit
class TestLogLevel:
    @pytest.fixture
    def error_message(self):
        return "Error message"

    @pytest.mark.parametrize("dev_mode", [True, False])
    def test_logger_exception(self, dev_mode, error_message, logging_capture):
        _log_exception(ValueError(error_message), dev_mode)

        assert "ERROR" in logging_capture.text
        assert error_message in logging_capture.text

    def test_logger_warning_dev_mode(self, error_message, logging_capture):
        _log_warning(ValueError(error_message), True)

        assert "WARNING" in logging_capture.text
        assert error_message in logging_capture.text

    def test_logger_warning_prod_mode(self, error_message, logging_capture):
        _log_warning(ValueError(error_message), False)

        assert "ERROR" in logging_capture.text
        assert error_message in logging_capture.text
