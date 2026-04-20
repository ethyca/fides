import asyncio
from collections.abc import Callable
from typing import Any, AsyncContextManager, Dict, List, Literal, Optional

from fastapi import Depends, HTTPException, Query, status
from loguru import logger
from pydantic import BaseModel
from redis.exceptions import ResponseError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

import fides
from fides.api.common_exceptions import RedisConnectionError
from fides.api.db.ctl_session import (
    async_session,
    ensure_async_readonly_pool_prewarmed,
    is_async_readonly_pool_prewarmed,
    readonly_async_engine,
    readonly_async_session,
)
from fides.api.db.database import get_db_health
from fides.api.deps import get_db
from fides.api.tasks import celery_app, get_worker_ids
from fides.api.util.api_router import APIRouter
from fides.api.util.cache import get_cache, get_queue_counts
from fides.api.util.logger import Pii
from fides.common.session_management import get_readonly_api_session
from fides.config import CONFIG

CacheHealth = Literal["healthy", "unhealthy", "no cache configured", "skipped"]
PoolHealth = Literal["healthy", "unhealthy", "skipped"]
DatabaseResponseHealth = Literal["healthy", "unhealthy", "needs migration"]
HEALTH_ROUTER = APIRouter(tags=["Health"])

# Per-pool ping: cap how long the health endpoint can block on each async check, and bound
# statement runtime on PostgreSQL (SET LOCAL is a no-op on other dialects we skip).
DATABASE_HEALTHCHECK_QUERY_TIMEOUT_SECONDS = 1.0


def _healthcheck_statement_timeout_ms() -> int:
    return max(1, int(DATABASE_HEALTHCHECK_QUERY_TIMEOUT_SECONDS * 1000))


def _bind_dialect_name(bind: Any) -> str:
    """Resolve dialect name for sync Engine or AsyncEngine."""
    sync_engine = getattr(bind, "sync_engine", bind)
    return sync_engine.dialect.name


def _sync_healthcheck_ping(db: Session) -> None:
    """Run a lightweight SELECT 1 with a PostgreSQL per-statement timeout."""
    if _bind_dialect_name(db.get_bind()) == "postgresql":
        # GUC value must be a literal in the statement; asyncpg rejects bound params here.
        timeout_ms = _healthcheck_statement_timeout_ms()
        db.execute(text(f"SET LOCAL statement_timeout = {timeout_ms}"))
    db.execute(text("SELECT 1"))


async def _async_healthcheck_ping(session: AsyncSession) -> None:
    """Run a lightweight SELECT 1 with a PostgreSQL per-statement timeout."""
    if _bind_dialect_name(session.get_bind()) == "postgresql":
        timeout_ms = _healthcheck_statement_timeout_ms()
        await session.execute(text(f"SET LOCAL statement_timeout = {timeout_ms}"))
    await session.execute(text("SELECT 1"))


class CoreHealthCheck(BaseModel):
    """Server Healthcheck schema"""

    webserver: str
    version: str
    cache: CacheHealth


class DatabaseHealthCheck(BaseModel):
    """Database Healthcheck Schema"""

    database: DatabaseResponseHealth
    pools: Dict[str, "PoolStatus"]
    async_readonly_pool_prewarmed: Optional[bool] = None
    database_revision: Optional[str] = None


class PoolPrewarming(BaseModel):
    """Optional pool prewarming details."""

    target: int
    checked_in: int
    checked_out: int
    capacity_percentage: Optional[float]


