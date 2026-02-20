from typing import Callable, List

from fastapi import Request
from fastapi.exceptions import ResponseValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.status import (
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from fides.api.common_exceptions import RedisNotConfigured


async def response_validation_error_handler(
    request: Request, exc: ResponseValidationError
) -> JSONResponse:
    """Handle ResponseValidationError raised during FastAPI response serialization.

    This occurs when data read from the database no longer passes the response
    model's validators — for example, a dataset field with data_type='string'
    that has sub-fields (should be 'object').
    """
    errors = exc.errors()
    field_errors = [
        {
            "loc": error.get("loc"),
            "msg": error.get("msg"),
            "type": error.get("type"),
        }
        for error in errors
    ]
    logger.error(
        f"Response validation error for {request.method} {request.url.path}: "
        f"{len(field_errors)} validation error(s): {field_errors}"
    )
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "The requested resource contains data that fails validation "
            "when serializing the response.",
            "errors": field_errors,
        },
    )


class ExceptionHandlers:
    @staticmethod
    def redis_not_configured_handler(
        request: Request, exc: RedisNotConfigured
    ) -> JSONResponse:
        return JSONResponse(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR, content={"message": str(exc)}
        )

    @classmethod
    def get_handlers(
        cls,
    ) -> List[Callable[[Request, RedisNotConfigured], JSONResponse]]:
        return [ExceptionHandlers.redis_not_configured_handler]
