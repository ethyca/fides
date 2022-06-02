from abc import ABC, abstractmethod

from requests import PreparedRequest

from fidesops.models.connectionconfig import ConnectionConfig
from fidesops.schemas.saas.strategy_configuration import StrategyConfiguration


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
