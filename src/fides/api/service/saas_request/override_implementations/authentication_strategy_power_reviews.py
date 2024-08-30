
from typing import Dict, cast
from requests import PreparedRequest, post
from fides.api.common_exceptions import FidesopsException
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.schemas.saas.strategy_configuration import StrategyConfiguration
from fides.api.service.authentication.authentication_strategy import AuthenticationStrategy
from loguru import logger
from fides.api.util.logger_context_utils import (
    request_details,
)
class PowerReviewsAuthenticationConfiguration(StrategyConfiguration):
    """
    Parameters to authorize a PowerReviews connection
    """

    client_id: str
    client_secret: str


class PowerReviewsAuthenticationStrategy(AuthenticationStrategy):
    """
    Generates a token from the provided client ID and client secret.
    """

    name = "power_reviews"
    configuration_model = PowerReviewsAuthenticationConfiguration

    def __init__(self, configuration: PowerReviewsAuthenticationConfiguration):
        self.client_id = configuration.client_id
        self.client_secret = configuration.client_secret

    def add_authentication(
        self, request: PreparedRequest, connection_config: ConnectionConfig
    ) -> PreparedRequest:
        """
        Retrieves an access token using the provided client ID and client secret
        """

        response = post(
            url=f"https://api.powerreviews.com/oauth2/token",
            auth=(self.client_id, self.client_secret),
            data={
                "grant_type": "client_credentials",
            },
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
            }
        )

        context_logger = logger.bind(
            **request_details(request, response)
        )

        if response.ok:
            json_response = response.json()
            access_token = json_response.get("access_token")
            context_logger.info("Retrieved Access Token.")
            context_logger.info(access_token)


        else:
            raise FidesopsException(f"Unable to get access token {response.json()}")

        request.headers["Authorization"] = f"Bearer {access_token}"
        return request
