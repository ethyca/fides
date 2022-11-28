from typing import List

from fastapi import HTTPException
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
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


class DrpActionValidationError(Exception):
    """A resource already exists with this DRP Action."""


class StorageConfigNotFoundException(BaseException):
    """Custom Exception - StorageConfig Not Found"""


class IdentityNotFoundException(BaseException):
    """Identity Not Found"""


class WebhookOrderException(BaseException):
    """Custom Exception - Issue with webhooks order"""


class PostProcessingException(BaseException):
    """Custom Exception - Issue with post processing"""


class CollectionDisabled(BaseException):
    """Collection is attached to disabled ConnectionConfig"""


class PrivacyRequestPaused(BaseException):
    """Halt Instruction Received on Privacy Request"""


class NoCachedManualWebhookEntry(BaseException):
    """No manual data exists for this webhook on the given privacy request."""


class ManualWebhookFieldsUnset(BaseException):
    """Manual webhook has fields that are not explicitly set: Likely new field has been added"""


class PrivacyRequestErasureEmailSendRequired(BaseException):
    """Erasure requests will need to be fulfilled by email send.  Exception is raised to change ExecutionLog details"""


class SaaSConfigNotFoundException(FidesopsException):
    """Custom Exception - SaaS Config Not Found"""


class MessagingConfigNotFoundException(FidesopsException):
    """Custom Exception - Messaging Config Not Found"""


class MessageDispatchException(FidesopsException):
    """Custom Exception - Message Dispatch Error"""


class EmailTemplateUnhandledActionType(FidesopsException):
    """Custom Exception - Email Template Unhandled ActionType Error"""


class OAuth2TokenException(FidesopsException):
    """Custom Exception - Unable to access or refresh OAuth2 tokens for SaaS connector"""


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


class ClientUnsuccessfulException(FidesopsException):
    """Exception for when client call fails"""

    def __init__(self, status_code: int):
        super().__init__(message=f"Client call failed with status code '{status_code}'")


class NoSuchStrategyException(ValueError):
    """Exception for when a masking strategy does not exist"""


class FunctionalityNotConfigured(Exception):
    """Custom exception for when invoked functionality is unavailable due to configuration."""


class InvalidSaaSRequestOverrideException(ValueError):
    """Exception for when a provied SaaS request override function is invalid"""


class NoSuchSaaSRequestOverrideException(ValueError):
    """Exception for when a requested SaaS request override function does not exist"""


class IdentityVerificationException(FidesopsException):
    """Custom exceptions for when we cannot verify the identity of a subjct"""
