"""
Contains the code that sets up the API.
"""

import logging
import time
from enum import Enum
from typing import Dict

from fastapi import FastAPI, Request
from loguru import logger as log
from uvicorn import Config, Server

from fidesapi import crud, database, db_session, visualize
from fidesapi.logger import setup as setup_logging
from fidesctl.core.config import get_config

app = FastAPI(title="fidesctl")


class DBActions(str, Enum):
    "The available path parameters for the `/admin/db/{action}` endpoint."
    init = "init"
    reset = "reset"


def configure_routes() -> None:
    "Include all of the routers not defined here."
    routers = crud.routers + visualize.routers
    for router in routers:
        log.debug(f'Adding router to fidesctl: {" ".join(router.tags)}')
        app.include_router(router)


def configure_db() -> None:
    "Set up the db to be used by the app."
    databse_url = config.api.database_url
    database.create_db_if_not_exists(databse_url)
    db_session.global_init(databse_url)
    database.init_db(databse_url)


@app.middleware("http")
async def log_request(request: Request, call_next):
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
        database.reset_db(config.api.database_url)
        action_text = DBActions.reset

    configure_db()
    return {"data": {"message": f"Fidesctl database {action_text}"}}


def start_webserver() -> None:
    "Run the webserver."
    server = Server(Config(app, host="0.0.0.0", port=8080, log_level=logging.WARNING))
    setup_logging(
        config.api.log_level,
        serialize=config.api.log_serialization,
        desination=config.api.log_destination,
    )
    server.run()


config = get_config()
setup_logging(
    config.api.log_level,
    serialize=config.api.log_serialization,
    desination=config.api.log_destination,
)
configure_routes()
configure_db()
