from abc import abstractmethod
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Optional

from loguru import logger
from requests import PreparedRequest, Response
from requests.exceptions import (  # pylint: disable=redefined-builtin
    ConnectionError,
    ConnectTimeout,
    ReadTimeout,
    SSLError,
    TooManyRedirects,
)

from fides.config import CONFIG


class LoggerContextKeys(Enum):
    action_type = "action_type"
    status_code = "status_code"
    body = "body"
    collection = "collection"
    connection_key = "connection_key"
    error_details = "error_details"
    error_group = "error_group"
    method = "method"
    privacy_request_id = "privacy_request_id"
    response = "response"
    system_key = "system_key"
    url = "url"


class ErrorGroup(Enum):
    """A collection of user-friendly error labels to be used in contextualized logs."""

    network_error = "NetworkError"
    authentication_error = "AuthenticationError"
    client_error = "ClientSideError"
    server_error = "ServerSideError"


class Contextualizable:
    """
    An abstract base class that defines a contract for classes which can provide
    contextual information for logging purposes.

    Subclasses of Contextualizable must implement the get_log_context method,
    which should return a dictionary of context information relevant to the object.
    This context will be used by the log_context decorator to add additional
    information to log messages.
    """

    @abstractmethod
    def get_log_context(self) -> Dict[LoggerContextKeys, Any]:
        pass


def log_context(
    _func: Optional[Callable] = None, **additional_context: Any
) -> Callable:
    """
    A decorator that adds context information to log messages. It extracts context from
    the arguments of the decorated function and from any specified additional context.
    Optional additional context is provided through keyword arguments.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            context = dict(additional_context)
            for arg in args:
                if isinstance(arg, Contextualizable):
                    arg_context = arg.get_log_context()
                    # get values from enums
                    context.update(
                        {
                            key.value if isinstance(key, Enum) else key: value
                            for key, value in arg_context.items()
                        }
                    )
            with logger.contextualize(**context):
                return func(*args, **kwargs)

        return wrapper

    if _func is None:
        return decorator
    return decorator(_func)


def request_details(
    prepared_request: PreparedRequest,
    response: Optional[Response] = None,
    ignore_error: bool = False,
) -> Dict[str, Any]:
    """
    Maps the request details and includes response details when "dev mode" is enabled.
    """

    details: Dict[str, Any] = {
        LoggerContextKeys.method.value: prepared_request.method,
        LoggerContextKeys.url.value: prepared_request.url,
    }
    if CONFIG.dev_mode and prepared_request.body is not None:
        if isinstance(prepared_request.body, bytes):
            details[LoggerContextKeys.body.value] = prepared_request.body.decode(
                "utf-8"
            )
        elif isinstance(prepared_request.body, str):
            details[LoggerContextKeys.body.value] = prepared_request.body

    if response is not None:
        if CONFIG.dev_mode and response.content:
            details[LoggerContextKeys.response.value] = response.content.decode("utf-8")

        details[LoggerContextKeys.status_code.value] = response.status_code

        # assign error group only if error should not be ignored
        if not ignore_error:
            if response.status_code in [401, 403]:
                details[LoggerContextKeys.error_group.value] = (
                    ErrorGroup.authentication_error.value
                )
            elif 400 <= response.status_code < 500:
                details[LoggerContextKeys.error_group.value] = (
                    ErrorGroup.client_error.value
                )
            elif 500 <= response.status_code:
                details[LoggerContextKeys.error_group.value] = (
                    ErrorGroup.server_error.value
                )
    return details


def connection_exception_details(exception: Exception, url: str) -> Dict[str, Any]:
    """Maps select connection exceptions to user-friendly error details."""

    details = {
        LoggerContextKeys.error_group.value: ErrorGroup.network_error.value,
        LoggerContextKeys.error_details.value: f"Unknown exception connecting to {url}.",
        LoggerContextKeys.status_code.value: None,
    }
    if isinstance(exception, ConnectTimeout):
        details[LoggerContextKeys.error_details.value] = (
            f"Timeout occurred connecting to {url}."
        )
    elif isinstance(exception, ReadTimeout):
        details[LoggerContextKeys.error_details.value] = (
            f"Timeout occurred waiting for a response from {url}."
        )
    elif isinstance(exception, SSLError):
        details[LoggerContextKeys.error_details.value] = (
            f"SSL exception occurred connecting to {url}."
        )
    elif isinstance(exception, TooManyRedirects):
        details[LoggerContextKeys.error_details.value] = (
            f"Too many redirects occurred connecting to {url}."
        )
    elif isinstance(exception, ConnectionError):
        details[LoggerContextKeys.error_details.value] = f"Unable to connect to {url}."
    return details
