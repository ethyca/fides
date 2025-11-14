from enum import Enum
from typing import Dict, Optional

from fastapi import HTTPException, Security, status
from loguru import logger

from fides.api.api.v1.endpoints import API_PREFIX
from fides.api.db.database import configure_db, migrate_db, reset_db
from fides.api.oauth.utils import verify_oauth_client_prod
from fides.api.util.api_router import APIRouter
from fides.api.util.memory_watchdog import (
    _capture_heap_dump,
    get_memory_watchdog_enabled,
)
from fides.common.api import scope_registry
from fides.common.api.scope_registry import HEAP_DUMP_EXEC
from fides.config import CONFIG

ADMIN_ROUTER = APIRouter(prefix=API_PREFIX, tags=["Admin"])


class DBActions(str, Enum):
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
            migrate_db(database_url=CONFIG.database.sync_database_uri, revision=revision, downgrade=True)  # type: ignore[arg-type]
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
