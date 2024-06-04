from typing import Dict, List, Literal, Optional

from fastapi import Depends, HTTPException, status
from loguru import logger
from pydantic import BaseModel
from redis.exceptions import ResponseError
from sqlalchemy.orm import Session

import fides
from fides.api.api.deps import get_db
from fides.api.common_exceptions import RedisConnectionError
from fides.api.db.database import get_db_health
from fides.api.tasks import celery_app, get_worker_ids
from fides.api.util.api_router import APIRouter
from fides.api.util.cache import get_cache, get_queue_counts
from fides.api.util.logger import Pii
from fides.config import CONFIG

CacheHealth = Literal["healthy", "unhealthy", "no cache configured"]
HEALTH_ROUTER = APIRouter(tags=["Health"])


class CoreHealthCheck(BaseModel):
    """Server Healthcheck schema"""

    webserver: str
    version: str
    cache: CacheHealth


class DatabaseHealthCheck(BaseModel):
    """Database Healthcheck Schema"""

    database: str
    database_revision: Optional[str]


class WorkerHealthCheck(BaseModel):
    """Worker Healthcheck Schema"""

    workers_enabled: bool
    workers: List[str]
    queue_counts: Dict[str, int]


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


@HEALTH_ROUTER.get(
    "/health/database",
    response_model=DatabaseHealthCheck,
    responses={
        status.HTTP_200_OK: {
            "content": {
                "application/json": {
                    "example": {
                        "database": "healthy",
                    }
                }
            }
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "database": "unhealthy",
                        }
                    }
                }
            }
        },
    },
)
async def database_health(db: Session = Depends(get_db)) -> Dict:
    """Confirm that the API is running and healthy."""
    db_health, revision = get_db_health(CONFIG.database.sync_database_uri, db=db)

    response = DatabaseHealthCheck(
        database=db_health, database_revision=revision if revision else "unknown"
    ).dict()

    if db_health != "healthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=response
        )

    return response


@HEALTH_ROUTER.get(
    "/health/workers",
    response_model=WorkerHealthCheck,
    responses={
        status.HTTP_200_OK: {
            "content": {
                "application/json": {
                    "example": {
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
                            "workers_enabled": "True",
                            "workers": ["celery@c606808353b5"],
                        }
                    }
                }
            }
        },
    },
)
async def workers_health() -> Dict:
    """Confirm that the API is running and healthy."""
    response = WorkerHealthCheck(
        workers_enabled=False, workers=[], queue_counts={}
    ).dict()

    fides_is_using_workers = not celery_app.conf["task_always_eager"]
    if fides_is_using_workers:
        response["workers_enabled"] = True
        # Figure out a way to make this faster
        response["workers"] = get_worker_ids()
        response["queue_counts"] = get_queue_counts()

    return response


@HEALTH_ROUTER.get(
    "/health",
    response_model=CoreHealthCheck,
    responses={
        status.HTTP_200_OK: {
            "content": {
                "application/json": {
                    "example": {
                        "webserver": "healthy",
                        "version": "1.0.0",
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
                            "cache": "unhealthy",
                        }
                    }
                }
            }
        },
    },
)
async def health() -> Dict:
    """Confirm that the API is running and healthy."""
    cache_health = get_cache_health()
    response = CoreHealthCheck(
        webserver="healthy",
        version=str(fides.__version__),
        cache=cache_health,
    ).dict()

    for _, value in response.items():
        if value == "unhealthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=response
            )

    return response
