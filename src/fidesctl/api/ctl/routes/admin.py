from enum import Enum
from typing import Dict

from fidesctl.api.ctl.database import database
from fidesctl.api.ctl.routes.util import API_PREFIX
from fidesctl.api.ctl.utils.api_router import APIRouter
from fidesctl.ctl.core.config import FidesctlConfig, get_config

CONFIG: FidesctlConfig = get_config()
router = APIRouter(prefix=API_PREFIX, tags=["Admin"])


class DBActions(str, Enum):
    "The available path parameters for the `/admin/db/{action}` endpoint."
    init = "init"
    reset = "reset"


@router.post("/admin/db/{action}", tags=["Admin"])
async def db_action(action: DBActions) -> Dict:
    """
    Initiate one of the enumerated DBActions.
    """
    action_text = "initialized"
    if action == DBActions.reset:
        database.reset_db(CONFIG.database.sync_database_uri)
        action_text = DBActions.reset
    await database.configure_db(CONFIG.database.sync_database_uri)
    return {"data": {"message": f"Fidesctl database {action_text}"}}
