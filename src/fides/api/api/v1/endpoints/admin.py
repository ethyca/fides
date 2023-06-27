from enum import Enum
from typing import Dict

from fastapi import Security

from fides.api.api.v1.endpoints import API_PREFIX
from fides.api.db.database import configure_db, reset_db
from fides.api.oauth.utils import verify_oauth_client_prod
from fides.api.util import errors
from fides.api.util.api_router import APIRouter
from fides.common.api import scope_registry
from fides.config import CONFIG

ADMIN_ROUTER = APIRouter(prefix=API_PREFIX, tags=["Admin"])


class DBActions(str, Enum):
    "The available path parameters for the `/admin/db/{action}` endpoint."
    upgrade = "upgrade"
    reset = "reset"


@ADMIN_ROUTER.post(
    "/admin/db/{action}",
    tags=["Admin"],
    dependencies=[
        Security(verify_oauth_client_prod, scopes=[scope_registry.DATABASE_RESET])
    ],
)
async def db_action(action: DBActions) -> Dict:
    """
    Initiate one of the enumerated DBActions.
    """
    action_text = "upgrade"

    if action == DBActions.reset:
        if not CONFIG.dev_mode:
            raise errors.FunctionalityNotConfigured(
                "unable to reset fides database outside of dev_mode."
            )

        reset_db(CONFIG.database.sync_database_uri)
        action_text = "reset"

    await configure_db(CONFIG.database.sync_database_uri)

    return {
        "data": {
            "message": f"Fides database action performed successfully: {action_text}"
        }
    }
