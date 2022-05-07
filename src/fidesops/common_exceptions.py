from typing import List

from fastapi import HTTPException

from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)


class FidesopsException(Exception):
    """Base class for fidesops exceptions"""

    def __init__(self, message: str, errors: List[str] = []):
        super().__init__(message)
        self.message = message
        self.errors = errors


class TraversalError(FidesopsException):
    """Fidesops error with the names of all nodes that could not be reached."""


class ValidationError(FidesopsException):
    """Data does not pass validation."""


class StorageUploadError(FidesopsException):
    """Data cannot be uploaded to storage destination"""


class ConnectionException(FidesopsException):
    """Exception class when there are errors making a connection"""


class InsufficientDataException(FidesopsException):
    """Exception class when there is not sufficient data to proceed"""


class RedisConnectionError(Exception):
    """The Configured Redis instance is uncontactable."""


class MisconfiguredPolicyException(Exception):
    """Thrown when a Privacy Request cannot be processed due to a misconfigured Policy."""


class PolicyValidationError(ValueError):
    """The policy you are trying to create has invalid data"""


class InvalidDataLengthValidationError(ValueError):
    """The length provided is invalid"""


class RuleValidationError(ValueError):
    """The Rule you are trying to create has invalid data"""


class InvalidDataTypeValidationError(ValueError):
    """The specified data type is invalid."""


class RuleTargetValidationError(ValueError):
    """The Rule you are trying to create has invalid data"""


class DataCategoryNotSupported(ValueError):
    """The data category you have supplied is not supported."""


class PolicyNotFoundException(Exception):
    """Policy could not be found"""


class ConnectorNotFoundException(Exception):
    """Connector could not be found"""


class KeyOrNameAlreadyExists(Exception):
    """A resource already exists with this key or name."""


class DrpActionValidationError(Exception):
    """A resource already exists with this DRP Action."""


class KeyValidationError(Exception):
    """The resource you're trying to create has a key specified but not a name specified."""


class StorageConfigNotFoundException(BaseException):
    """Custom Exception - StorageConfig Not Found"""


class AuthenticationException(BaseException):
    """Custom Exception - Authentication Failed"""


class WebhookOrderException(BaseException):
    """Custom Exception - Issue with webhooks order"""


class PostProcessingException(BaseException):
    """Custom Exception - Issue with post processing"""


class PrivacyRequestPaused(BaseException):
    """Halt Instruction Received on Privacy Request"""


class SaaSConfigNotFoundException(FidesopsException):
    """Custom Exception - SaaS Config Not Found"""


class AuthenticationFailure(HTTPException):
    """Wrapper for authentication failure exception"""

    def __init__(self, detail: str) -> None:
        super().__init__(status_code=HTTP_401_UNAUTHORIZED, detail=detail)


class BadRequest(HTTPException):
    """Wrapper for bad request exception"""

    def __init__(self, detail: str) -> None:
        super().__init__(status_code=HTTP_400_BAD_REQUEST, detail=detail)


class NotFoundException(HTTPException):
    """Wrapper for not found exception"""

    def __init__(self, detail: str) -> None:
        super().__init__(status_code=HTTP_404_NOT_FOUND, detail=detail)


class AuthorizationError(HTTPException):
    """Throws an HTTP 403"""

    def __init__(self, detail: str) -> None:
        """Override the regular HTTPException throwing only a 403"""
        super().__init__(status_code=HTTP_403_FORBIDDEN, detail=detail)


class ClientUnsuccessfulException(FidesopsException):
    """Exception for when client call fails"""

    def __init__(self, status_code: int):
        super().__init__(message=f"Client call failed with status code '{status_code}'")


class NoSuchStrategyException(ValueError):
    """Exception for when a masking strategy does not exist"""


class MissingConfig(Exception):
    """Custom exception for when no valid configuration file is provided."""
