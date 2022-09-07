import pytest

from fidesops.ops.common_exceptions import NoSuchStrategyException
from fidesops.ops.service.authentication.authentication_strategy import (
    AuthenticationStrategy,
)
from fidesops.ops.service.authentication.authentication_strategy_basic import (
    BasicAuthenticationStrategy,
)
from fidesops.ops.service.authentication.authentication_strategy_bearer import (
    BearerAuthenticationStrategy,
)
from fidesops.ops.service.authentication.authentication_strategy_query_param import (
    QueryParamAuthenticationStrategy,
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


def test_get_strategy_query_param():
    config = {"name": "api_key", "value": "<api_key>"}
    strategy = AuthenticationStrategy.get_strategy(
        strategy_name="query_param", configuration=config
    )
    assert isinstance(strategy, QueryParamAuthenticationStrategy)


def test_get_strategy_invalid_strategy():
    with pytest.raises(NoSuchStrategyException):
        AuthenticationStrategy.get_strategy("invalid", {})
