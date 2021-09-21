from fastapi import FastAPI

from fidesapi import crud
from fidesctl.core.config import get_config

from fidesapi import db_session

app = FastAPI()


def configure_routes():
    for router in crud.routers:
        app.include_router(router)


def configure_db(database_url: str):
    db_session.global_init(database_url)


@app.get("/", tags=["Healthcheck"])
async def healthcheck():
    return {"data": {"message": "Fides service is healthy!"}}


config = get_config()
configure_routes()
configure_db(config.api.database_url)
