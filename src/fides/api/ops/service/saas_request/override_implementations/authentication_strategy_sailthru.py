import hashlib
import json
from typing import Dict, List
from urllib.parse import parse_qsl

from requests import PreparedRequest

from fides.api.ops.models.connectionconfig import ConnectionConfig
from fides.api.ops.schemas.saas.strategy_configuration import StrategyConfiguration
from fides.api.ops.service.authentication.authentication_strategy import (
    AuthenticationStrategy,
)
from fides.api.ops.util.saas_util import assign_placeholders


class SailthruAuthenticationConfiguration(StrategyConfiguration):
    """
    Parameters to generate a Sailthru keyed HMAC - an MD5 hash of secret +
    key + format + JSON object
    """

    format: str = "json"
    api_key: str
    secret: str


class SailthruAuthenticationStrategy(AuthenticationStrategy):
    """
    Sailthru Authentication Strategy.

    Uses a "shared-secret hash authentication mechanism", where for each request,
    we create a unique sig value.
    """

    name = "sailthru"
    configuration_model = SailthruAuthenticationConfiguration

    def __init__(self, configuration: SailthruAuthenticationConfiguration):
        self.format = configuration.format
        self.api_key = configuration.api_key
        self.secret = configuration.secret

    @staticmethod
    def generate_sailthru_sig(
        assigned_secret: str, assigned_api_key: str, request_format: str, body: str
    ) -> str:
        """
        Generate a Sailthru sig.

        The Sailthru sig is a MD5 hash of the following concatenated values as a single string:
        the secret, followed by remaining parameter values (api_key, format, and body) sorted alphabetically
        """
        other_param_values: List[str] = [assigned_api_key, request_format, body]
        other_param_values.sort()

        return hashlib.md5(
            (assigned_secret + "".join([val for val in other_param_values]))
            .lower()
            .encode()
        ).hexdigest()

    def add_authentication(
        self, request: PreparedRequest, connection_config: ConnectionConfig
    ) -> PreparedRequest:
        """
        Add the api_key and the sailthru sig to the request body.

        Request body expected to be in application/x-www-form-urlencoded format
        """
        # Replace the placeholders in the "secret" and "api_key" with values from "secrets"
        secret: str = (
            assign_placeholders(self.secret, connection_config.secrets or {}) or ""
        )
        api_key: str = (
            assign_placeholders(self.api_key, connection_config.secrets or {}) or ""
        )

        # Turn the original application/x-www-form-urlencoded request body format into a json string
        original_request_body: str = str(request.body) or ""
        request_body: Dict[str, str] = dict(parse_qsl(original_request_body))
        json_str_body: str = json.dumps(request_body, separators=(",", ":"))

        # Stage updated request data
        new_body: Dict = {
            "api_key": api_key,
            "sig": self.generate_sailthru_sig(
                secret, api_key, self.format, json_str_body
            ),
            "format": self.format,
            "json": json_str_body,
        }

        # Update request body - still should return in application/x-www-form-urlencoded format
        request.prepare_body(data=new_body, files=None, json=False)
        return request
