from typing import Dict, cast

from requests import PreparedRequest, post

from fides.api.common_exceptions import FidesopsException
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.schemas.saas.strategy_configuration import StrategyConfiguration
from fides.api.service.authentication.authentication_strategy import (
    AuthenticationStrategy,
)
from fides.api.util.saas_util import assign_placeholders


class YotpoReviewsAuthenticationConfiguration(StrategyConfiguration):
    """
    Parameters to authorize a Yotpo Reviews connection
    """

    store_id: str
    secret_key: str


class YotpoReviewsAuthenticationStrategy(AuthenticationStrategy):
    """
    Generates a token from the provided store ID and secret key.
    """

    name = "yotpo_reviews"
    configuration_model = YotpoReviewsAuthenticationConfiguration

    def __init__(self, configuration: YotpoReviewsAuthenticationConfiguration):
        self.store_id = configuration.store_id
        self.secret_key = configuration.secret_key

    def add_authentication(
        self, request: PreparedRequest, connection_config: ConnectionConfig
    ) -> PreparedRequest:
        """
        Retrieves an access token using the provided store ID and secret key
        """

        secrets = cast(Dict, connection_config.secrets)

        response = post(
            url=f"https://api.yotpo.com/core/v3/stores/{assign_placeholders(self.store_id, secrets)}/access_tokens",
            json={
                "secret": assign_placeholders(self.secret_key, secrets),
            },
        )

        if response.ok:
            json_response = response.json()
            access_token = json_response.get("access_token")
        else:
            raise FidesopsException(f"Unable to get access token {response.json()}")

        request.headers["X-Yotpo-Token"] = access_token
        request.headers["x-utoken"] = access_token
        return request
