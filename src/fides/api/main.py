"""
Contains the code that sets up the API.
"""
from datetime import datetime, timezone
from logging import DEBUG, WARNING
from typing import Callable, List, Optional, Pattern, Union

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import FileResponse
from fideslog.sdk.python.event import AnalyticsEvent
from loguru import logger
from redis.exceptions import RedisError, ResponseError
from slowapi.errors import RateLimitExceeded  # type: ignore
from slowapi.extension import Limiter, _rate_limit_exceeded_handler  # type: ignore
from slowapi.middleware import SlowAPIMiddleware  # type: ignore
from slowapi.util import get_remote_address  # type: ignore
from starlette.background import BackgroundTask
from starlette.middleware.cors import CORSMiddleware
from uvicorn import Config, Server

import fides
from fides.api.ctl import view
from fides.api.ctl.database.database import configure_db
from fides.api.ctl.database.seed import create_or_update_parent_user
from fides.api.ctl.routes import (
    admin,
    crud,
    datamap,
    generate,
    health,
    system,
    validate,
)
from fides.api.ctl.routes.util import API_PREFIX
from fides.api.ctl.ui import (
    get_admin_index_as_response,
    get_path_to_admin_ui_file,
    get_ui_file_map,
    match_route,
    path_is_in_ui_directory,
)
from fides.api.ctl.utils.errors import FidesError
from fides.api.ctl.utils.logger import setup as setup_logging
from fides.api.ops.analytics import (
    accessed_through_local_host,
    in_docker_container,
    send_analytics_event,
)
from fides.api.ops.api.deps import get_api_session
from fides.api.ops.api.v1.api import api_router
from fides.api.ops.api.v1.exception_handlers import ExceptionHandlers
from fides.api.ops.common_exceptions import (
    FunctionalityNotConfigured,
    RedisConnectionError,
)
from fides.api.ops.models.application_config import ApplicationConfig
from fides.api.ops.schemas.analytics import Event, ExtraData
from fides.api.ops.service.connectors.saas.connector_registry_service import (
    load_registry,
    registry_file,
    update_saas_configs,
)

# pylint: disable=wildcard-import, unused-wildcard-import
from fides.api.ops.service.privacy_request.email_batch_service import (
    initiate_scheduled_batch_email_send,
)
from fides.api.ops.service.saas_request.override_implementations import *
from fides.api.ops.tasks.scheduled.scheduler import scheduler
from fides.api.ops.util.cache import get_cache
from fides.api.ops.util.logger import _log_exception
from fides.api.ops.util.oauth_util import get_root_client, verify_oauth_client_cli
from fides.api.ops.util.system_manager_oauth_util import (
    get_system_fides_key,
    get_system_schema,
    verify_oauth_client_for_system_from_fides_key_cli,
    verify_oauth_client_for_system_from_request_body_cli,
)
from fides.core.config import CONFIG
from fides.core.config.helpers import check_required_webserver_config_values
from fides.lib.oauth.api.routes.user_endpoints import router as user_router

VERSION = fides.__version__

ROUTERS = crud.routers + [  # type: ignore[attr-defined]
    admin.router,
    datamap.router,
    generate.router,
    health.router,
    validate.router,
    view.router,
    system.system_connections_router,
    system.system_router,
]


def create_fides_app(
    cors_origins: Union[str, List[str]] = CONFIG.security.cors_origins,
    cors_origin_regex: Optional[Pattern] = CONFIG.security.cors_origin_regex,
    routers: List = ROUTERS,
    app_version: str = VERSION,
    api_prefix: str = API_PREFIX,
    request_rate_limit: str = CONFIG.security.request_rate_limit,
    rate_limit_prefix: str = CONFIG.security.rate_limit_prefix,
    security_env: str = CONFIG.security.env,
) -> FastAPI:
    """Return a properly configured application."""

    fastapi_app = FastAPI(title="fides", version=app_version)
    fastapi_app.state.limiter = Limiter(
        default_limits=[request_rate_limit],
        headers_enabled=True,
        key_prefix=rate_limit_prefix,
        key_func=get_remote_address,
        retry_after="http-date",
    )
    fastapi_app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    for handler in ExceptionHandlers.get_handlers():
        fastapi_app.add_exception_handler(FunctionalityNotConfigured, handler)
    fastapi_app.add_middleware(SlowAPIMiddleware)

    if cors_origins or cors_origin_regex:
        fastapi_app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in cors_origins],
            allow_origin_regex=cors_origin_regex,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    for router in routers:
        fastapi_app.include_router(router)
    fastapi_app.include_router(user_router, tags=["Users"], prefix=f"{api_prefix}")
    fastapi_app.include_router(api_router)

    if security_env == "dev":
        # This removes auth requirements for CLI-related endpoints
        # and is the default
        fastapi_app.dependency_overrides[verify_oauth_client_cli] = get_root_client
        fastapi_app.dependency_overrides[
            verify_oauth_client_for_system_from_request_body_cli
        ] = get_system_schema
        fastapi_app.dependency_overrides[
            verify_oauth_client_for_system_from_fides_key_cli
        ] = get_system_fides_key
    elif security_env == "prod":
        # This is the most secure, so all security deps are maintained
        pass

    return fastapi_app


