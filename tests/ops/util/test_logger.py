import os
from datetime import datetime

import pytest
from loguru import logger
from loguru._handler import Message

from fides.api.schemas.privacy_request import PrivacyRequestSource
from fides.api.util.cache import get_cache
from fides.api.util.logger import MASKED, Pii, RedisSink, _log_exception, _log_warning
from fides.config import CONFIG


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
    def test_logger_exception(self, dev_mode, error_message, loguru_caplog):
        _log_exception(ValueError(error_message), dev_mode)

        assert "ERROR" in loguru_caplog.text
        assert error_message in loguru_caplog.text

    def test_logger_warning_dev_mode(self, error_message, loguru_caplog):
        _log_warning(ValueError(error_message), True)

        assert "WARNING" in loguru_caplog.text
        assert error_message in loguru_caplog.text

    def test_logger_warning_prod_mode(self, error_message, loguru_caplog):
        _log_warning(ValueError(error_message), False)

        assert "ERROR" in loguru_caplog.text
        assert error_message in loguru_caplog.text


class TestRedisSink:
    def test_dataset_test_source_writes_to_redis(self):
        """Test that messages from dataset_test source are written to Redis"""
        test_id = "test_id_123"
        test_msg = "test message"

        # Log with dataset_test source context
        with logger.contextualize(
            privacy_request_id=test_id,
            privacy_request_source=PrivacyRequestSource.dataset_test.value,
        ):
            logger.info(test_msg)

        # Verify the message was written to Redis
        cache = get_cache()
        key = f"log_{test_id}"
        logs = cache.get_decoded_list(key)
        assert len(logs) == 1
        assert logs[0]["message"] == test_msg

        # Cleanup
        cache.delete(key)

    def test_other_sources_do_not_write_to_redis(self):
        """Test that messages from other sources are not written to Redis"""
        test_id = "test_id_456"
        test_msg = "test message"

        # Test different privacy request sources
        other_sources = [
            PrivacyRequestSource.privacy_center.value,
            PrivacyRequestSource.request_manager.value,
            None,
        ]
        for source in other_sources:
            with logger.contextualize(
                privacy_request_id=test_id, privacy_request_source=source
            ):
                logger.info(test_msg)

            # Verify nothing was written to Redis
            cache = get_cache()
            key = f"log_{test_id}"
            assert len(cache.get_decoded_list(key)) == 0
