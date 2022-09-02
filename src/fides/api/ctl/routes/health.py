import logging
from typing import Dict

from fastapi import HTTPException, status
from redis.exceptions import ResponseError

import fides
from fides.api.ctl.database.database import get_db_health
from fides.api.ctl.utils.api_router import APIRouter
from fides.api.ops.common_exceptions import RedisConnectionError
from fides.api.ops.util.cache import get_cache
from fides.api.ops.util.logger import Pii
from fides.ctl.core.config import FidesConfig, get_config

CONFIG: FidesConfig = get_config()

router = APIRouter(tags=["Health"])

logger = logging.getLogger(__name__)
# stops polluting logs with sqlalchemy / alembic info-level logs
logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)
logging.getLogger("alembic").setLevel(logging.WARNING)


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


@router.get(
    "/health",
    response_model=Dict[str, str],
    responses={
        status.HTTP_200_OK: {
            "content": {
                "application/json": {
                    "example": {
                        "webserver": "healthy",
                        "version": "1.0.0",
                        "database": "healthy",
                        "cache": "healthy",
                    }
                }
            }
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "webserver": "healthy",
                            "version": "1.0.0",
                            "database": "unhealthy",
                            "cache": "healthy",
                        }
                    }
                }
            }
        },
    },
)
async def health() -> Dict:
    "Confirm that the API is running and healthy."
    database_health = get_db_health(CONFIG.database.sync_database_uri)
    cache_health = get_cache_health()
    response = {
        "webserver": "healthy",
        "version": str(fides.__version__),
        "database": database_health,
        "cache": cache_health,
    }

    for _, value in response.items():
        if value == "unhealthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=response
            )

    return response
