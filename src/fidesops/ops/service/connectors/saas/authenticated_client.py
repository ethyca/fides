from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from requests import PreparedRequest, Request, Response, Session

from fidesops.ops.common_exceptions import (
    ClientUnsuccessfulException,
    ConnectionException,
)
from fidesops.ops.core.config import config

if TYPE_CHECKING:
    from fidesops.ops.models.connectionconfig import ConnectionConfig
    from fidesops.ops.schemas.saas.saas_config import ClientConfig
    from fidesops.ops.schemas.saas.shared_schemas import SaaSRequestParams

logger = logging.getLogger(__name__)


class AuthenticatedClient:
    """
    A helper class to build authenticated HTTP requests based on
    authentication and parameter configurations. Optionally allows
    a request client config to override the root client config.
    """

    def __init__(
        self,
        uri: str,
        configuration: ConnectionConfig,
        request_client_config: Optional[ClientConfig] = None,
    ):
        saas_config = configuration.get_saas_config()
        self.configuration = configuration
        self.session = Session()
        self.uri = uri
        self.key = configuration.key
        self.client_config = (
            request_client_config
            if request_client_config
            else saas_config.client_config  # type: ignore
        )
        self.secrets = configuration.secrets

    def get_authenticated_request(
        self, request_params: SaaSRequestParams
    ) -> PreparedRequest:
        """
        Returns an authenticated request based on the client config and
        incoming path, headers, query, and body params.
        """

        from fidesops.ops.service.authentication.authentication_strategy import (  # pylint: disable=R0401
            AuthenticationStrategy,
        )

        req: PreparedRequest = Request(
            method=request_params.method,
            url=f"{self.uri}{request_params.path}",
            headers=request_params.headers,
            params=request_params.query_params,
            data=request_params.body,
        ).prepare()

        # add authentication if provided
        if self.client_config.authentication:
            auth_strategy = AuthenticationStrategy.get_strategy(
                self.client_config.authentication.strategy,
                self.client_config.authentication.configuration,
            )
            return auth_strategy.add_authentication(req, self.configuration)

        # otherwise just return the prepared request
        return req

    def send(
        self, request_params: SaaSRequestParams, ignore_errors: Optional[bool] = False
    ) -> Response:
        """
        Builds and executes an authenticated request.
        Optionally ignores non-200 responses if ignore_errors is set to True
        """
        try:
            prepared_request: PreparedRequest = self.get_authenticated_request(
                request_params
            )
            response = self.session.send(prepared_request)
        except Exception as exc:  # pylint: disable=W0703
            if config.dev_mode:  # pylint: disable=R1720
                raise ConnectionException(
                    f"Operational Error connecting to '{self.key}' with error: {exc}"
                )
            else:
                raise ConnectionException(
                    f"Operational Error connecting to '{self.key}'."
                )

        log_request_and_response_for_debugging(
            prepared_request, response
        )  # Dev mode only

        if not response.ok:
            if ignore_errors:
                logger.info(
                    "Ignoring errors on response with status code %s as configured.",
                    response.status_code,
                )
                return response

            raise ClientUnsuccessfulException(status_code=response.status_code)

        return response


def log_request_and_response_for_debugging(
    prepared_request: PreparedRequest, response: Response
) -> None:
    """Log SaaS request and response in dev mode only"""
    if config.dev_mode:
        logger.info(
            "\n\n-----------SAAS REQUEST-----------"
            "\n%s %s"
            "\nheaders: %s"
            "\nbody: %s"
            "\nresponse: %s",
            prepared_request.method,
            prepared_request.url,
            prepared_request.headers,
            prepared_request.body,
            response._content,  # pylint: disable=W0212
        )
