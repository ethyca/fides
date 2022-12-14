from __future__ import annotations

from fastapi import HTTPException, status

from fides.lib.oauth.scopes import SCOPES


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