class PoolStatus(BaseModel):
    """Per-pool health details."""

    health: PoolHealth
    prewarming: Optional[PoolPrewarming] = None


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
    """Confirm that configured API database pools are reachable."""
    pools: Dict[str, PoolStatus] = {}
    async_readonly_pool_prewarmed: Optional[bool] = None

    migration_health, current_revision = get_db_health(
        CONFIG.database.sync_database_uri, db=db
    )

    # Primary sync pool (already checked out by dependency-injected session).
    pools["api_sync_primary"] = PoolStatus(health=_check_sync_session(db))

    # Optional sync readonly pool.
    if CONFIG.database.sqlalchemy_readonly_database_uri:
        readonly_db: Optional[Session] = None
        try:
            readonly_db = get_readonly_api_session()
            pools["api_sync_readonly"] = PoolStatus(
                health=_check_sync_session(readonly_db)
            )
        except Exception as error:  # pylint: disable=broad-except
            logger.error(
                "Unable to open sync readonly database pool session: {}",
                Pii(str(error)),
            )
            pools["api_sync_readonly"] = PoolStatus(health="unhealthy")
        finally:
            if readonly_db:
                readonly_db.close()
    else:
        pools["api_sync_readonly"] = PoolStatus(health="skipped")

    # Primary async pool.
    pools["api_async_primary"] = PoolStatus(
        health=await _check_async_session(async_session)
    )

    # Optional readonly async pool with prewarm awareness.
    if CONFIG.database.async_readonly_database_uri:
        if CONFIG.database.async_readonly_database_prewarm:
            await ensure_async_readonly_pool_prewarmed()
            async_readonly_pool_prewarmed = is_async_readonly_pool_prewarmed()
        else:
            async_readonly_pool_prewarmed = False

        pools["api_async_readonly"] = PoolStatus(
            health=await _check_async_session(readonly_async_session),
            prewarming=_get_async_readonly_prewarming_details(),
        )
    else:
        pools["api_async_readonly"] = PoolStatus(health="skipped")
        async_readonly_pool_prewarmed = None

    has_unhealthy_pool = any(
        pool_status.health == "unhealthy" for pool_status in pools.values()
    )

    if has_unhealthy_pool:
        overall_database: DatabaseResponseHealth = "unhealthy"
    elif migration_health == "needs migration":
        overall_database = "needs migration"
    elif migration_health == "unhealthy":
        # Rare: get_db_health() can fail (e.g. Alembic metadata) while pool pings still pass.
        overall_database = "unhealthy"
    else:
        overall_database = "healthy"

    response = DatabaseHealthCheck(
        database=overall_database,
        pools=pools,
        async_readonly_pool_prewarmed=async_readonly_pool_prewarmed,
        database_revision=current_revision if current_revision else "unknown",
    ).model_dump(mode="json")

    if overall_database != "healthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=response
        )

    return response


def _check_sync_session(db: Session) -> PoolHealth:
    """Return health status for a sync pool-backed session."""
    try:
        _sync_healthcheck_ping(db)
        return "healthy"
    except Exception as error:  # pylint: disable=broad-except
        logger.error("Unable to reach sync database pool: {}", Pii(str(error)))
        return "unhealthy"


async def _check_async_session(
    session_factory: Callable[[], AsyncContextManager[AsyncSession]],
) -> PoolHealth:
    """Return health status for an async pool-backed session factory."""

    async def _ping_with_session() -> None:
        async with session_factory() as session:
            await _async_healthcheck_ping(session)

    try:
        await asyncio.wait_for(
            _ping_with_session(),
            timeout=DATABASE_HEALTHCHECK_QUERY_TIMEOUT_SECONDS,
        )
        return "healthy"
    except asyncio.TimeoutError:
        logger.error(
            "Async database healthcheck timed out after {}s",
            DATABASE_HEALTHCHECK_QUERY_TIMEOUT_SECONDS,
        )
        return "unhealthy"
    except Exception as error:  # pylint: disable=broad-except
        logger.error("Unable to reach async database pool: {}", Pii(str(error)))
        return "unhealthy"


def _get_async_readonly_prewarming_details() -> Optional[PoolPrewarming]:
    """Return readonly async pool prewarming details when enabled."""
    if not CONFIG.database.async_readonly_database_prewarm:
        return None
    if not readonly_async_engine:
        return None

    pool = readonly_async_engine.sync_engine.pool
    target = CONFIG.database.async_readonly_database_pool_size
    checked_in = int(pool.checkedin())
    checked_out = int(pool.checkedout())

    capacity_percentage: Optional[float]
    if target <= 0:
        capacity_percentage = None
    else:
        capacity_percentage = (checked_in + checked_out) / target

    return PoolPrewarming(
        target=target,
        checked_in=checked_in,
        checked_out=checked_out,
        capacity_percentage=capacity_percentage,
    )


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
    ).model_dump(mode="json")

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
async def health(
    include_cache: Optional[bool] = Query(default=False),
) -> Dict:
    """
    Confirm that the API is running and healthy.

    If include_cache is True, the cache health will be included in the response.
    If include_cache is False, the cache health check will be skipped and set to "skipped".
    """

    if include_cache:
        cache_health = get_cache_health()
    else:
        cache_health = "skipped"

    response = CoreHealthCheck(
        webserver="healthy",
        version=str(fides.__version__),
        cache=cache_health,
    ).model_dump(mode="json")

    for _, value in response.items():
        if value == "unhealthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=response
            )

    return response
