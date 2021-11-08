import logging
import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from fidesops.api.v1.api import api_router
from fidesops.api.v1.urn_registry import V1_URL_PREFIX
from fidesops.db.database import init_db
from fidesops.core.config import config
from fidesops.tasks.scheduled.tasks import initiate_scheduled_request_intake

logging.basicConfig(level=logging.INFO)
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


def start_webserver() -> None:
    """Run any pending DB migrations and start the webserver."""
    logger.info("****************fidesops****************")
    logger.info("Running any pending DB migrations...")
    init_db(config.database.SQLALCHEMY_DATABASE_URI)

    logger.info("Starting scheduled request intake...")
    initiate_scheduled_request_intake()

    logger.info("Starting web server...")
    uvicorn.run(
        "src.fidesops.main:app", host="0.0.0.0", port=8080, log_config=None, reload=True
    )


if __name__ == "__main__":
    start_webserver()
