"""
Contains the code that sets up the API.
"""

from datetime import datetime
from enum import Enum
from logging import WARNING
from pathlib import Path
from typing import Callable, Dict

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger as log
from uvicorn import Config, Server

import fidesctl
from fidesapi import view
from fidesapi.database import database
from fidesapi.routes import crud, visualize
from fidesapi.utils.logger import setup as setup_logging
from fidesctl.core.config import FidesctlConfig, get_config

WEBAPP_DIRECTORY = Path("src/fidesapi/build/static")
WEBAPP_INDEX = Path(WEBAPP_DIRECTORY / "index.html")

app = FastAPI(title="fidesctl")
CONFIG: FidesctlConfig = get_config()


def configure_routes() -> None:
    "Include all of the routers not defined in this module."
    routers = crud.routers + visualize.routers
    for router in routers:
        log.debug(f'Adding router to fidesctl: {" ".join(router.tags)}')
        app.include_router(router)

    app.include_router(view.router)


# Configure the routes here so we can generate the openapi json file
configure_routes()


async def configure_db(database_url: str) -> None:
    "Set up the db to be used by the app."
    database.create_db_if_not_exists(database_url)
    await database.init_db(database_url)


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
    "/health",
    response_model=Dict[str, str],
    responses={
        status.HTTP_200_OK: {
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "version": "1.0.0",
                    }
                }
            }
        }
    },
    tags=["Health"],
)
async def health() -> Dict:
    "Confirm that the API is running and healthy."
    return {
        "status": "healthy",
        "version": str(fidesctl.__version__),
    }


class DBActions(str, Enum):
    "The available path parameters for the `/admin/db/{action}` endpoint."
    init = "init"
    reset = "reset"


@app.post("/admin/db/{action}", tags=["Admin"])
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
@app.get("/")
def read_index() -> Response:
    """
    Return an index.html at the root path
    """
    path = WEBAPP_DIRECTORY / "index.html"
    return FileResponse(path)


@app.get("/{catchall:path}", response_class=FileResponse)
def read_other_paths(request: Request) -> FileResponse:
    """
    Return related frontend files. Adapted from https://github.com/tiangolo/fastapi/issues/130
    """
    # check first if requested file exists
    path = request.path_params["catchall"]
    file = WEBAPP_DIRECTORY / Path(path)
    if file.exists():
        return FileResponse(file)

    # otherwise return the index
    return FileResponse(WEBAPP_DIRECTORY / "index.html")


def start_webserver() -> None:
    "Run the webserver."
    server = Server(Config(app, host="0.0.0.0", port=8080, log_level=WARNING))
    server.run()
