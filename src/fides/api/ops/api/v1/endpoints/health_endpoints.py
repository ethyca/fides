import logging
from typing import Dict, Optional, Union

from alembic import migration, script
from fastapi import Depends
from redis.exceptions import ResponseError
from sqlalchemy.orm import Session

from fides.api.ops.api import deps
from fides.api.ops.api.v1.urn_registry import HEALTH
from fides.api.ops.common_exceptions import RedisConnectionError
from fides.ctl.core.config import get_config
from fides.api.ops.db.database import get_alembic_config
from fides.api.ops.util.api_router import APIRouter
from fides.api.ops.util.cache import get_cache
from fides.api.ops.util.logger import Pii

router = APIRouter(tags=["Public"])
CONFIG = get_config()

logger = logging.getLogger(__name__)
# stops polluting logs with sqlalchemy / alembic info-level logs
logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)
logging.getLogger("alembic").setLevel(logging.WARNING)


@router.get(HEALTH, response_model=Dict[str, Union[bool, str]])
def health_check(
    db: Session = Depends(deps.get_db_for_health_check),
) -> Dict[str, Union[bool, str]]:
    return {
        "webserver": "healthy",
        "database": get_db_health(CONFIG.database.sqlalchemy_database_uri, db),
        "cache": get_cache_health(),
    }


def get_db_health(database_url: Optional[str], db: Session) -> str:
    """Checks if the db is reachable and up to date in alembic migrations"""
    try:
        alembic_config = get_alembic_config(database_url)
        alembic_script_directory = script.ScriptDirectory.from_config(alembic_config)
        context = migration.MigrationContext.configure(db.connection())
        if (
            context.get_current_revision()
            != alembic_script_directory.get_current_head()
        ):
            return "needs migration"
        return "healthy"
    except Exception as error:  # pylint: disable=broad-except
        logger.error("Unable to reach the database: %s", Pii(str(error)))
        return "unhealthy"


def get_cache_health() -> str:
    """Checks if the cache is reachable"""
    if not CONFIG.redis.enabled:
        return "no cache configured"
    try:
        get_cache()
        return "healthy"
    except (RedisConnectionError, ResponseError) as e:
        logger.error("Unable to reach cache: %s", Pii(str(e)))
        return "unhealthy"
