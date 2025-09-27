import pytest

from fides.api.common_exceptions import NoSuchStrategyException, ValidationError
from fides.api.service.async_dsr.strategies.async_dsr_strategy_callback import (
    AsyncCallbackStrategy,
)
from fides.api.service.async_dsr.strategies.async_dsr_strategy_factory import (
    get_strategy,
)
from fides.api.service.async_dsr.strategies.async_dsr_strategy_polling import (
    AsyncPollingStrategy,
)


class TestAsyncDSRStrategyFactory:
    def test_get_strategy_polling(self, db):
        """Test getting a polling strategy with valid configuration"""
        config = {
            "status_request": {
                "method": "GET",
                "path": "/status/<request_id>",
                "status_path": "status",
                "status_completed_value": "completed",
            },
            "result_request": {
                "method": "GET",
                "path": "/result/<request_id>",
                "result_path": "data.users",
            },
        }
        strategy = get_strategy(
            strategy_name="polling", session=db, configuration=config
        )
        assert isinstance(strategy, AsyncPollingStrategy)
        assert strategy.type.value == "polling"

    @pytest.mark.parametrize(
        "status_value",
        [
            "completed",  # string
            True,  # boolean
            1,  # integer
        ],
    )
    def test_get_strategy_polling_different_status_types(self, db, status_value):
        """Test polling strategy supports different status value types"""
        config = {
            "status_request": {
                "method": "GET",
                "path": "/status/<request_id>",
                "status_path": "ready",
                "status_completed_value": status_value,
            },
            "result_request": {
                "method": "GET",
                "path": "/result/<request_id>",
                "result_path": "data",
            },
        }
        strategy = get_strategy(
            strategy_name="polling", session=db, configuration=config
        )
        assert isinstance(strategy, AsyncPollingStrategy)
        assert strategy.type.value == "polling"

    def test_get_strategy_callback(self, db):
        """Test getting a callback strategy (no configuration required)"""
        config = {}
        strategy = get_strategy(
            strategy_name="callback", session=db, configuration=config
        )
        assert isinstance(strategy, AsyncCallbackStrategy)
        assert strategy.type.value == "callback"

    def test_get_strategy_invalid_strategy_name(self, db):
        """Test that invalid strategy name raises NoSuchStrategyException"""
        with pytest.raises(NoSuchStrategyException) as exc:
            get_strategy(strategy_name="invalid_strategy", session=db, configuration={})

        assert "Strategy 'invalid_strategy' does not exist" in str(exc.value)
        assert "polling" in str(exc.value)
        assert "callback" in str(exc.value)

    def test_get_strategy_polling_no_config(self, db):
        """Test that polling strategy without config raises ValidationError"""
        with pytest.raises(ValidationError) as exc:
            get_strategy(strategy_name="polling", session=db, configuration=None)

        assert "Configuration required for polling strategy" in str(exc.value)

    def test_get_strategy_polling_invalid_config_structure(self, db):
        """Test that invalid configuration structure raises ValidationError"""
        config = {
            "status_request": {
                "method": "GET",
                "path": "/status",
                "status_path": "status",
                "status_completed_value": "done",
            },
            "result_request": "invalid_request_format",  # Should be a dict
        }
        with pytest.raises(ValidationError):
            get_strategy(strategy_name="polling", session=db, configuration=config)

    def test_get_strategy_polling_missing_required_fields(self, db):
        """Test that missing required fields in polling config raises ValidationError"""
        # Missing status_path and status_completed_value in status_request
        config = {
            "status_request": {
                "method": "GET",
                "path": "/status",
                # Missing status_path and status_completed_value
            },
            "result_request": {
                "method": "GET",
                "path": "/result",
            },
        }
        with pytest.raises(ValidationError):
            get_strategy(strategy_name="polling", session=db, configuration=config)
