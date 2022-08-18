from typing import Callable, List

from fastapi import Request
from fastapi.responses import JSONResponse
from fidesops.ops.common_exceptions import FunctionalityNotConfigured
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR


class ExceptionHandlers:
    @staticmethod
    def functionality_not_configured_handler(
        request: Request, exc: FunctionalityNotConfigured
    ) -> JSONResponse:
        return JSONResponse(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR, content={"message": str(exc)}
        )

    @classmethod
    def get_handlers(
        cls,
    ) -> List[Callable[[Request, FunctionalityNotConfigured], JSONResponse]]:
        return [ExceptionHandlers.functionality_not_configured_handler]
