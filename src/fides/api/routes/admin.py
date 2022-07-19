from enum import Enum
from typing import Dict

from fides.api.database import database
from fides.api.routes.util import API_PREFIX
from fides.api.utils.api_router import APIRouter
from fides.core.config import FidesctlConfig, get_config

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
        database.reset_db(CONFIG.api.sync_database_url)
        action_text = DBActions.reset
    await database.configure_db(CONFIG.api.sync_database_url)
    return {"data": {"message": f"Fidesctl database {action_text}"}}
