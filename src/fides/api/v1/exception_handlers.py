from typing import Callable, List

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from fides.api.common_exceptions import RedisNotConfigured


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
