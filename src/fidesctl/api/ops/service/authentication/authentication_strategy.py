from abc import ABC, abstractmethod

from fidesctl.api.ops.models.connectionconfig import ConnectionConfig
from fidesctl.api.ops.schemas.saas.strategy_configuration import StrategyConfiguration
from requests import PreparedRequest


class AuthenticationStrategy(ABC):
    """Abstract base class for SaaS authentication strategies"""

    @abstractmethod
    def add_authentication(
        self, request: PreparedRequest, connection_config: ConnectionConfig
    ) -> PreparedRequest:
        """Add authentication to the request"""

    @staticmethod
    @abstractmethod
    def get_configuration_model() -> StrategyConfiguration:
        """Used to get the configuration model to configure the strategy"""
