import gc
from loguru import logger
from sqlalchemy.orm import Session


GC_COUNT = 3

def cleanup_dsr_memory(
    session: Session,
    privacy_request_id: str,
) -> None:
    """
    Aggressively clean up memory after DSR processing.

    This prevents baseline memory creep when processing multiple concurrent DSRs.
    Designed to be safe for both DSR 2.0 and DSR 3.0 workflows.

    Called on ALL exit paths in run_privacy_request() right before returning:
    - Successful completion
    - Error/exception paths
    - Pause paths (manual webhooks, email send)
    - DSR 3.0 PrivacyRequestExit (before re-invocation)

    Cleanup steps:
    1. Checks for dirty session state and rolls back if needed
    2. Expunges session identity map to release ORM objects
    3. Runs garbage collection 3x to free memory
    4. Logs connection pool diagnostics

    IMPORTANT Safety notes:
    - Does NOT close the session - the context manager handles that
    - DOES rollback if unexpected dirty state detected (logged as ERROR)
    - Safe for DSR 3.0 - new session created on re-invocation
    - All operations wrapped in try-except to never break DSR

    Args:
        session: SQLAlchemy session (managed by caller's context manager)
        privacy_request_id: ID of the privacy request
    """
    logger.info(
        "Performing memory cleanup for privacy request '{}'",
        privacy_request_id,
    )

    try:
        # 1. Clear SQLAlchemy session identity map
        # This releases ORM object references so they can be garbage collected
        try:
            identity_map_size = (
                len(session.identity_map) if hasattr(session, "identity_map") else 0
            )
            # Check for unexpected pending changes (shouldn't happen, indicates a bug)
            if session.new or session.dirty or session.deleted:
                # This should NOT happen - indicates a bug in DSR logic
                logger.error(
                    f"UNEXPECTED: Pending session changes at cleanup "
                    f"(new: {len(session.new)}, dirty: {len(session.dirty)}, "
                    f"deleted: {len(session.deleted)}). Rolling back to clean state."
                )
                # Rollback to ensure session is clean before expunging
                # This prevents losing any critical state that should have been committed
                session.rollback()
            # Expunge all objects from session to release memory
            session.expunge_all()
            logger.debug(
                f"Cleared SQLAlchemy session identity map ({identity_map_size} objects)"
            )
        except Exception as e:
            logger.debug(f"Could not clear SQLAlchemy session identity map: {e}")

        # 2. Force multiple garbage collection passes AFTER expunging
        # Now that references are released, GC can actually free the objects
        collected_total = 0
        for i in range(GC_COUNT):
            collected = gc.collect()
            collected_total += collected
            if collected > 0:
                logger.debug(f"GC pass {i + 1}: collected {collected} objects")

        if collected_total > 0:
            logger.info(f"Garbage collection freed {collected_total} total objects")

        # 3. Log connection pool diagnostics (non-invasive)
        try:
            engine = session.get_bind()
            if engine and hasattr(engine, "pool"):
                pool = engine.pool
                if hasattr(pool, "_overflow") and hasattr(pool, "_pool"):
                    overflow_count = len(pool._overflow) if pool._overflow else 0
                    pool_count = (
                        pool._pool.qsize() if hasattr(pool._pool, "qsize") else 0
                    )
                    logger.debug(
                        f"Connection pool state: {pool_count} pooled, {overflow_count} overflow"
                    )
        except Exception as e:
            logger.debug(f"Could not inspect connection pool: {e}")

    except Exception as exc:
        # Never fail the DSR due to cleanup errors
        logger.warning(f"Error during memory cleanup: {exc}")
