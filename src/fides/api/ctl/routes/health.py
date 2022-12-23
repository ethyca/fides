from typing import Any, Dict, List, Union

from fastapi import Depends, HTTPException, status
from loguru import logger
from redis.exceptions import ResponseError
from sqlalchemy.orm import Session

import fides
from fides.api.ctl.database.database import get_db_health
from fides.api.ctl.utils.api_router import APIRouter
from fides.api.ops.api.deps import get_db
from fides.api.ops.common_exceptions import RedisConnectionError
from fides.api.ops.tasks import celery_app, get_worker_ids
from fides.api.ops.util.cache import get_cache
from fides.api.ops.util.logger import Pii
from fides.core.config import FidesConfig, get_config

CONFIG: FidesConfig = get_config()

router = APIRouter(tags=["Health"])


def get_cache_health() -> str:
    """Checks if the cache is reachable"""

    if not CONFIG.redis.enabled:
        return "no cache configured"
    try:
        get_cache()
        return "healthy"
    except (RedisConnectionError, ResponseError) as e:
        logger.error("Unable to reach cache: {}", Pii(str(e)))
        return "unhealthy"


@router.get(
    "/health",
    response_model=Dict[str, Union[str, List[str]]],
    responses={
        status.HTTP_200_OK: {
            "content": {
                "application/json": {
                    "example": {
                        "webserver": "healthy",
                        "version": "1.0.0",
                        "database": "healthy",
                        "cache": "healthy",
                        "workers_enabled": "True",
                        "workers": ["celery@c606808353b5"],
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
                            "workers_enabled": "True",
                            "workers": ["celery@c606808353b5"],
                        }
                    }
                }
            }
        },
    },
)
async def health(
    db: Session = Depends(get_db),
) -> Dict:  # Intentionally injecting the ops get_db
    """Confirm that the API is running and healthy."""
    database_health = get_db_health(CONFIG.database.sync_database_uri, db=db)
    cache_health = get_cache_health()
    response: Dict[str, Any] = {
        "webserver": "healthy",
        "version": str(fides.__version__),
        "database": database_health,
        "cache": cache_health,
        "workers_enabled": False,
        "workers": [],
    }
    fides_is_using_workers = not celery_app.conf["task_always_eager"]
    if fides_is_using_workers:
        response["workers_enabled"] = True
        response["workers"] = get_worker_ids()

    for _, value in response.items():
        if value == "unhealthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=response
            )

    return response
