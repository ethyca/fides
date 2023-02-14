from enum import Enum
from typing import Dict

from fastapi import Security

from fides.api.ctl.database import database
from fides.api.ctl.routes.util import API_PREFIX
from fides.api.ctl.utils import errors
from fides.api.ctl.utils.api_router import APIRouter
from fides.api.ops.api.v1 import scope_registry
from fides.api.ops.util.oauth_util import verify_oauth_client_cli
from fides.core.config import FidesConfig, get_config

CONFIG: FidesConfig = get_config()
router = APIRouter(prefix=API_PREFIX, tags=["Admin"])


class DBActions(str, Enum):
    "The available path parameters for the `/admin/db/{action}` endpoint."
    init = "init"
    reset = "reset"


@router.post(
    "/admin/db/{action}",
    tags=["Admin"],
    dependencies=[
        Security(verify_oauth_client_cli, scopes=[scope_registry.DATABASE_RESET])
    ],
)
async def db_action(action: DBActions) -> Dict:
    """
    Initiate one of the enumerated DBActions.
    """

    action_text = "initialized"
    if action == DBActions.reset:
        if not CONFIG.dev_mode:
            raise errors.FunctionalityNotConfigured(
                "unable to reset fides database outside of dev_mode."
            )

        database.reset_db(CONFIG.database.sync_database_uri)
        action_text = DBActions.reset
    await database.configure_db(CONFIG.database.sync_database_uri)
    return {"data": {"message": f"fides database {action_text}"}}
