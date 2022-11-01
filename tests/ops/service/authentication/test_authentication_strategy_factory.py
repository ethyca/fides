import pytest

from fides.api.ops.common_exceptions import NoSuchStrategyException
from fides.api.ops.service.authentication.authentication_strategy import (
    AuthenticationStrategy,
)
from fides.api.ops.service.authentication.authentication_strategy_basic import (
    BasicAuthenticationStrategy,
)
from fides.api.ops.service.authentication.authentication_strategy_bearer import (
    BearerAuthenticationStrategy,
)


def test_get_strategy_basic():
    config = {
        "username": "<username>",
        "password": "<password>",
    }
    strategy = AuthenticationStrategy.get_strategy(
        strategy_name="basic", configuration=config
    )
    assert isinstance(strategy, BasicAuthenticationStrategy)


def test_get_strategy_bearer():
    config = {"token": "<api_key>"}
    strategy = AuthenticationStrategy.get_strategy(
        strategy_name="bearer", configuration=config
    )
    assert isinstance(strategy, BearerAuthenticationStrategy)


def test_get_strategy_invalid_strategy():
    with pytest.raises(NoSuchStrategyException):
        AuthenticationStrategy.get_strategy("invalid", {})
