"""
Contains the code that sets up the API.
"""

import logging
import time
from enum import Enum
from typing import Callable, Dict

from fastapi import FastAPI, Request, Response
from loguru import logger as log
from uvicorn import Config, Server

from fidesapi import crud, database, db_session, view, visualize
from fidesapi.logger import setup as setup_logging
from fidesctl.core.config import get_config, FidesctlConfig

app = FastAPI(title="fidesctl")
CONFIG: FidesctlConfig = get_config()

class DBActions(str, Enum):
    "The available path parameters for the `/admin/db/{action}` endpoint."
    init = "init"
    reset = "reset"


def configure_routes() -> None:
    "Include all of the routers not defined in this module."
    routers = crud.routers + visualize.routers
    for router in routers:
        log.debug(f'Adding router to fidesctl: {" ".join(router.tags)}')
        app.include_router(router)

    app.include_router(view.router)


def configure_db(database_url: str) -> None:
    "Set up the db to be used by the app."
    database.create_db_if_not_exists(database_url)
    db_session.global_init(database_url)
    database.init_db(database_url)


@app.middleware("http")
async def log_request(request: Request, call_next: Callable) -> Response:
    "Log basic information about every request handled by the server."
    start = time.time()
    response = await call_next(request)
    handle_time = time.time() - start
    log.bind(
        method=request.method,
        status_code=response.status_code,
        handler_time=f"{handle_time}s",
        path=request.url.path,
    ).info("Request received")
    return response


@app.get("/health", tags=["Health"])
async def health() -> Dict:
    "Confirm that the API is running and healthy."
    return {"data": {"message": "Fidesctl API service is healthy!"}}


@app.post("/admin/db/{action}", tags=["Admin"])
async def db_action(action: DBActions) -> Dict:
    """
    Initiate one of the enumerated DBActions.
    """
    action_text = "initialized"
    if action == DBActions.reset:
        database.reset_db(CONFIG.api.database_url)
        action_text = DBActions.reset
    configure_db(CONFIG.api.database_url)
    return {"data": {"message": f"Fidesctl database {action_text}"}}


def start_webserver() -> None:
    "Run the webserver."
    setup_server()
    server = Server(Config(app, host="0.0.0.0", port=8080, log_level=logging.WARNING))
    server.run()

def setup_server() -> None:
    setup_logging(
        CONFIG.api.log_level,
        serialize=CONFIG.api.log_serialization,
        desination=CONFIG.api.log_destination,
    )
    configure_routes()
    configure_db(CONFIG.api.database_url)

setup_server()
