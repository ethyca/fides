from datetime import datetime, timedelta
from typing import Dict, Optional, cast

from loguru import logger
from requests import PreparedRequest, post
from sqlalchemy.orm import Session

from fides.api.common_exceptions import FidesopsException
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.schemas.saas.strategy_configuration import StrategyConfiguration
from fides.api.service.authentication.authentication_strategy import (
    AuthenticationStrategy,
)
from fides.api.util.saas_util import assign_placeholders


class FriendbuyNextgenAuthenticationConfiguration(StrategyConfiguration):
    """
    Parameters to authorize a Friendbuy Nextgen connection
    """

    key: str
    secret: str


class FriendbuyNextgenAuthenticationStrategy(AuthenticationStrategy):
    """
    Generates a token from the provided key and secret.
    Stores the expiration time to know when to refresh the token.
    """

    name = "friendbuy_nextgen"
    configuration_model = FriendbuyNextgenAuthenticationConfiguration

    def __init__(self, configuration: FriendbuyNextgenAuthenticationConfiguration):
        self.key = configuration.key
        self.secret = configuration.secret

    def add_authentication(
        self, request: PreparedRequest, connection_config: ConnectionConfig
    ) -> PreparedRequest:
        """
        Retrieves a token using the provided key and secret
        """

        secrets = cast(Dict, connection_config.secrets)
        domain: Optional[str] = secrets.get("domain")
        token: Optional[str] = secrets.get("token")
        expires_at: Optional[int] = secrets.get("expires_at")

        if not token or self.close_to_expiration(expires_at, connection_config):
            response = post(
                url=f"https://{domain}/v1/authorization",
                json={
                    "key": assign_placeholders(self.key, secrets),
                    "secret": assign_placeholders(self.secret, secrets),
                },
            )

            if response.ok:
                json_response = response.json()
                token = json_response.get("token")
                expires_at = int(
                    datetime.strptime(
                        json_response.get("expires"), "%Y-%m-%dT%H:%M:%S.%fZ"
                    ).timestamp()
                )

                # merge the new values into the existing connection_config secrets
                db = Session.object_session(connection_config)
                updated_secrets = {
                    **secrets,
                    **{
                        "token": token,
                        "expires_at": expires_at,
                    },
                }
                connection_config.update(db, data={"secrets": updated_secrets})
                logger.info(
                    "Successfully updated the token for {}",
                    connection_config.key,
                )
            else:
                raise FidesopsException(f"Unable to get token {response.json()}")

        request.headers["Authorization"] = f"Bearer {token}"
        return request

    @staticmethod
    def close_to_expiration(
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
