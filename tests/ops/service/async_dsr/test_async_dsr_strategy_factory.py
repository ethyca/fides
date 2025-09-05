import pytest

from fides.api.common_exceptions import NoSuchStrategyException, ValidationError
from fides.api.service.async_dsr.async_dsr_strategy_callback import (
    CallbackAsyncDSRStrategy,
)
from fides.api.service.async_dsr.async_dsr_strategy_factory import (
    SupportedAsyncDSRStrategies,
    get_strategy,
    get_strategy_names,
)
from fides.api.service.async_dsr.async_dsr_strategy_polling import (
    PollingAsyncDSRStrategy,
)


class TestAsyncDSRStrategyFactory:
    def test_get_strategy_polling(self):
        """Test getting a polling strategy with valid configuration"""
        config = {
            "status_request": {
                "method": "GET",
                "path": "/status/<status_id>",
            },
            "status_path": "status",
            "result_request": {
                "method": "GET",
                "path": "/result/<result_id>",
            },
            "result_path": "data",
        }
        strategy = get_strategy(strategy_name="polling", configuration=config)
        assert isinstance(strategy, PollingAsyncDSRStrategy)
        assert strategy.name == "polling"

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
        assert "Valid strategies are [callback, polling]" in str(exc.value)

    def test_get_strategy_invalid_config(self):
        """Test that invalid configuration raises ValidationError"""
        config = {
            "status_request": "invalid_request_format",  # Should be a dict
        }
        with pytest.raises(ValidationError):
            get_strategy(strategy_name="polling", configuration=config)
