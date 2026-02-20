"""
Base domain exceptions raised by service-layer code.

Route handlers should catch these and translate them into appropriate
HTTP responses. Services must never raise HTTPException directly.
"""


class DomainException(Exception):
    """Base for all domain exceptions raised by services."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ResourceNotFoundError(DomainException):
    """Raised when a requested resource does not exist."""

    def __init__(self, resource_type: str, resource_id: str):
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(f"{resource_type} '{resource_id}' not found")


class ResourceAlreadyExistsError(DomainException):
    """Raised when attempting to create a resource that already exists."""

    def __init__(self, resource_type: str, identifier: str):
        self.resource_type = resource_type
        self.identifier = identifier
        super().__init__(f"{resource_type} '{identifier}' already exists")


class ValidationError(DomainException):
    """Raised when domain validation fails."""

    pass


class AuthorizationError(DomainException):
    """Raised when the requested action is not permitted."""

    pass
