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
