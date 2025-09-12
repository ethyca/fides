import pytest

from fides.api.common_exceptions import NoSuchStrategyException, ValidationError
from fides.api.service.async_dsr.async_dsr_strategy_callback import (
    CallbackAsyncDSRStrategy,
)
from fides.api.service.async_dsr.async_dsr_strategy_factory import get_strategy
from fides.api.service.async_dsr.async_dsr_strategy_polling_access_data import (
    PollingAsyncDSRAccessDataStrategy,
)
from fides.api.service.async_dsr.async_dsr_strategy_polling_access_download import (
    PollingAsyncAccessDownloadStrategy,
)
from fides.api.service.async_dsr.async_dsr_strategy_polling_delete import (
    PollingAsyncErasureStrategy,
)


class TestAsyncDSRStrategyFactory:
    def test_get_strategy_polling_access_data(self):
        """Test getting a polling access data strategy with valid configuration"""
        config = {
            "status_request": {
                "method": "GET",
                "path": "/status/<request_id>",
            },
            "status_path": "status",
            "status_completed_value": "completed",
            "result_request": {
                "method": "GET",
                "path": "/result/<request_id>",
            },
            "result_path": "data.users",
            "request_id_config": {"id_source": "path", "id_path": "request_id"},
            "data_type": "json",
        }
        strategy = get_strategy(
            strategy_name="polling_access_data", configuration=config
        )
        assert isinstance(strategy, PollingAsyncDSRAccessDataStrategy)
        assert strategy.name == "polling_access_data"

    def test_get_strategy_polling_access_download(self):
        """Test getting a polling access download strategy with valid configuration"""
        config = {
            "status_request": {
                "method": "GET",
                "path": "/download-status/<request_id>",
            },
            "status_path": "ready",
            "status_completed_value": "true",
            "result_request": {
                "method": "GET",
                "path": "/download/<request_id>",
            },
            "result_path": "download_url",
            "request_id_config": {"id_source": "generated", "format": "uuid4"},
            "download_type": "link",
        }
        strategy = get_strategy(
            strategy_name="polling_access_download", configuration=config
        )
        assert isinstance(strategy, PollingAsyncAccessDownloadStrategy)
        assert strategy.name == "polling_access_download"

    def test_get_strategy_polling_erasure(self):
        """Test getting a polling erasure strategy with valid configuration"""
        config = {
            "status_request": {
                "method": "GET",
                "path": "/erasure-status/<request_id>",
            },
            "status_path": "completed",
            "status_completed_value": "done",
            "result_request": {
                "method": "GET",
                "path": "/erasure-result/<request_id>",
            },
            "result_path": "status",
            "request_id_config": {"id_source": "path", "id_path": "erasure_id"},
        }
        strategy = get_strategy(strategy_name="polling_erasure", configuration=config)
        assert isinstance(strategy, PollingAsyncErasureStrategy)
        assert strategy.name == "polling_erasure"

    def test_get_strategy_callback_minimal_config(self):
        """Test getting a callback strategy with minimal configuration"""
        config = {}
        strategy = get_strategy(strategy_name="callback", configuration=config)
        assert isinstance(strategy, CallbackAsyncDSRStrategy)

    def test_get_strategy_invalid_strategy(self):
        """Test that invalid strategy name raises NoSuchStrategyException"""
        with pytest.raises(NoSuchStrategyException) as exc:
            get_strategy(strategy_name="invalid_strategy", configuration={})

        assert "Strategy 'invalid_strategy' does not exist" in str(exc.value)

    def test_get_strategy_invalid_config(self):
        """Test that invalid configuration raises ValidationError"""
        config = {
            "status_request": "invalid_request_format",  # Should be a dict
        }
        with pytest.raises(ValidationError):
            get_strategy(strategy_name="polling_access_data", configuration=config)

    def test_get_strategy_missing_required_fields(self):
        """Test that missing required fields raises ValidationError"""
        # Missing status_path
        config = {
            "status_request": {
                "method": "GET",
                "path": "/status",
            },
            "result_request": {
                "method": "GET",
                "path": "/result",
            },
            "request_id_config": {"id_source": "path", "id_path": "id"},
        }
        with pytest.raises(ValidationError):
            get_strategy(strategy_name="polling_access_data", configuration=config)

    # TODO: parametrize different invalid request id config cases
    def test_get_strategy_invalid_request_id_config(self):
        """Test that invalid request_id_config raises ValidationError"""
        # Missing id_path when id_source is 'path'
        config = {
            "status_request": {
                "method": "GET",
                "path": "/status",
            },
            "status_path": "status",
            "result_request": {
                "method": "GET",
                "path": "/result",
            },
            "result_path": "data",
            "request_id_config": {
                "id_source": "path"
                # Missing id_path
            },
        }
        with pytest.raises(ValidationError):
            get_strategy(strategy_name="polling_access_data", configuration=config)

    def test_get_strategy_csv_data_type(self):
        """Test getting a polling access data strategy with CSV data type"""
        config = {
            "status_request": {
                "method": "GET",
                "path": "/csv-status/<request_id>",
            },
            "status_path": "ready",
            "status_completed_value": "finished",
            "result_request": {
                "method": "GET",
                "path": "/csv-result/<request_id>",
            },
            "result_path": "csv_data",
            "request_id_config": {"id_source": "generated", "format": "random_string"},
            "data_type": "csv",
        }
        strategy = get_strategy(
            strategy_name="polling_access_data", configuration=config
        )
        assert isinstance(strategy, PollingAsyncDSRAccessDataStrategy)
        assert strategy.data_type.value == "csv"

    def test_get_strategy_file_download_type(self):
        """Test getting a polling access download strategy with file download type"""
        config = {
            "status_request": {
                "method": "GET",
                "path": "/file-status/<request_id>",
            },
            "status_path": "complete",
            "result_request": {
                "method": "GET",
                "path": "/file-download/<request_id>",
            },
            "result_path": "file_content",
            "request_id_config": {"id_source": "path", "id_path": "download_id"},
            "download_type": "file",
        }
        strategy = get_strategy(
            strategy_name="polling_access_download", configuration=config
        )
        assert isinstance(strategy, PollingAsyncAccessDownloadStrategy)
        assert strategy.download_type.value == "file"