app = create_fides_app()


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
        _log_exception(e, CONFIG.dev_mode)
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


# Configure the routes here so we can generate the openapi json file


@app.on_event("startup")
async def setup_server() -> None:
    "Run all of the required setup steps for the webserver."
    logger.info(f"Starting Fides - v{VERSION}")
    logger.info(
        "Startup configuration: reloading = {}, dev_mode = {}",
        CONFIG.hot_reloading,
        CONFIG.dev_mode,
    )
    logger.info("Startup configuration: pii logging = {}", CONFIG.logging.log_pii)

    if CONFIG.logging.level == DEBUG:
        logger.warning(
            "WARNING: log level is DEBUG, so sensitive or personal data may be logged. "
            "Set FIDES__LOGGING__LEVEL to INFO or higher in production."
        )
        CONFIG.log_all_config_values()

    if not CONFIG.database.sync_database_uri:
        raise FidesError("No database uri provided")

    await configure_db(CONFIG.database.sync_database_uri)

    try:
        create_or_update_parent_user()
    except Exception as e:
        logger.error("Error creating parent user: {}", str(e))
        raise FidesError(f"Error creating parent user: {str(e)}")

    logger.info("Loading config settings into database...")
    try:
        db = get_api_session()
        ApplicationConfig.update_config_set(db, CONFIG)
    except Exception as e:
        logger.error("Error occurred writing config settings to database: {}", str(e))
        raise FidesError(
            f"Error occurred writing config settings to database: {str(e)}"
        )
    finally:
        db.close()

    logger.info("Validating SaaS connector templates...")
    try:
        registry = load_registry(registry_file)
        db = get_api_session()
        update_saas_configs(registry, db)
        logger.info("Finished loading saas templates")
    except Exception as e:
        logger.error(
            "Error occurred during SaaS connector template validation: {}",
            str(e),
        )
        return
    finally:
        db.close()

    logger.info("Running Cache connection test...")

    try:
        get_cache()
    except (RedisConnectionError, RedisError, ResponseError) as e:
        logger.error("Connection to cache failed: {}", str(e))
        return
    else:
        logger.debug("Connection to cache succeeded")

    if not scheduler.running:
        scheduler.start()

    initiate_scheduled_batch_email_send()

    logger.debug("Sending startup analytics events...")
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

    logger.bind(api_config=CONFIG.logging.json()).debug("Configuration options in use")


@app.middleware("http")
async def log_request(request: Request, call_next: Callable) -> Response:
    """Log basic information about every request handled by the server."""
    start = datetime.now()
    response = await call_next(request)
    handler_time = datetime.now() - start
    logger.bind(
        method=request.method,
        status_code=response.status_code,
        handler_time=f"{round(handler_time.microseconds * 0.001,3)}ms",
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

    # search for matching route in package (i.e. /dataset)
    ui_file = match_route(get_ui_file_map(), path)

    # if not, check if the requested file is an asset (i.e. /_next/static/...)
    if not ui_file:
        ui_file = get_path_to_admin_ui_file(path)

    # Serve up the file as long as it is within the UI directory
    if ui_file and ui_file.is_file():
        if not path_is_in_ui_directory(ui_file):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
            )
        logger.debug(
            "catchall request path '{}' matched static admin UI file: {}",
            path,
            ui_file,
        )
        return FileResponse(ui_file)

    # raise 404 for anything that should be backend endpoint but we can't find it
    if path.startswith(API_PREFIX[1:]):
        logger.debug(
            "catchall request path '{}' matched an invalid API route, return 404",
            path,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )

    # otherwise return the index
    logger.debug(
        "catchall request path '{}' did not match any admin UI routes, return generic admin UI index",
        path,
    )
    return get_admin_index_as_response()


def start_webserver(port: int = 8080) -> None:
    """Run the webserver."""
    check_required_webserver_config_values()
    server = Server(Config(app, host="0.0.0.0", port=port, log_level=WARNING))

    logger.info(
        "Starting webserver - Host: {}, Port: {}, Log Level: {}",
        server.config.host,
        server.config.port,
        server.config.log_level,
    )
    server.run()
