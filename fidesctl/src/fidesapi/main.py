"""
Contains the code that sets up the API.
"""

from typing import Dict

import uvicorn
from fastapi import FastAPI

from fidesapi import crud, db_session, visualize
from fidesctl.core.config import get_config

app = FastAPI(title="fidesctl")


def configure_routes() -> None:
    "Include all of the routers not defined here."
    for router in crud.routers:
        app.include_router(router)
    # add router for the category viz endpoints
    for router in visualize.routers:
        app.include_router(router)


def configure_db(database_url: str) -> None:
    "Set up the db to be used by the app."
    db_session.global_init(database_url)


@app.get("/health", tags=["Health"])
async def health() -> Dict:
    "Confirm that the API is running and healthy."
    return {"data": {"message": "Fides service is healthy!"}}


def start_webserver() -> None:
    "Run the webserver."
    uvicorn.run(app, host="0.0.0.0", port=8080)


config = get_config()
configure_routes()
configure_db(config.api.database_url)
