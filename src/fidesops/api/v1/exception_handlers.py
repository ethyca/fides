from typing import Callable, List

from fastapi import Request
from fastapi.responses import JSONResponse, Response
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from fidesops.common_exceptions import FunctionalityNotConfigured


class ExceptionHandlers:
    @staticmethod
    def functionality_not_configured_handler(
        request: Request, exc: FunctionalityNotConfigured
    ) -> JSONResponse:
        return JSONResponse(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR, content={"message": str(exc)}
        )

    @classmethod
    def get_handlers(cls) -> List[Callable[[Request, Exception], Response]]:
        return [ExceptionHandlers.functionality_not_configured_handler]
