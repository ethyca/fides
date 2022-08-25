"""
Contains the code that sets up the API.
"""
from datetime import datetime
from logging import WARNING
from typing import Callable

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import FileResponse
from fideslib.oauth.api.deps import get_config as lib_get_config
from fideslib.oauth.api.deps import get_db as lib_get_db
from fideslib.oauth.api.deps import verify_oauth_client as lib_verify_oauth_client
from fideslib.oauth.api.routes.user_endpoints import router as user_router
from loguru import logger as log
from uvicorn import Config, Server

from fides.api.ctl import view
from fides.api.ctl.database.database import configure_db
from fides.api.ctl.deps import get_db, verify_oauth_client
from fides.api.ctl.routes import (
    admin,
    crud,
    datamap,
    generate,
    health,
    user,
    validate,
    visualize,
)
from fides.api.ctl.routes.util import API_PREFIX
from fides.api.ctl.ui import get_admin_index_as_response, get_path_to_admin_ui_file
from fides.api.ctl.utils.logger import setup as setup_logging
from fides.ctl.core.config import FidesctlConfig, get_config as get_ctl_config

import logging
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional, Union

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.exceptions import HTTPException
from fastapi.responses import FileResponse
from fideslib.oauth.api.deps import get_config as lib_get_config
from fideslib.oauth.api.deps import get_db as lib_get_db
from fideslib.oauth.api.deps import verify_oauth_client as lib_verify_oauth_client
from fideslib.oauth.api.routes.user_endpoints import router as user_router
from fideslog.sdk.python.event import AnalyticsEvent
from redis.exceptions import ResponseError
from starlette.background import BackgroundTask
from starlette.middleware.cors import CORSMiddleware
from starlette.status import HTTP_404_NOT_FOUND

from fides.api.ctl.database.database import configure_db
from fides.api.ops.analytics import (
    accessed_through_local_host,
    in_docker_container,
    send_analytics_event,
)
from fides.api.ops.api.deps import get_config, get_db
from fides.api.ops.api.v1.api import api_router
from fides.api.ops.api.v1.exception_handlers import ExceptionHandlers
from fides.api.ops.api.v1.urn_registry import V1_URL_PREFIX
from fides.api.ops.common_exceptions import (
    FunctionalityNotConfigured,
    RedisConnectionError,
)
from fides.api.ops.core.config import config as ops_config
from fides.api.ops.schemas.analytics import Event, ExtraData
from fides.api.ops.service.connectors.saas.connector_registry_service import (
    load_registry,
    registry_file,
)
from fides.api.ops.tasks.scheduled.scheduler import scheduler
from fides.api.ops.tasks.scheduled.tasks import initiate_scheduled_request_intake
from fides.api.ops.util.cache import get_cache
from fides.api.ops.util.logger import Pii, get_fides_log_record_factory
from fides.api.ops.util.oauth_util import verify_oauth_client

logging.basicConfig(level=ops_config.security.log_level)
logging.setLogRecordFactory(get_fides_log_record_factory())
logger = logging.getLogger(__name__)

app = FastAPI(title="fides")
CONFIG: FidesctlConfig = get_ctl_config()
ROUTERS = (
    crud.routers
    + visualize.routers
    + [
        admin.router,
        datamap.router,
        generate.router,
        health.router,
        user.router,
        validate.router,
        view.router,
    ]
)


# Set all CORS enabled origins

if ops_config.security.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in ops_config.security.cors_origins],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def configure_routes() -> None:
    "Include all of the routers not defined in this module."
    for router in ROUTERS:
        app.include_router(router)

    app.include_router(user_router, tags=["Users"], prefix=f"{API_PREFIX}")
    app.include_router(api_router)


# Configure the routes here so we can generate the openapi json file
configure_routes()
app.dependency_overrides[lib_get_config] = get_config
app.dependency_overrides[lib_get_db] = get_db
app.dependency_overrides[lib_verify_oauth_client] = verify_oauth_client

for handler in ExceptionHandlers.get_handlers():
    app.add_exception_handler(FunctionalityNotConfigured, handler)


@app.on_event("startup")
async def setup_server() -> None:
    "Run all of the required setup steps for the webserver."
    if logger.getEffectiveLevel() == logging.DEBUG:
        logger.warning(
            "WARNING: log level is DEBUG, so sensitive or personal data may be logged. "
            "Set FIDESOPS__SECURITY__LOG_LEVEL to INFO or higher in production."
        )
        ops_config.log_all_config_values()

    logger.info("Validating SaaS connector templates...")
    load_registry(registry_file)

    if ops_config.redis.enabled:
        logger.info("Running Redis connection test...")
        try:
            get_cache()
        except (RedisConnectionError, ResponseError) as e:
            logger.error("Connection to cache failed: %s", Pii(str(e)))
            return

    scheduler.start()

    if ops_config.database.enabled:
        logger.info("Starting scheduled request intake...")
        initiate_scheduled_request_intake()

    send_analytics_event(
        AnalyticsEvent(
            docker=in_docker_container(),
            event=Event.server_start.value,
            event_created_at=datetime.now(tz=timezone.utc),
        )
    )

    if not ops_config.execution.worker_enabled:
        logger.info("Starting worker...")
        subprocess.Popen(["fidesops", "worker"])  # pylint: disable=consider-using-with

    setup_logging(
        CONFIG.logging.level,
        serialize=CONFIG.logging.serialization,
        desination=CONFIG.logging.destination,
    )

    log.bind(api_config=CONFIG.logging.json()).debug("Configuration options in use")
    await configure_db(CONFIG.database.sync_database_uri)


@app.middleware("http")
async def log_request(request: Request, call_next: Callable) -> Response:
    "Log basic information about every request handled by the server."
    start = datetime.now()
    response = await call_next(request)
    handler_time = datetime.now() - start
    log.bind(
        method=request.method,
        status_code=response.status_code,
        handler_time=f"{handler_time.microseconds * 0.001}ms",
        path=request.url.path,
    ).info("Request received")
    return response


# Configure the static file paths last since otherwise it will take over all paths
@app.get("/", tags=["Default"])
def read_index() -> Response:
    """
    Return an index.html at the root path
    """

    return get_admin_index_as_response()


@app.get("/{catchall:path}", response_class=Response, tags=["Default"])
def read_other_paths(request: Request) -> Response:
    """
    Return related frontend files. Adapted from https://github.com/tiangolo/fastapi/issues/130
    """
    # check first if requested file exists (for frontend assets)
    path = request.path_params["catchall"]
    ui_file = get_path_to_admin_ui_file(path)
    if ui_file and ui_file.is_file():
        return FileResponse(ui_file)

    # raise 404 for anything that should be backend endpoint but we can't find it
    if path.startswith(API_PREFIX[1:]):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )

    # otherwise return the index
    return get_admin_index_as_response()


def start_webserver() -> None:
    "Run the webserver."
    server = Server(Config(app, host="0.0.0.0", port=8080, log_level=WARNING))
    server.run()
