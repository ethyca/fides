"""
Contains the code that sets up the API.
"""
import logging
from datetime import datetime, timezone
from logging import WARNING
from os import getenv
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
from fides.api.ctl.routes import admin, crud, datamap, generate, health, validate
from fides.api.ctl.routes.util import API_PREFIX
from fides.api.ctl.ui import (
    get_admin_index_as_response,
    get_local_file_map,
    get_package_file_map,
    get_path_to_admin_ui_file,
    match_route,
)
from fides.api.ctl.utils.errors import FidesError
from fides.api.ctl.utils.logger import setup as setup_logging
from fides.api.ops.analytics import (
    accessed_through_local_host,
    in_docker_container,
    send_analytics_event,
)
from fides.api.ops.api.deps import get_api_session
from fides.api.ops.api.deps import get_db as get_ctl_db
from fides.api.ops.api.v1.api import api_router
from fides.api.ops.api.v1.exception_handlers import ExceptionHandlers
from fides.api.ops.common_exceptions import (
    FunctionalityNotConfigured,
    RedisConnectionError,
)
from fides.api.ops.schemas.analytics import Event, ExtraData
from fides.api.ops.service.connectors.saas.connector_registry_service import (
    load_registry,
    registry_file,
    update_saas_configs,
)
from fides.api.ops.tasks.scheduled.scheduler import scheduler
from fides.api.ops.util.cache import get_cache
from fides.api.ops.util.logger import Pii, get_fides_log_record_factory
from fides.api.ops.util.oauth_util import verify_oauth_client
from fides.ctl.core.config import FidesConfig
from fides.ctl.core.config import get_config as get_ctl_config

CONFIG: FidesConfig = get_ctl_config()

logging.basicConfig(level=CONFIG.logging.level)
logging.setLogRecordFactory(get_fides_log_record_factory())
logger = logging.getLogger(__name__)

app = FastAPI(title="fides")
ROUTERS = crud.routers + [  # type: ignore[attr-defined]
    admin.router,
    datamap.router,
    generate.router,
    health.router,
    validate.router,
    view.router,
]


@app.middleware("http")
async def dispatch_log_request(request: Request, call_next: Callable) -> Response:
    """
    HTTP Middleware that logs analytics events for each call to Fides endpoints.
    :param request: Request to Fides api
    :param call_next: Callable api endpoint
    :return: Response
    """

    # Only log analytics events for requests that are for API endpoints (i.e. /api/...)
    path = request.url.path
    if (not path.startswith(API_PREFIX)) or (path.endswith("/health")):
        return await call_next(request)

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
        await prepare_and_log_request(
            endpoint, request.url.hostname, 500, now, fides_source, e.__class__.__name__
        )
        raise


async def prepare_and_log_request(
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
    if CONFIG.user.analytics_opt_out:
        return
    await send_analytics_event(
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

if CONFIG.security.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in CONFIG.security.cors_origins],
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
    log.warning(
        f"Startup configuration: reloading = {CONFIG.hot_reloading}, dev_mode = {CONFIG.dev_mode}",
    )
    log_pii = getenv("FIDES__LOG_PII", "").lower() == "true"
    log.warning(
        f"Startup configuration: pii logging = {log_pii}",
    )

    if logger.getEffectiveLevel() == logging.DEBUG:
        log.warning(
            "WARNING: log level is DEBUG, so sensitive or personal data may be logged. "
            "Set FIDES__LOGGING__LEVEL to INFO or higher in production."
        )
        CONFIG.log_all_config_values()

    if not CONFIG.database.sync_database_uri:
        raise FidesError("No database uri provided")

    await configure_db(CONFIG.database.sync_database_uri)

    log.info("Validating SaaS connector templates...")
    registry = load_registry(registry_file)
    try:
        db = get_api_session()
        update_saas_configs(registry, db)
    finally:
        db.close()

    log.info("Running Redis connection test...")

    try:
        get_cache()
    except (RedisConnectionError, ResponseError) as e:
        log.error("Connection to cache failed: %s", Pii(str(e)))
        return

    if not scheduler.running:
        scheduler.start()

    log.debug("Sending startup analytics events...")
    await send_analytics_event(
        AnalyticsEvent(
            docker=in_docker_container(),
            event=Event.server_start.value,
            event_created_at=datetime.now(tz=timezone.utc),
        )
    )

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

    # First search in the local (dev) build for for a matching route.
    ui_file = match_route(get_local_file_map(), path)

    # Next, search for a matching route in the packaged files.
    if not ui_file:
        ui_file = match_route(get_package_file_map(), path)

    # Finally, try to find the exact path as a packaged file.
    if not ui_file:
        ui_file = get_path_to_admin_ui_file(path)

    # If any of those worked, serve the file.
    if ui_file and ui_file.is_file():
        log.debug(
            f"catchall request path '{path}' matched static admin UI file: {ui_file}"
        )
        return FileResponse(ui_file)

    # raise 404 for anything that should be backend endpoint but we can't find it
    if path.startswith(API_PREFIX[1:]):
        log.debug(
            f"catchall request path '{path}' matched an invalid API route, return 404"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )

    # otherwise return the index
    log.debug(
        f"catchall request path '{path}' did not match any admin UI routes, return generic admin UI index"
    )
    return get_admin_index_as_response()


def start_webserver() -> None:
    "Run the webserver."
    server = Server(Config(app, host="0.0.0.0", port=8080, log_level=WARNING))
    server.run()
