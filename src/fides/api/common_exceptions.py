from __future__ import annotations

from typing import List

from fastapi import HTTPException, status
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
)

from fides.common.api.scope_registry import SCOPE_REGISTRY as SCOPES


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


class SystemManagerException(FidesopsException):
    """Exception class when there are errors making a systemmanager"""


class ConnectionException(FidesopsException):
    """Exception class when there are errors making a connection"""


class InsufficientDataException(FidesopsException):
    """Exception class when there is not sufficient data to proceed"""


class SkippingConsentPropagation(BaseException):
    """Skipping consent propagation for collection. Used to trigger "skipped" execution logs being created where applicable
    for Privacy Preference requests on saas connectors.
    """


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


class StorageConfigValidationError(ValueError):
    """The Storage Config you are trying to create has invalid data"""


class InvalidDataTypeValidationError(ValueError):
    """The specified data type is invalid."""


class RuleTargetValidationError(ValueError):
    """The Rule you are trying to create has invalid data"""


class DataCategoryNotSupported(ValueError):
    """The data category you have supplied is not supported."""


class PolicyNotFoundException(Exception):
    """Policy could not be found"""


class ResumeTaskException(Exception):
    """Issue restoring data from collection to resume Privacy Request Processing"""


class ConnectorNotFoundException(Exception):
    """Connector could not be found"""


class DrpActionValidationError(Exception):
    """A resource already exists with this DRP Action."""


class StorageConfigNotFoundException(BaseException):
    """Custom Exception - StorageConfig Not Found"""


class SystemNotFound(BaseException):
    """System Not Found"""


class PrivacyNoticeHistoryNotFound(BaseException):
    """PrivacyNoticeHistory Not Found"""


class ConsentHistorySaveError(BaseException):
    """PrivacyPreferenceHistory or ServedNoticeHistory Save Error"""


class IdentityNotFoundException(BaseException):
    """Identity Not Found"""


class WebhookOrderException(BaseException):
    """Custom Exception - Issue with webhooks order"""


class PostProcessingException(BaseException):
    """Custom Exception - Issue with post processing"""


class CollectionDisabled(BaseException):
    """Collection is attached to disabled ConnectionConfig"""


class ActionDisabled(BaseException):
    """Collection is attached to a ConnectionConfig that has not enabled the given action"""


class NotSupportedForCollection(BaseException):
    """The given action is not supported for this type of collection"""


class PrivacyRequestExit(BaseException):
    """Privacy request exiting processing waiting on subtasks to complete"""


class PrivacyRequestCanceled(BaseException):
    """Privacy Request has been Canceled"""


class PrivacyRequestPaused(BaseException):
    """Halt Instruction Received on Privacy Request"""


class PrivacyRequestNotFound(BaseException):
    """Privacy Request Not Found"""


class RequestTaskNotFound(BaseException):
    """Privacy Request Task Not Found"""


class AwaitingAsyncTaskCallback(BaseException):
    """Request Task is Awaiting Processing - Awaiting Async Task Callback"""


class UpstreamTasksNotReady(BaseException):
    """Privacy Request Task awaiting upstream tasks"""


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


class MessagingConfigValidationException(FidesopsException):
    """Custom Exception - Messaging Config Could Not Be Created, Updated, or Deleted"""


class MessageDispatchException(FidesopsException):
    """Custom Exception - Message Dispatch Error"""


class EmailTemplateUnhandledActionType(FidesopsException):
    """Custom Exception - Email Template Unhandled ActionType Error"""


class EmailTemplateNotFoundException(FidesopsException):
    """Custom Exception - Email Template Not Found"""


class MessagingTemplateValidationException(FidesopsException):
    """Custom Exception - Messaging Template Could Not Be Created, Updated, or Deleted"""


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


class NoSuchConnectionTypeSecretSchemaError(Exception):
    """Exception for when a connection type secret schema is not found."""


class SSHTunnelConfigNotFoundException(Exception):
    """Exception for when Fides is configured to use an SSH tunnel without config provided."""


class MalisciousUrlException(Exception):
    """Fides has detected a potentially maliscious URL."""


class AuthenticationError(HTTPException):
    """To be raised when attempting to fetch an access token using
    invalid credentials.
    """

    def __init__(self, detail: str) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
        )


class AuthorizationError(HTTPException):
    """Throws an HTTP 403"""

    def __init__(self, detail: str) -> None:
        """Override the regular HTTPException throwing only a 403"""
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class ClientWriteFailedError(HTTPException):
    """To be raised when a client cannot be created."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Failed to create client",
        )


class ClientNotFoundError(HTTPException):
    """To be raised when attempting to fetch a client that does not exist."""

    def __init__(self, client_id: str) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Client does not exist",
                "id": client_id,
            },
        )


class ExpiredTokenError(HTTPException):
    """To be raised when a provided token is expired."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="OAuth token expired",
        )


class InvalidAuthorizationSchemeError(HTTPException):
    """To be raised when attempting to authenticate with an unexpected
    Authorization header value.
    """

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to authenticate",
            headers={"WWW-Authenticate": "Bearer"},
        )


class InvalidScopeError(HTTPException):
    """To be raised when a provided scope does not exist."""

    def __init__(self, invalid_scopes: list[str]) -> None:
        SCOPES.sort()

        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "Invalid scope provided",
                "invalid_scopes": invalid_scopes,
                "valid_scopes": SCOPES,
            },
        )


class KeyOrNameAlreadyExists(Exception):
    """A resource already exists with this key or name."""


class KeyValidationError(Exception):
    """The resource you're trying to create has a key specified but not
    a name specified.
    """


class MissingConfig(Exception):
    """Custom exception for when no valid configuration file is provided."""


class MonitorConfigNotFoundException(BaseException):
    """MonitorConfig could not be found"""
