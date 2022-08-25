from typing import Dict
import logging

from fastapi import HTTPException, status

import fides
from fides.api.ctl.database.database import get_db_health
from fides.api.ctl.utils.api_router import APIRouter
from fides.ctl.core.config import FidesctlConfig, get_config

from typing import Dict

from redis.exceptions import ResponseError

from fides.api.ops.common_exceptions import RedisConnectionError
from fides.api.ops.core.config import config as ops_config
from fides.api.ops.util.api_router import APIRouter
from fides.api.ops.util.cache import get_cache
from fides.api.ops.util.logger import Pii

CONFIG: FidesctlConfig = get_config()

router = APIRouter(tags=["Health"])

logger = logging.getLogger(__name__)
# stops polluting logs with sqlalchemy / alembic info-level logs
logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)
logging.getLogger("alembic").setLevel(logging.WARNING)


def get_cache_health() -> str:
    """Checks if the cache is reachable"""
    if not ops_config.redis.enabled:
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
                        "status": "healthy",
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
                            "status": "healthy",
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
        "status": "healthy",
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
