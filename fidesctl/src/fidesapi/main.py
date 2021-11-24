"""
Contains the code that sets up the API.
"""

from enum import Enum
from typing import Dict

import uvicorn
from fastapi import FastAPI
from fidesapi import crud, database, db_session, visualize
from fidesctl.core.config import get_config

app = FastAPI(title="fidesctl")


class DBActions(str, Enum):
    "The available path parameters for the `/admin/db/{action}` endpoint."
    init = "init"
    reset = "reset"


def configure_routes() -> None:
    "Include all of the routers not defined here."
    for router in crud.routers:
        app.include_router(router)
    # add router for the category viz endpoints
    for router in visualize.routers:
        app.include_router(router)


def configure_db() -> None:
    "Set up the db to be used by the app."
    databse_url = config.api.database_url
    database.create_db_if_not_exists(databse_url)
    db_session.global_init(databse_url)
    database.init_db(databse_url)


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
    uvicorn.run(app, host="0.0.0.0", port=8080)


config = get_config()
configure_routes()
configure_db()
