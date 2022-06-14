import logging
from datetime import datetime, timezone
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fideslog.sdk.python.event import AnalyticsEvent
from starlette.middleware.cors import CORSMiddleware

from fidesops.analytics import (
    in_docker_container,
    running_on_local_host,
    send_analytics_event,
)
from fidesops.api.v1.api import api_router
from fidesops.api.v1.exception_handlers import ExceptionHandlers
from fidesops.api.v1.urn_registry import V1_URL_PREFIX
from fidesops.common_exceptions import FunctionalityNotConfigured
from fidesops.core.config import config
from fidesops.db.database import init_db
from fidesops.schemas.analytics import EVENT
from fidesops.tasks.scheduled.scheduler import scheduler
from fidesops.tasks.scheduled.tasks import initiate_scheduled_request_intake
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
        init_db(config.database.SQLALCHEMY_DATABASE_URI)

    scheduler.start()

    if config.database.ENABLED:
        logger.info("Starting scheduled request intake...")
        initiate_scheduled_request_intake()

    send_analytics_event(
        AnalyticsEvent(
            docker=in_docker_container(),
            event=EVENT.server_start.value,
            event_created_at=datetime.now(tz=timezone.utc),
            local_host=running_on_local_host(),
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
