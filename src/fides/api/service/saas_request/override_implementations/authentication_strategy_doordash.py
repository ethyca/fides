import math
import time
from typing import Any, Dict, Optional

import jwt.utils
from requests import PreparedRequest

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.schemas.saas.strategy_configuration import StrategyConfiguration
from fides.api.service.authentication.authentication_strategy import (
    AuthenticationStrategy,
)
from fides.api.util.saas_util import assign_placeholders


class DoordashAuthenticationConfiguration(StrategyConfiguration):
    """
    Parameters to generate a Doordash JWT token
    """

    developer_id: str
    key_id: str
    signing_secret: str


class DoordashAuthenticationStrategy(AuthenticationStrategy):
    """
    Adds a Doordash JWT as bearer auth to the request
    """

    name = "doordash"
    configuration_model = DoordashAuthenticationConfiguration

    def __init__(self, configuration: DoordashAuthenticationConfiguration):
        self.developer_id = configuration.developer_id
        self.key_id = configuration.key_id
        self.signing_secret = configuration.signing_secret

    def add_authentication(
        self, request: PreparedRequest, connection_config: ConnectionConfig
    ) -> PreparedRequest:
        """
        Generate a Doordash JWT and add it as bearer auth
        """

        secrets: Optional[Dict[str, Any]] = connection_config.secrets

        token = jwt.encode(
            {
                "aud": "doordash",
                "iss": (
                    assign_placeholders(self.developer_id, secrets) if secrets else None
                ),
                "kid": assign_placeholders(self.key_id, secrets) if secrets else None,
                "exp": str(math.floor(time.time() + 60)),
                "iat": str(math.floor(time.time())),
            },
            jwt.utils.base64url_decode(
                assign_placeholders(self.signing_secret, secrets)  # type: ignore
            ),
            algorithm="HS256",
            headers={"dd-ver": "DD-JWT-V1"},
        )

        request.headers["Authorization"] = f"Bearer {token}"
        return request
