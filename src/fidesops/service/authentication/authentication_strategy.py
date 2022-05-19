from abc import ABC, abstractmethod
from typing import Any, Dict

from requests import PreparedRequest

from fidesops.schemas.saas.strategy_configuration import StrategyConfiguration


class AuthenticationStrategy(ABC):
    """Abstract base class for SaaS authentication strategies"""

    @abstractmethod
    def add_authentication(
        self, request: PreparedRequest, secrets: Dict[str, Any]
    ) -> PreparedRequest:
        """Add authentication to the request"""

    @staticmethod
    @abstractmethod
    def get_configuration_model() -> StrategyConfiguration:
        """Used to get the configuration model to configure the strategy"""
