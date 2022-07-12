import logging
from typing import Dict, Optional, Union

from alembic import migration, script
from redis.exceptions import ResponseError
from sqlalchemy import create_engine

from fidesops.api.v1.urn_registry import HEALTH
from fidesops.common_exceptions import RedisConnectionError
from fidesops.core.config import config
from fidesops.db.database import get_alembic_config
from fidesops.util.api_router import APIRouter
from fidesops.util.cache import get_cache

router = APIRouter(tags=["Public"])

logger = logging.getLogger(__name__)
# stops polluting logs with sqlalchemy / alembic info-level logs
logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)
logging.getLogger("alembic").setLevel(logging.WARNING)


@router.get(HEALTH, response_model=Dict[str, Union[bool, str]])
def health_check() -> Dict[str, Union[bool, str]]:
    return {
        "webserver": "healthy",
        "database": get_db_health(config.database.SQLALCHEMY_DATABASE_URI),
        "cache": get_cache_health(),
    }


def get_db_health(database_url: Optional[str]) -> str:
    """Checks if the db is reachable and up to date in alembic migrations"""
    if not database_url or not config.database.ENABLED:
        return "no db configured"
    try:
        engine = create_engine(database_url)
        alembic_config = get_alembic_config(database_url)
        alembic_script_directory = script.ScriptDirectory.from_config(alembic_config)
        with engine.begin() as conn:
            context = migration.MigrationContext.configure(conn)
            if (
                context.get_current_revision()
                != alembic_script_directory.get_current_head()
            ):
                return "needs migration"
        return "healthy"
    except Exception as error:  # pylint: disable=broad-except
        logger.error(f"Unable to reach the database: {error}")
        return "unhealthy"


def get_cache_health() -> str:
    """Checks if the cache is reachable"""
    if not config.redis.ENABLED:
        return "no cache configured"
    try:
        get_cache()
        return "healthy"
    except (RedisConnectionError, ResponseError) as e:
        logger.error(f"Unable to reach cache: {e}")
        return "unhealthy"
