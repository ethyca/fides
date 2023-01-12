import math
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, cast

from jwt import encode
from loguru import logger
from requests import PreparedRequest, post
from sqlalchemy.orm import Session

from fides.api.ops.common_exceptions import FidesopsException
from fides.api.ops.models.connectionconfig import ConnectionConfig
from fides.api.ops.schemas.saas.strategy_configuration import StrategyConfiguration
from fides.api.ops.service.authentication.authentication_strategy import (
    AuthenticationStrategy,
)
from fides.api.ops.util.saas_util import assign_placeholders


class AdobeCampaignAuthenticationConfiguration(StrategyConfiguration):
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

    name = "adobe_campaign"
    configuration_model = AdobeCampaignAuthenticationConfiguration

    def __init__(self, configuration: AdobeCampaignAuthenticationConfiguration):
        self.organization_id = configuration.organization_id
        self.technical_account_id = configuration.technical_account_id
        self.client_id = configuration.client_id
        self.client_secret = configuration.client_secret
        self.private_key = configuration.private_key

    def add_authentication(
        self, request: PreparedRequest, connection_config: ConnectionConfig
    ) -> PreparedRequest:
        """
        Generate an Adobe JWT and add it as bearer auth
        """

        secrets = cast(Dict, connection_config.secrets)
        access_token: Optional[str] = secrets.get("access_token")
        expires_at: Optional[int] = secrets.get("expires_at")

        if not access_token or self._close_to_expiration(expires_at, connection_config):
            # generate a JWT token and sign it with the private key
            jwt_token = encode(
                {
                    "exp": math.floor(time.time() + 60),
                    "iss": f"{assign_placeholders(self.organization_id, secrets)}",
                    "sub": f"{assign_placeholders(self.technical_account_id, secrets)}",
                    "https://ims-na1.adobelogin.com/s/ent_campaign_sdk": True,
                    "aud": f"https://ims-na1.adobelogin.com/c/{assign_placeholders(self.client_id, secrets)}",
                },
                str(assign_placeholders(self.private_key, secrets)),
                algorithm="RS256",
            )

            # exchange the short-lived JWT token for longer-lived access token
            response = post(
                url="https://ims-na1.adobelogin.com/ims/exchange/jwt",
                data={
                    "client_id": assign_placeholders(self.client_id, secrets),
                    "client_secret": assign_placeholders(self.client_secret, secrets),
                    "jwt_token": jwt_token,
                },
            )

            if response.ok:
                json_response = response.json()
                access_token = json_response.get("access_token")
                # note: `expires_in` is expressed in ms
                expires_in = json_response.get("expires_in")

                # merge the new values into the existing connection_config secrets
                db = Session.object_session(connection_config)
                updated_secrets = {
                    **secrets,
                    **{
                        "access_token": access_token,
                        "expires_at": (
                            datetime.utcnow() + timedelta(milliseconds=expires_in)
                        ).timestamp(),
                    },
                }
                connection_config.update(db, data={"secrets": updated_secrets})
                logger.info(
                    "Successfully updated the access token for {}",
                    connection_config.key,
                )
            else:
                raise FidesopsException(f"Unable to get access token {response.json()}")

        request.headers["Authorization"] = f"Bearer {access_token}"
        return request

    @staticmethod
    def _close_to_expiration(
        expires_at: Optional[int], connection_config: ConnectionConfig
    ) -> bool:
        """Check if the access_token will expire in the next 10 minutes."""

        if expires_at is None:
            logger.info(
                "The expires_at value is not defined for {}, skipping token refresh",
                connection_config.key,
            )
            return False

        return expires_at < (datetime.utcnow() + timedelta(minutes=10)).timestamp()
