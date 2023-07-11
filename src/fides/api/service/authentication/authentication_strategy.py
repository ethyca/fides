from abc import abstractmethod

from requests import PreparedRequest

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.service.strategy import Strategy


class AuthenticationStrategy(Strategy):
    """Abstract base class for SaaS authentication strategies"""

    @abstractmethod
    def add_authentication(
        self, request: PreparedRequest, connection_config: ConnectionConfig
    ) -> PreparedRequest:
        """Add authentication to the request"""
