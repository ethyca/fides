"""
Contains the code that sets up the API.
"""
import logging
import subprocess
from datetime import datetime, timezone
from logging import WARNING
from typing import Callable, Optional

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import FileResponse
from fideslib.oauth.api.deps import get_config as lib_get_config
from fideslib.oauth.api.deps import get_db as lib_get_db
from fideslib.oauth.api.deps import verify_oauth_client as lib_verify_oauth_client
from fideslib.oauth.api.routes.user_endpoints import router as user_router
from fideslog.sdk.python.event import AnalyticsEvent
from loguru import logger as log
from redis.exceptions import ResponseError
from starlette.background import BackgroundTask
from starlette.middleware.cors import CORSMiddleware
from uvicorn import Config, Server

from fides.api.ctl import view
from fides.api.ctl.database.database import configure_db
from fides.api.ctl.deps import get_db as get_ctl_db
from fides.api.ops.util.oauth_util import verify_oauth_client
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
from fides.api.ops.analytics import (
    accessed_through_local_host,
    in_docker_container,
    send_analytics_event,
)
from fides.api.ops.api.v1.api import api_router
from fides.api.ops.api.v1.exception_handlers import ExceptionHandlers
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
from fides.api.ops.util.cache import get_cache
from fides.api.ops.util.logger import Pii, get_fides_log_record_factory
from fides.ctl.core.config import FidesctlConfig
from fides.ctl.core.config import get_config as get_ctl_config

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
    if ops_config.root_user.analytics_opt_out:
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
app.dependency_overrides[lib_get_config] = get_ctl_config
app.dependency_overrides[lib_get_db] = get_ctl_db
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

    await configure_db(CONFIG.database.sync_database_uri)

    logger.info("Validating SaaS connector templates...")
    load_registry(registry_file)

    if ops_config.redis.enabled:
        logger.info("Running Redis connection test...")
        try:
            get_cache()
        except (RedisConnectionError, ResponseError) as e:
            logger.error("Connection to cache failed: %s", Pii(str(e)))
            return

    if not scheduler.running:
        scheduler.start()

    # TODO: Fix this, this line is preventing the webserver from starting properly
    # if ops_config.database.enabled:
    #     logger.info("Starting scheduled request intake...")
    #     initiate_scheduled_request_intake()

    send_analytics_event(
        AnalyticsEvent(
            docker=in_docker_container(),
            event=Event.server_start.value,
            event_created_at=datetime.now(tz=timezone.utc),
        )
    )

    if not ops_config.execution.worker_enabled:
        logger.info("Starting worker...")
        subprocess.Popen(["fides", "worker"])  # pylint: disable=consider-using-with

    setup_logging(
        CONFIG.logging.level,
        serialize=CONFIG.logging.serialization,
        desination=CONFIG.logging.destination,
    )

    log.bind(api_config=CONFIG.logging.json()).debug("Configuration options in use")


@app.middleware("http")
async def log_request(request: Request, call_next: Callable) -> Response:
    """Log basic information about every request handled by the server."""
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
