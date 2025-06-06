import logging
import os
from datetime import datetime

import pytest
from loguru import logger
from loguru._handler import Message

from fides.api.schemas.privacy_request import PrivacyRequestSource
from fides.api.util.cache import get_cache
from fides.api.util.logger import (
    MASKED,
    Pii,
    RedisSink,
    _log_exception,
    _log_warning,
    suppress_logging,
)
from fides.api.util.sqlalchemy_filter import SQLAlchemyGeneratedFilter
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


@pytest.mark.unit
class TestSuppressLogging:
    def test_suppress_logging_context_manager(self, loguru_caplog):
        """Test that the suppress_logging context manager correctly suppresses logs."""

        # Log a message outside the context manager
        logger.info("This message should appear in logs")

        # Log messages inside the context manager
        with suppress_logging():
            logger.info("This INFO message should be suppressed")
            logger.warning("This WARNING message should be suppressed")
            logger.error("This ERROR message should be suppressed")

        # Log another message after the context manager
        logger.info("This message should also appear in logs")

        # Check that only the messages outside the context manager appear in the logs
        log_messages = loguru_caplog.text
        assert "This message should appear in logs" in log_messages
        assert "This message should also appear in logs" in log_messages
        assert "This INFO message should be suppressed" not in log_messages
        assert "This WARNING message should be suppressed" not in log_messages
        assert "This ERROR message should be suppressed" not in log_messages

    def test_suppress_logging_exception_safety(self, loguru_caplog):
        """Test that the suppress_logging context manager restores log levels even if an exception occurs."""

        # Get the original minimum log level
        original_min_level = logger._core.min_level

        try:
            # Try logging in a context that will raise an exception
            with suppress_logging():
                logger.info("This message should be suppressed")
                raise ValueError("Test exception")
        except ValueError:
            pass  # We expect this exception

        # Log a message after the exception
        logger.info("This message should appear in logs")

        # Check that the log level was restored despite the exception
        assert logger._core.min_level == original_min_level
        assert "This message should be suppressed" not in loguru_caplog.text
        assert "This message should appear in logs" in loguru_caplog.text


@pytest.mark.unit
class TestSQLAlchemyLogger:
    def test_sqlalchemy_logging_filter(self, loguru_caplog):
        """Test that the SQLAlchemyGeneratedFilter correctly filters out unwanted log messages."""

        # Create a logger for SQLAlchemy
        sqlalchemy_logger = logging.getLogger("sqlalchemy.engine.Engine")
        sqlalchemy_logger.setLevel(logging.INFO)

        # Add the SQLAlchemyGeneratedFilter
        filter = SQLAlchemyGeneratedFilter()
        sqlalchemy_logger.addFilter(filter)

        # Log messages that should be filtered out
        sqlalchemy_logger.info(
            "This message was cached since yesterday and should be filtered"
        )
        sqlalchemy_logger.info(
            "This message indicates caching disabled and should be filtered"
        )
        sqlalchemy_logger.info(
            "[dialect redshift+psycopg2 does not support caching 0.00016s] {'email': ('atestingemail@email.com',)"
        )

        # Log a message that should not be filtered out
        sqlalchemy_logger.info("This message should appear in logs")

        # Check that only the message that should not be filtered appears in the logs
        log_messages = loguru_caplog.text
        assert "This message should appear in logs" in log_messages
        assert "This message contains no key and should be filtered" not in log_messages
        assert (
            "This message was cached since yesterday and should be filtered"
            not in log_messages
        )
        assert (
            "This message was generated in 0.001s and should be filtered"
            not in log_messages
        )
        assert (
            "This message indicates caching disabled and should be filtered"
            not in log_messages
        )
        assert (
            "This message does not support caching and should be filtered"
            not in log_messages
        )
        assert "This message is unknown and should be filtered" not in log_messages
        assert (
            "[dialect redshift+psycopg2 does not support caching 0.00016s] {'email': ('atestingemail@email.com',)"
            not in log_messages
        )
