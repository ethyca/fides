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

from fidesctl.api.ctl import view
from fidesctl.api.ctl.database.database import configure_db
from fidesctl.api.ctl.deps import get_db, verify_oauth_client
from fidesctl.api.ctl.routes import (
    admin,
    crud,
    datamap,
    generate,
    health,
    user,
    validate,
    visualize,
)
from fidesctl.api.ctl.routes.util import API_PREFIX
from fidesctl.api.ctl.ui import (
    get_admin_index_as_response,
    get_local_file_map,
    get_package_file_map,
    get_path_to_admin_ui_file,
    match_route,
)
from fidesctl.api.ctl.utils.logger import setup as setup_logging
from fidesctl.ctl.core.config import FidesctlConfig, get_config

app = FastAPI(title="fidesctl")
CONFIG: FidesctlConfig = get_config()
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


def configure_routes() -> None:
    "Include all of the routers not defined in this module."
    for router in ROUTERS:
        app.include_router(router)

    app.include_router(user_router, tags=["Users"], prefix=f"{API_PREFIX}")


# Configure the routes here so we can generate the openapi json file
configure_routes()
app.dependency_overrides[lib_get_config] = get_config
app.dependency_overrides[lib_get_db] = get_db
app.dependency_overrides[lib_verify_oauth_client] = verify_oauth_client


@app.on_event("startup")
async def setup_server() -> None:
    "Run all of the required setup steps for the webserver."
    setup_logging(
        CONFIG.logging.level,
        serialize=CONFIG.logging.serialization,
        desination=CONFIG.logging.destination,
    )

    log.bind(api_config=CONFIG.logging.json()).debug("Configuration options in use")

    docs_link = "https://ethyca.github.io/fides/"
    log.warning(
        f"WARNING: 'Fidesctl' has been deprecated and replaced by a more robust 'Fides' tool, which includes existing 'fidesctl' functionality. Run `pip install ethyca-fides` to get the latest version of Fides and visit '{docs_link}' for up-to-date documentation.\n"
    )
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
