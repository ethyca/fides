from fastapi import HTTPException, status


class AlreadyExistsError(HTTPException):
    """
    To be raised when attempting to create a new resource violates a uniqueness constraint.
    """

    def __init__(self, resource_type: str, fides_key: str) -> None:
        detail = {
            "error": "resource already exists",
            "resource_type": resource_type,
            "fides_key": fides_key,
        }

        super().__init__(status.HTTP_409_CONFLICT, detail=detail)


class DatabaseUnavailableError(HTTPException):
    """
    To be raised when attempting to connect to an uninitialized database.
    """

    def __init__(self) -> None:
        super().__init__(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "database unavailable"},
        )


class NotFoundError(HTTPException):
    """
    To be raised when a requested resource does not exist in the database.
    """

    def __init__(self, resource_type: str, fides_key: str) -> None:
        detail = {
            "error": "resource does not exist",
            "resource_type": resource_type,
            "fides_key": fides_key,
        }

        super().__init__(status.HTTP_404_NOT_FOUND, detail=detail)


class QueryError(HTTPException):
    """
    To be raised when a database query fails.
    TODO: Improve the messaging here.
    """

    def __init__(self) -> None:
        super().__init__(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "a database query failed"},
        )


class ForbiddenError(HTTPException):
    """
    To be raised when a user cannot modify an entity.
    """

    def __init__(self, resource_type: str, fides_key: str) -> None:
        detail = {
            "error": "user does not have permission to modify",
            "resource_type": resource_type,
            "fides_key": fides_key,
        }
        super().__init__(status.HTTP_403_FORBIDDEN, detail=detail)


def get_full_exception_name(exception: Exception) -> str:
    """Get the full exception name
    i.e. get sqlalchemy.exc.IntegrityError instead of just IntegrityError
    """
    module = exception.__class__.__module__
    if module is None or module == str.__class__.__module__:
        return exception.__class__.__name__
    return module + "." + exception.__class__.__name__


class FunctionalityNotConfigured(Exception):
    """Custom exception for when invoked functionality is unavailable due to configuration."""
