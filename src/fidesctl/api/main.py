"""
Contains the code that sets up the API.
"""
from datetime import datetime
from logging import WARNING
from pathlib import Path
from typing import Callable

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fideslib.oauth.api.deps import get_db as lib_get_db
from fideslib.oauth.api.deps import verify_oauth_client as lib_verify_oauth_client
from fideslib.oauth.api.routes.user_endpoints import router as user_router
from loguru import logger as log
from uvicorn import Config, Server

from fidesctl.api import view
from fidesctl.api.database.database import configure_db
from fidesctl.api.routes import (
    admin,
    crud,
    datamap,
    generate,
    health,
    validate,
    visualize,
)
from fidesctl.api.routes.util import API_PREFIX, WEBAPP_DIRECTORY, WEBAPP_INDEX
from fidesctl.api.utils.logger import setup as setup_logging
from fidesctl.core.config import FidesctlConfig, get_config

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
        validate.router,
        view.router,
        user_router,
    ]
)


def configure_routes() -> None:
    "Include all of the routers not defined in this module."
    for router in ROUTERS:
        app.include_router(router)


# Configure the routes here so we can generate the openapi json file
configure_routes()
app.dependency_overrides[lib_get_db] = get_db
app.dependency_overrides[lib_verify_oauth_client] = verify_oauth_client


@app.on_event("startup")
async def create_webapp_dir_if_not_exists() -> None:
    """Creates the webapp directory if it doesn't exist."""

    if not WEBAPP_INDEX.is_file():
        WEBAPP_DIRECTORY.mkdir(parents=True, exist_ok=True)
        with open(WEBAPP_DIRECTORY / "index.html", "w") as index_file:
            index_file.write("<h1>Privacy is a Human Right!</h1>")

    app.mount("/static", StaticFiles(directory=WEBAPP_DIRECTORY), name="static")


@app.on_event("startup")
async def setup_server() -> None:
    "Run all of the required setup steps for the webserver."
    setup_logging(
        CONFIG.api.log_level,
        serialize=CONFIG.api.log_serialization,
        desination=CONFIG.api.log_destination,
    )

    log.bind(api_config=CONFIG.api.json()).debug("Configuration options in use")
    await configure_db(CONFIG.api.sync_database_url)


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
    return FileResponse(WEBAPP_INDEX)


@app.get("/{catchall:path}", response_class=FileResponse, tags=["Default"])
def read_other_paths(request: Request) -> FileResponse:
    """
    Return related frontend files. Adapted from https://github.com/tiangolo/fastapi/issues/130
    """
    # check first if requested file exists (for frontend assets)
    path = request.path_params["catchall"]
    file = WEBAPP_DIRECTORY / Path(path)
    if file.exists():
        return FileResponse(file)

    # raise 404 for anything that should be backend endpoint but we can't find it
    if path.startswith(API_PREFIX[1:]):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )

    # otherwise return the index
    return FileResponse(WEBAPP_INDEX)


def start_webserver() -> None:
    "Run the webserver."
    server = Server(Config(app, host="0.0.0.0", port=8080, log_level=WARNING))
    server.run()
