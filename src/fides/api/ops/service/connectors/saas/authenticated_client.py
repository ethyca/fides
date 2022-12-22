from __future__ import annotations

import email
import re
import time
from functools import wraps
from time import sleep
from typing import TYPE_CHECKING, Any, Callable, List, Optional, Union

from loguru import logger
from requests import PreparedRequest, Request, Response, Session

from fides.api.ops.common_exceptions import (
    ClientUnsuccessfulException,
    ConnectionException,
    FidesopsException,
)
from fides.api.ops.service.connectors.limiter.rate_limiter import (
    RateLimiter,
    RateLimiterPeriod,
    RateLimiterRequest,
)
from fides.core.config import get_config

if TYPE_CHECKING:
    from fides.api.ops.models.connectionconfig import ConnectionConfig
    from fides.api.ops.schemas.limiter.rate_limit_config import RateLimitConfig
    from fides.api.ops.schemas.saas.saas_config import ClientConfig
    from fides.api.ops.schemas.saas.shared_schemas import SaaSRequestParams


CONFIG = get_config()


class AuthenticatedClient:
    """
    A helper class to build authenticated HTTP requests based on
    authentication and parameter configurations.
    """

    def __init__(
        self,
        uri: str,
        configuration: ConnectionConfig,
        client_config: ClientConfig,
        rate_limit_config: Optional[RateLimitConfig] = None,
    ):
        self.session = Session()
        self.uri = uri
        self.configuration = configuration
        self.client_config = client_config
        self.rate_limit_config = rate_limit_config

    def get_authenticated_request(
        self, request_params: SaaSRequestParams
    ) -> PreparedRequest:
        """
        Returns an authenticated request based on the client config and
        incoming path, headers, query, and body params.
        """

        from fides.api.ops.service.authentication.authentication_strategy import (  # pylint: disable=R0401
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

    def retry_send(  # type: ignore
        retry_count: int,
        backoff_factor: float,
        retry_status_codes: List[int] = [429, 502, 503, 504],
    ) -> Callable:
        """
        Retry decorator for http requests, backing off exponentially or listening to server retry-after header

        Exponential backoff factor uses the following formula:
        backoff_factor * (2 ** (retry_attempt))
        For an backoff_factor of 1 it will sleep for 2,4,8 seconds

        General exceptions are not retried. RequestFailureResponseException exceptions are only retried
        if the status code is in retry_status_codes.
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def result(*args: Any, **kwargs: Any) -> Response:
                self = args[0]
                last_exception: Optional[Union[BaseException, Exception]] = None

                for attempt in range(retry_count + 1):
                    sleep_time = backoff_factor * (2 ** (attempt + 1))
                    try:
                        return func(*args, **kwargs)
                    except RequestFailureResponseException as exc:  # pylint: disable=W0703
                        response: Response = exc.response
                        status_code: int = response.status_code
                        last_exception = ClientUnsuccessfulException(
                            status_code=status_code
                        )

                        if status_code not in retry_status_codes:
                            break

                        # override sleep time if retry after header is found
                        retry_after_time = get_retry_after(response)
                        sleep_time = (
                            retry_after_time if retry_after_time else sleep_time
                        )
                    except Exception as exc:  # pylint: disable=W0703
                        dev_mode_log = f" with error: {exc}" if CONFIG.dev_mode else ""
                        last_exception = ConnectionException(
                            f"Operational Error connecting to '{self.configuration.key}'{dev_mode_log}"
                        )
                        # requests library can raise ConnectionError, Timeout or TooManyRedirects
                        # we will not retry these as they don't usually point to intermittent issues
                        break

                    if attempt < retry_count:
                        logger.warning(
                            "Retrying http request in {} seconds", sleep_time
                        )
                        sleep(sleep_time)

                raise last_exception  # type: ignore

            return result

        return decorator

    def build_rate_limit_requests(self) -> List[RateLimiterRequest]:
        """
        Builds rate limit request objects for client's rate limit config

        Returns empty list if a rate limit config is not provided or is not enabled
        """
        if not self.rate_limit_config or not self.rate_limit_config.enabled:
            return []

        rate_limit_requests = [
            RateLimiterRequest(
                key=rate_limit.custom_key or self.configuration.key,
                rate_limit=rate_limit.rate,
                period=RateLimiterPeriod[rate_limit.period.name.upper()],
            )
            for rate_limit in (self.rate_limit_config.limits or [])
        ]
        return rate_limit_requests

    @retry_send(retry_count=3, backoff_factor=1.0)  # pylint: disable=E1124
    def send(
        self,
        request_params: SaaSRequestParams,
        ignore_errors: Optional[bool] = False,
    ) -> Response:
        """
        Builds and executes an authenticated request.
        Optionally ignores non-200 responses if ignore_errors is set to True
        """
        rate_limit_requests = self.build_rate_limit_requests()
        RateLimiter().limit(rate_limit_requests)

        prepared_request: PreparedRequest = self.get_authenticated_request(
            request_params
        )
        response = self.session.send(prepared_request)

        log_request_and_response_for_debugging(
            prepared_request, response
        )  # Dev mode only

        if not response.ok:
            if ignore_errors:
                logger.info(
                    "Ignoring errors on response with status code {} as configured.",
                    response.status_code,
                )
                return response
            raise RequestFailureResponseException(response=response)
        return response


class RequestFailureResponseException(FidesopsException):
    """Exception class which preserves http response"""

    response: Response

    def __init__(self, response: Response):
        super().__init__("Received failure response from server")
        self.response = response


def log_request_and_response_for_debugging(
    prepared_request: PreparedRequest, response: Response
) -> None:
    """Log SaaS request and response in dev mode only"""
    if CONFIG.dev_mode:
        logger.info(
            "\n\n-----------SAAS REQUEST-----------"
            "\n{} {}"
            "\nheaders: {}"
            "\nbody: {}"
            "\nresponse: {}",
            prepared_request.method,
            prepared_request.url,
            prepared_request.headers,
            prepared_request.body,
            response._content,  # pylint: disable=W0212
        )


def get_retry_after(response: Response, max_retry_after: int = 300) -> Optional[float]:
    """Given a Response object, parses Retry-After header and calculates how long we should sleep for"""
    retry_after = response.headers.get("Retry-After", None)

    if retry_after is None:
        return None

    seconds: float
    # if a number value is provided the server is telling us to sleep for X seconds
    if re.match(r"^\s*[0-9]+\s*$", retry_after):
        seconds = int(retry_after)
    # else we will attempt to parse a timestamp and diff with current time
    else:
        retry_date_tuple = email.utils.parsedate_tz(retry_after)
        if retry_date_tuple is None:
            return None

        retry_date = email.utils.mktime_tz(retry_date_tuple)
        seconds = retry_date - time.time()

    seconds = max(seconds, 0)
    return min(seconds, max_retry_after)
