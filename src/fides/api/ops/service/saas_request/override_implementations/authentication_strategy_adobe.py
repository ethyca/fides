import math
import time
from typing import Any, Dict, Optional

import jwt.utils
from jwt import encode
from requests import PreparedRequest

from fides.api.ops.models.connectionconfig import ConnectionConfig
from fides.api.ops.schemas.saas.strategy_configuration import StrategyConfiguration
from fides.api.ops.service.authentication.authentication_strategy import (
    AuthenticationStrategy,
)
from fides.api.ops.util.saas_util import assign_placeholders


class AdobeAuthenticationConfiguration(StrategyConfiguration):
    """
    Parameters to generate an Adobe JWT token
    """

    organization_id: str
    technical_account_id: str
    client_id: str
    private_key: str
    client_secret: str


class AdobeAuthenticationStrategy(AuthenticationStrategy):
    """
    Adds an Adobe JWT as bearer auth to the request
    """

    name = "adobe"
    configuration_model = AdobeAuthenticationConfiguration

    def __init__(self, configuration: AdobeAuthenticationConfiguration):
        self.organization_id = configuration.organization_id
        self.technical_account_id = configuration.technical_account_id
        self.client_id = configuration.client_id
        self.private_key = configuration.private_key
        self.client_secrent = configuration.client_secret

    def add_authentication(
        self, request: PreparedRequest, connection_config: ConnectionConfig
    ) -> PreparedRequest:
        """
        Generate an Adobe JWT and add it as bearer auth
        """

        secrets: Optional[Dict[str, Any]] = connection_config.secrets

        token = encode(
            {
                "exp": str(math.floor(time.time() + 60)),
                "iss": f"{assign_placeholders(self.organization_id, secrets)}@AdobeOrg",
                "sub": f"{assign_placeholders(self.technical_account_id, secrets)}@techacct.adobe.com",
                "https://ims-na1.adobelogin.com/s/meta_scope": True,
                "aud": f"https://ims-na1.adobelogin.com/c/{assign_placeholders(self.client_id, secrets)}",
            },
            jwt.utils.base64url_decode(
                assign_placeholders(self.private_key, secrets)  # type: ignore
            ),
            algorithm="RS256",
        )

        request.headers["Authorization"] = f"Bearer {token}"
        return request
