import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fideslog.sdk.python.event import AnalyticsEvent
from redis.exceptions import ResponseError
from starlette.background import BackgroundTask
from starlette.middleware.cors import CORSMiddleware

from fidesops.analytics import (
    accessed_through_local_host,
    in_docker_container,
    send_analytics_event,
)
from fidesops.api.v1.api import api_router
from fidesops.api.v1.exception_handlers import ExceptionHandlers
from fidesops.api.v1.urn_registry import V1_URL_PREFIX
from fidesops.common_exceptions import FunctionalityNotConfigured, RedisConnectionError
from fidesops.core.config import config
from fidesops.db.database import init_db
from fidesops.schemas.analytics import Event, ExtraData
from fidesops.tasks.scheduled.scheduler import scheduler
from fidesops.tasks.scheduled.tasks import initiate_scheduled_request_intake
from fidesops.util.cache import get_cache
from fidesops.util.logger import get_fides_log_record_factory

logging.basicConfig(level=config.security.LOG_LEVEL)
logging.setLogRecordFactory(get_fides_log_record_factory())
logger = logging.getLogger(__name__)

app = FastAPI(title="fidesops", openapi_url=f"{V1_URL_PREFIX}/openapi.json")

# Set all CORS enabled origins
if config.security.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in config.security.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.middleware("http")
async def dispatch_log_request(request: Request, call_next: Callable) -> Response:
    """
    HTTP Middleware that logs analytics events for each call to Fidesops endpoints.
    :param request: Request to fidesops api
    :param call_next: Callable api endpoint
    :return: Response
    """
    fides_source: Optional[str] = request.headers.get("X-Fides-Source")
    now: datetime = datetime.now(tz=timezone.utc)
    endpoint = f"{request.method}: {request.url}"

    try:
        response = await call_next(request)
        # HTTPExceptions are considered a handled err by default so are not thrown here.
        # Accepted workaround is to inspect status code of response.
        # More context- https://github.com/tiangolo/fastapi/issues/1840
        response.background = BackgroundTask(
            prepare_and_log_request,
            endpoint,
            request.url.hostname,
            response.status_code,
            now,
            fides_source,
            "HTTPException" if response.status_code >= 400 else None,
        )
        return response

    except Exception as e:
        prepare_and_log_request(
            endpoint, request.url.hostname, 500, now, fides_source, e.__class__.__name__
        )
        raise


def prepare_and_log_request(
    endpoint: str,
    hostname: Optional[str],
    status_code: int,
    event_created_at: datetime,
    fides_source: Optional[str],
    error_class: Optional[str],
) -> None:
    """
    Prepares and sends analytics event provided the user is not opted out of analytics.
    """

    # this check prevents AnalyticsEvent from being called with invalid endpoint during unit tests
    if config.root_user.ANALYTICS_OPT_OUT:
        return
    send_analytics_event(
        AnalyticsEvent(
            docker=in_docker_container(),
            event=Event.endpoint_call.value,
            event_created_at=event_created_at,
            local_host=accessed_through_local_host(hostname),
            endpoint=endpoint,
            status_code=status_code,
            error=error_class or None,
            extra_data={ExtraData.fides_source.value: fides_source}
            if fides_source
            else None,
        )
    )


app.include_router(api_router)
for handler in ExceptionHandlers.get_handlers():
    app.add_exception_handler(FunctionalityNotConfigured, handler)


@app.on_event("startup")
async def create_webapp_dir_if_not_exists() -> None:
    """Creates the webapp directory if it doesn't exist."""
    if config.admin_ui.ENABLED:
        WEBAPP_DIRECTORY = Path("src/fidesops/build/static")
        WEBAPP_INDEX = WEBAPP_DIRECTORY / "index.html"
        if not WEBAPP_INDEX.is_file():
            WEBAPP_DIRECTORY.mkdir(parents=True, exist_ok=True)
            with open(WEBAPP_DIRECTORY / "index.html", "w") as index_file:
                index_file.write("<h1>Privacy is a Human Right!</h1>")

        app.mount("/static", StaticFiles(directory=WEBAPP_DIRECTORY), name="static")
        logger.info("Mounted static file directory...")


def start_webserver() -> None:
    """Run any pending DB migrations and start the webserver."""
    logger.info("****************fidesops****************")

    if logger.getEffectiveLevel() == logging.DEBUG:
        logger.warning(
            "WARNING: log level is DEBUG, so sensitive or personal data may be logged. "
            "Set FIDESOPS__SECURITY__LOG_LEVEL to INFO or higher in production."
        )
        config.log_all_config_values()

    if config.database.ENABLED:
        logger.info("Running any pending DB migrations...")
        try:
            init_db(config.database.SQLALCHEMY_DATABASE_URI)
        except Exception as error:  # pylint: disable=broad-except
            logger.error(f"Connection to database failed: {error}")
            return

    if config.redis.ENABLED:
        logger.info("Running Redis connection test...")
        try:
            get_cache()
        except (RedisConnectionError, ResponseError) as e:
            logger.error(f"Connection to cache failed: {e}")
            return

    scheduler.start()

    if config.database.ENABLED:
        logger.info("Starting scheduled request intake...")
        initiate_scheduled_request_intake()

    send_analytics_event(
        AnalyticsEvent(
            docker=in_docker_container(),
            event=Event.server_start.value,
            event_created_at=datetime.now(tz=timezone.utc),
        )
    )

    logger.info("Starting web server...")
    uvicorn.run(
        "fidesops.main:app",
        host="0.0.0.0",
        port=config.PORT,
        log_config=None,
        reload=config.hot_reloading,
    )


if __name__ == "__main__":
    start_webserver()
