"""
Contains the code that sets up the API.
"""
from datetime import datetime, timezone
from enum import Enum
from logging import WARNING
from typing import Callable, Dict
from importlib.metadata import version
import platform

from fastapi import FastAPI, Request, Response
from loguru import logger as log
from uvicorn import Config, Server

from fidesapi import view
from fidesapi.database import database
from fidesapi.routes import crud, visualize
from fidesapi.utils.logger import setup as setup_logging
from fidesctl.core.config import FidesctlConfig, get_config
from fideslog.sdk.python import event, client


PRODUCT_NAME = "fidesctl"
app = FastAPI(title=PRODUCT_NAME)
CONFIG: FidesctlConfig = get_config()

fideslog_client = client.AnalyticsClient(
    client_id=CONFIG.api.analytics_id,
    os=platform.system(),
    product_name=PRODUCT_NAME,
    production_version=version(PRODUCT_NAME),
)


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
async def setup_server() -> None:
    "Run all of the required setup steps for the webserver."
    setup_logging(
        CONFIG.api.log_level,
        serialize=CONFIG.api.log_serialization,
        desination=CONFIG.api.log_destination,
    )
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


@app.middleware("http")
async def send_anonymous_event(request: Request, call_next: Callable) -> Response:
    "If opted in, send anonymous event data from the fidesctl API"
    response = await call_next(request)

    if not CONFIG.user.analytics_opt_out:
        command = request.url.path
        status_code = response.status_code
        fideslog_event = event.AnalyticsEvent(
            event="API",
            event_created_at=datetime.now(timezone.utc),
            command=request.method,
            endpoint=command,
            status_code=status_code,
        )

        await fideslog_client.send(event=fideslog_event)
    return response


@app.get("/health", tags=["Health"])
async def health() -> Dict:
    "Confirm that the API is running and healthy."
    return {"data": {"message": "Fidesctl API service is healthy!"}}


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


def start_webserver() -> None:
    "Run the webserver."
    server = Server(Config(app, host="0.0.0.0", port=8888, log_level=WARNING))
    server.run()
