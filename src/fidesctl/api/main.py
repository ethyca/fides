"""
Contains the code that sets up the API.
"""
from datetime import datetime
from enum import Enum
from logging import WARNING
from pathlib import Path
from typing import Callable, Dict

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger as log
from uvicorn import Config, Server

import fidesctl
from fidesctl.api import view
from fidesctl.api.database import database
from fidesctl.api.database.database import get_db_health
from fidesctl.api.routes import crud, datamap, generate, validate, visualize
from fidesctl.api.routes.util import API_PREFIX, WEBAPP_DIRECTORY, WEBAPP_INDEX
from fidesctl.api.utils.errors import get_full_exception_name
from fidesctl.api.utils.logger import setup as setup_logging
from fidesctl.core.config import FidesctlConfig, get_config

app = FastAPI(title="fidesctl")
CONFIG: FidesctlConfig = get_config()
ROUTERS = (
    crud.routers
    + visualize.routers
    + [view.router, generate.router, datamap.router, validate.router]
)


def configure_routes() -> None:
    "Include all of the routers not defined in this module."
    for router in ROUTERS:
        app.include_router(router)


# Configure the routes here so we can generate the openapi json file
configure_routes()


async def configure_db(database_url: str) -> None:
    "Set up the db to be used by the app."
    try:
        database.create_db_if_not_exists(database_url)
        await database.init_db(database_url)
    except Exception as error:  # pylint: disable=broad-except
        error_type = get_full_exception_name(error)
        log.error(f"Unable to configure database: {error_type}: {error}")


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


@app.get(
    f"{API_PREFIX}/health",
    response_model=Dict[str, str],
    responses={
        status.HTTP_200_OK: {
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "version": "1.0.0",
                        "database": "healthy",
                    }
                }
            }
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "status": "healthy",
                            "version": "1.0.0",
                            "database": "unhealthy",
                        }
                    }
                }
            }
        },
    },
    tags=["Health"],
)
async def health() -> Dict:
    "Confirm that the API is running and healthy."
    database_health = get_db_health(CONFIG.api.sync_database_url)
    response = {
        "status": "healthy",
        "version": str(fidesctl.__version__),
        "database": database_health,
    }

    for key in response:
        if response[key] == "unhealthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=response
            )

    return response


class DBActions(str, Enum):
    "The available path parameters for the `/admin/db/{action}` endpoint."
    init = "init"
    reset = "reset"


@app.post(API_PREFIX + "/admin/db/{action}", tags=["Admin"])
async def db_action(action: DBActions) -> Dict:
    """
    Initiate one of the enumerated DBActions.
    """
    action_text = "initialized"
    if action == DBActions.reset:
        database.reset_db(CONFIG.api.sync_database_url)
        action_text = DBActions.reset
    await configure_db(CONFIG.api.sync_database_url)
    return {"data": {"message": f"Fidesctl database {action_text}"}}


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
