from enum import Enum
from typing import Dict, Optional

from fastapi import BackgroundTasks, HTTPException, Security, status
from loguru import logger

from fides.api.api.v1.endpoints import API_PREFIX
from fides.api.db.database import configure_db, migrate_db, reset_db
from fides.api.migrations.post_upgrade_backfill import (
    acquire_backfill_lock,
    run_backfill_manually,
)
from fides.api.oauth.utils import verify_oauth_client_prod
from fides.api.schemas.admin import BackfillRequest
from fides.api.util.api_router import APIRouter
from fides.api.util.memory_watchdog import (
    _capture_heap_dump,
    get_memory_watchdog_enabled,
)
from fides.common.api import scope_registry
from fides.common.api.scope_registry import BACKFILL_EXEC, HEAP_DUMP_EXEC
from fides.config import CONFIG

ADMIN_ROUTER = APIRouter(prefix=API_PREFIX, tags=["Admin"])


from enum import StrEnum


class DBActions(StrEnum):
    "The available path parameters for the `/admin/db/{action}` endpoint."

    upgrade = "upgrade"
    reset = "reset"
    downgrade = "downgrade"


@ADMIN_ROUTER.post(
    "/admin/db/{action}",
    tags=["Admin"],
    dependencies=[
        Security(verify_oauth_client_prod, scopes=[scope_registry.DATABASE_RESET])
    ],
    status_code=status.HTTP_200_OK,
)
def db_action(action: DBActions, revision: Optional[str] = "head") -> Dict:
    """
    Initiate one of the enumerated DBActions.

    NOTE: Database downgrades are _not_ guaranteed to succeed, and may put your application
    into an unrecoverable state. They should be invoked with caution. Only downgrade with
    explicit guidance from Ethyca support.
    """

    if action == DBActions.downgrade:
        try:
            migrate_db(
                database_url=CONFIG.database.sync_database_uri,
                revision=revision,  # type: ignore[arg-type]
                downgrade=True,
            )
            action_text = "downgrade"
        except Exception as e:
            logger.exception("Database downgrade failed")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database downgrade failed: {e}. Check server logs for more details",
            )
    else:
        action_text = "upgrade"

        if action == DBActions.reset:
            if revision != "head":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A revision cannot be specified on 'reset' actions",
                )
            if not CONFIG.dev_mode:
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail="Resetting the application database outside of dev_mode is not supported.",
                )

            reset_db(CONFIG.database.sync_database_uri)
            action_text = "reset"

        try:
            logger.info("Database being configured...")
            configure_db(CONFIG.database.sync_database_uri, revision=revision)
        except Exception as e:
            logger.exception("Database configuration failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database configuration failed: {e}. Check server logs for more details",
            )

    return {
        "data": {
            "message": f"Fides database action performed successfully: {action_text}"
        }
    }


@ADMIN_ROUTER.post(
    "/admin/heap-dump",
    tags=["Admin"],
    dependencies=[Security(verify_oauth_client_prod, scopes=[HEAP_DUMP_EXEC])],
    status_code=status.HTTP_200_OK,
)
def trigger_heap_dump() -> Dict:
    """
    Trigger a heap dump for memory diagnostics.

    Captures and logs detailed memory profiling information including:
    - Process memory stats (RSS, VMS)
    - Top object type counts
    - Garbage collector stats
    - Uncollectable objects (memory leaks)

    The full heap dump report is logged to error logs.
    """
    if not get_memory_watchdog_enabled():
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            detail="Heap dump functionality is not enabled. Set memory_watchdog_enabled to true in application configuration.",
        )

    logger.warning("Manual heap dump triggered via API")
    _capture_heap_dump()

    return {
        "data": {
            "message": "Heap dump captured successfully. Check server logs for detailed report."
        }
    }


@ADMIN_ROUTER.post(
    "/admin/backfill",
    tags=["Admin"],
    dependencies=[Security(verify_oauth_client_prod, scopes=[BACKFILL_EXEC])],
    status_code=status.HTTP_202_ACCEPTED,
)
def trigger_backfill(
    background_tasks: BackgroundTasks,
    request: BackfillRequest = BackfillRequest(),
) -> Dict:
    """
    Trigger a database backfill operation.

    This endpoint runs deferred data migrations (backfills) that were skipped during
    normal database migrations due to table size. The backfill runs in the background
    and progress can be monitored via server logs.

    The operation is:
    - **Idempotent**: Safe to run multiple times
    - **Resumable**: If interrupted, re-run and it will continue where it left off
    - **Non-blocking**: Uses small batches with delays to minimize database impact

    Only one backfill can run at a time. Returns 409 Conflict if a backfill is already running.
    """
    if not acquire_backfill_lock():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A backfill is already running. Check server logs for progress.",
        )

    logger.info(
        f"Manual backfill triggered via API "
        f"(batch_size={request.batch_size}, delay={request.batch_delay_seconds}s)"
    )

    background_tasks.add_task(
        run_backfill_manually,
        request.batch_size,
        request.batch_delay_seconds,
    )

    return {
        "data": {
            "message": "Backfill started in background. Monitor progress via server logs.",
            "config": {
                "batch_size": request.batch_size,
                "batch_delay_seconds": request.batch_delay_seconds,
            },
        }
    }
