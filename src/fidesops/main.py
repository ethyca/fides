import logging

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from fidesops.api.v1.api import api_router
from fidesops.api.v1.exception_handlers import ExceptionHandlers
from fidesops.api.v1.urn_registry import V1_URL_PREFIX
from fidesops.common_exceptions import FunctionalityNotConfigured
from fidesops.core.config import config
from fidesops.db.database import init_db
from fidesops.tasks.scheduled.scheduler import scheduler
from fidesops.tasks.scheduled.tasks import initiate_scheduled_request_intake
from fidesops.util.logger import get_fides_log_record_factory

logging.basicConfig(level=logging.INFO)
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


def start_webserver() -> None:
    """Run any pending DB migrations and start the webserver."""
    logger.info("****************fidesops****************")
    if config.database.ENABLED:
        logger.info("Running any pending DB migrations...")
        init_db(config.database.SQLALCHEMY_DATABASE_URI, config.package.PATH)

    scheduler.start()

    if config.database.ENABLED:
        logger.info("Starting scheduled request intake...")
        initiate_scheduled_request_intake()

    logger.info("Starting web server...")
    uvicorn.run(
        "fidesops.main:app",
        host="0.0.0.0",
        port=8080,
        log_config=None,
        reload=config.hot_reloading,
    )


if __name__ == "__main__":
    start_webserver()
