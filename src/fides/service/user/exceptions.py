"""
User service exceptions - domain-specific errors for user operations.

These exceptions are raised by the UserService and should be mapped to
appropriate HTTP responses by the API layer.
"""


class UserServiceError(Exception):
    """Base exception for user service operations."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class UsernameAlreadyExistsError(UserServiceError):
    """Raised when attempting to create a user with an existing username."""

    pass


class EmailAlreadyExistsError(UserServiceError):
    """Raised when attempting to create a user with an existing email address."""

    pass


class DeletedUsernameError(UserServiceError):
    """Raised when attempting to reuse a username that belongs to a soft-deleted user."""

    pass


class DeletedEmailError(UserServiceError):
    """Raised when attempting to reuse an email that belongs to a soft-deleted user."""

    pass


class UserNotFoundError(UserServiceError):
    """Raised when a user cannot be found."""

    pass


class InvalidPasswordError(UserServiceError):
    """Raised when password validation fails."""

    pass
