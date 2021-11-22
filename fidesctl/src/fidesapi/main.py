"""
Contains the code that sets up the API.
"""

from enum import Enum
from typing import Dict
import os

import uvicorn
from fastapi import FastAPI
from fidesapi import crud, database, db_session, visualize
from fidesctl.core.config import get_config

app = FastAPI(title="fidesctl")


class DBActions(str, Enum):
    "The available path parameters for the `/admin/db/{action}` endpoint."
    init = "init"
    reset = "reset"
    set_test_context = "set-test-context"
    set_std_context = "set-std-context"


def configure_routes() -> None:
    "Include all of the routers not defined here."
    for router in crud.routers:
        app.include_router(router)
    # add router for the category viz endpoints
    for router in visualize.routers:
        app.include_router(router)


def configure_db() -> None:
    "Set up the db to be used by the app."
    db_session.global_init(CONFIG.api.database_url)
    database.init_db(CONFIG.api.database_url)


@app.get("/health", tags=["Health"])
async def health() -> Dict:
    "Confirm that the API is running and healthy."
    ## TODO: this should also hit the database
    return {"data": {"message": "Fidesctl API service is healthy!"}}


@app.post("/admin/db/{action}", tags=["Admin"])
async def db_action(action: DBActions) -> Dict:
    """
    Initiate one of the enumerated DBActions.
    """
    global CONFIG  # pylint: disable=global-statement
    action_text = "initialized"
    if action == DBActions.reset:
        database.reset_db(CONFIG.api.database_url)
        action_text = DBActions.reset

    if action == DBActions.set_test_context:
        os.environ["FIDESCTL_CONFIG_OVERRIDE_PATH"] = "tests/test_config.toml"
        CONFIG = get_config()

    if action == DBActions.set_std_context:
        os.environ["FIDESCTL_CONFIG_OVERRIDE_PATH"] = ""
        CONFIG = get_config()

    configure_db()
    return {"data": {"message": f"Fidesctl database {action_text}"}}


def start_webserver() -> None:
    "Run the webserver."
    uvicorn.run(app, host="0.0.0.0", port=8080)


CONFIG = get_config()
configure_routes()
configure_db()
