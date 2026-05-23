"""Temporal implementation of the DSREngine protocol."""

from __future__ import annotations

import asyncio
from typing import Any, Optional

from loguru import logger
from temporalio.client import Client

from fides.api.task.temporal.converters import DSRLifecycleParams
from fides.config import CONFIG


class TemporalDSREngine:
    """DSR execution engine backed by Temporal workflows."""

    def dispatch_privacy_request(
        self,
        privacy_request_id: str,
        from_webhook_id: Optional[str] = None,
        from_step: Optional[str] = None,
    ) -> Optional[str]:
        from fides.api.task.temporal.workflows.dsr_lifecycle import (
            DSRLifecycleWorkflow,
        )

        logger.info(
            "Temporal: dispatching privacy request {} from_step={}",
            privacy_request_id,
            from_step,
        )

        async def _start_workflow() -> str:
            from fides.api.task.temporal.client import get_temporal_client

            client = await get_temporal_client()
            handle = await client.start_workflow(
                DSRLifecycleWorkflow.run,
                DSRLifecycleParams(
                    privacy_request_id=privacy_request_id,
                    from_webhook_id=from_webhook_id,
                    from_step=from_step,
                ),
                id=f"dsr-{privacy_request_id}",
                task_queue=CONFIG.temporal.task_queue,
            )
            return handle.id

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                workflow_id = pool.submit(asyncio.run, _start_workflow()).result()
        else:
            workflow_id = asyncio.run(_start_workflow())

        return workflow_id

    def dispatch_request_task(
        self,
        request_task_id: str,
        privacy_request_id: str,
        action_type: str,
        privacy_request_proceed: bool = True,
    ) -> None:
        logger.debug(
            "Temporal: dispatch_request_task is a no-op (workflow handles scheduling)"
        )

    def signal_task_complete(
        self,
        privacy_request_id: str,
        collection_address: str,
        data: Optional[dict[str, Any]] = None,
    ) -> None:
        from fides.api.task.temporal.signals import TaskCompletedSignal
        from fides.api.task.temporal.workflows.node_execution import (
            NodeExecutionWorkflow,
        )

        logger.info(
            "Temporal: signaling task complete for {} collection {}",
            privacy_request_id,
            collection_address,
        )

        signal = TaskCompletedSignal(
            collection_address=collection_address,
            data=data,
            rows_masked=data.get("rows_masked") if data else None,
        )

        async def _send_signal() -> None:
            from fides.api.task.temporal.client import get_temporal_client

            client = await get_temporal_client()
            # Find the child workflow for this node
            # Child workflow IDs follow pattern: {phase}-{pr_id}-{collection_address}
            for phase in ["access", "erasure", "consent"]:
                child_id = f"{phase}-{privacy_request_id}-{collection_address}"
                try:
                    handle = client.get_workflow_handle(child_id)
                    await handle.signal(NodeExecutionWorkflow.task_completed, signal)
                    logger.info(
                        "Signal sent to workflow {}",
                        child_id,
                    )
                    return
                except Exception:
                    continue

            logger.warning(
                "Could not find workflow for {} collection {}",
                privacy_request_id,
                collection_address,
            )

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                pool.submit(asyncio.run, _send_signal()).result()
        else:
            asyncio.run(_send_signal())
