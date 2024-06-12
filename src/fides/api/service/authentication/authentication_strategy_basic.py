from base64 import b64encode

from requests import PreparedRequest

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.schemas.saas.strategy_configuration import (
    BasicAuthenticationConfiguration,
)
from fides.api.service.authentication.authentication_strategy import (
    AuthenticationStrategy,
)
from fides.api.util.saas_util import assign_placeholders


class BasicAuthenticationStrategy(AuthenticationStrategy):
    """
    Replaces the username and password placeholders with the actual credentials
    and uses them to add a basic authentication header to the incoming request.
    """

    name = "basic"
    configuration_model = BasicAuthenticationConfiguration

    def __init__(self, configuration: BasicAuthenticationConfiguration):
        self.username = configuration.username
        self.password = configuration.password

    def add_authentication(
        self, request: PreparedRequest, connection_config: ConnectionConfig
    ) -> PreparedRequest:
        """Add basic authentication to the request"""
        secrets = connection_config.secrets
        username = assign_placeholders(self.username, secrets)  # type: ignore
        password = assign_placeholders(self.password, secrets)  # type: ignore

        # the requests library treats a None password as a "None" literal string
        # so we need to override this behavior
        if password is None:
            password = ""

        request.headers["Authorization"] = (
            "Basic " + b64encode(f"{username}:{password}".encode()).decode()
        )
        return request
