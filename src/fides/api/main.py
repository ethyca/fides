"""
Contains the code that sets up the API.
"""
import os
import sys
from datetime import datetime, timezone
from logging import WARNING
from time import perf_counter
from typing import Callable, Optional
from urllib.parse import unquote

from fastapi import HTTPException, Request, Response, status
from fastapi.responses import FileResponse, HTMLResponse
from fideslog.sdk.python.event import AnalyticsEvent
from loguru import logger
from pyinstrument import Profiler
from starlette.background import BackgroundTask
from uvicorn import Config, Server

import fides
from fides.api.app_setup import (
    check_redis,
    create_fides_app,
    log_startup,
    run_database_startup,
)
from fides.api.common_exceptions import MalisciousUrlException
from fides.api.middleware import handle_audit_log_resource
from fides.api.schemas.analytics import Event, ExtraData

# pylint: disable=wildcard-import, unused-wildcard-import
from fides.api.service.privacy_request.email_batch_service import (
    initiate_scheduled_batch_email_send,
)
from fides.api.tasks.scheduled.scheduler import async_scheduler, scheduler
from fides.api.ui import (
    get_admin_index_as_response,
    get_path_to_admin_ui_file,
    get_ui_file_map,
    match_route,
    path_is_in_ui_directory,
)
from fides.api.util.endpoint_utils import API_PREFIX
from fides.api.util.logger import _log_exception
from fides.cli.utils import FIDES_ASCII_ART
from fides.config import CONFIG, check_required_webserver_config_values

IGNORED_AUDIT_LOG_RESOURCE_PATHS = {"/api/v1/login"}

VERSION = fides.__version__

app = create_fides_app()

if CONFIG.dev_mode:

    @app.middleware("http")
    async def profile_request(request: Request, call_next: Callable) -> Response:
        profiling = request.headers.get("profile-request", False)
        if profiling:
            profiler = Profiler(interval=0.001, async_mode="enabled")
            profiler.start()
            await call_next(request)
            profiler.stop()
            logger.debug("Request Profiled!")
            return HTMLResponse(profiler.output_text(timeline=True))

        return await call_next(request)


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
    # Avoid circular imports
    from fides.api.analytics import (
        accessed_through_local_host,
        in_docker_container,
        send_analytics_event,
    )

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


@app.middleware("http")
async def log_request(request: Request, call_next: Callable) -> Response:
    """Log basic information about every request handled by the server."""
    start = datetime.now()

    # If the request fails, we still want to log it
    try:
        response = await call_next(request)
    except:  # pylint: disable=bare-except
        response = Response(status_code=500)

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


def sanitise_url_path(path: str) -> str:
    """Returns a URL path that does not contain any ../ or //"""
    path = unquote(path)
    path = os.path.normpath(path)
    for token in path.split("/"):
        if ".." in token:
            logger.warning(
                f"Potentially dangerous use of URL hierarchy in path: {path}"
            )
            raise MalisciousUrlException()
    return path


@app.get("/{catchall:path}", response_class=Response, tags=["Default"])
def read_other_paths(request: Request) -> Response:
    """
    Return related frontend files. Adapted from https://github.com/tiangolo/fastapi/issues/130
    """
    # check first if requested file exists (for frontend assets)
    path = request.path_params["catchall"]
    logger.debug(f"Catch all path detected: {path}")
    try:
        path = sanitise_url_path(path)
    except MalisciousUrlException:
        # if a maliscious URL is detected, route the user to the index
        return get_admin_index_as_response()

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


@app.on_event("startup")
async def setup_server() -> None:
    """Run all of the required setup steps for the webserver.

    **NOTE**: The order of operations here _is_ deliberate
    and must be maintained.
    """
    start_time = perf_counter()
    logger.info("Starting server setup...")
    if not CONFIG.dev_mode:
        sys.tracebacklimit = 0

    log_startup()

    await run_database_startup(app)

    check_redis()

    if not scheduler.running:
        scheduler.start()
    if not async_scheduler.running:
        async_scheduler.start()

    initiate_scheduled_batch_email_send()

    logger.debug("Sending startup analytics events...")
    # Avoid circular imports
    from fides.api.analytics import in_docker_container, send_analytics_event

    await send_analytics_event(
        AnalyticsEvent(
            docker=in_docker_container(),
            event=Event.server_start.value,
            event_created_at=datetime.now(tz=timezone.utc),
        )
    )

    # It's just a random bunch of strings when serialized
    if not CONFIG.logging.serialization:
        logger.info(FIDES_ASCII_ART)

    logger.info("Fides startup complete! v{}", VERSION)
    startup_time = round(perf_counter() - start_time, 3)
    logger.info("Server setup completed in {} seconds", startup_time)


def start_webserver(port: int = 8080) -> None:
    """Run the webserver."""
    check_required_webserver_config_values(config=CONFIG)
    server = Server(Config(app, host="0.0.0.0", port=port, log_level=WARNING))

    logger.info(
        "Starting webserver - Host: {}, Port: {}, Log Level: {}",
        server.config.host,
        server.config.port,
        server.config.log_level,
    )
    server.run()


@app.middleware("http")
async def action_to_audit_log(
    request: Request,
    call_next: Callable,
) -> Response:
    """Log basic information about every non-GET request handled by the server."""

    if (
        request.method != "GET"
        and request.scope["path"] not in IGNORED_AUDIT_LOG_RESOURCE_PATHS
        and CONFIG.security.enable_audit_log_resource_middleware
    ):
        try:
            await handle_audit_log_resource(request)
        except Exception as exc:
            logger.debug(exc)
    return await call_next(request)
