"""Per-collection child workflow.

Each collection node gets its own NodeExecutionWorkflow with independent
event history. Dispatches to the appropriate execution strategy:

- Regular: activity with RetryPolicy
- Manual: activity, wait for signal if needed, re-execute
- Polling: long-running activity with heartbeat poll loop
- Callback: activity, wait for signal, re-execute
"""

from __future__ import annotations

from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from fides.api.task.temporal.activities.connector_execution import (
        execute_access_node,
        execute_consent_node,
        execute_erasure_node,
        execute_polling_node,
    )
    from fides.api.task.temporal.converters import (
        NodeExecutionParams,
        NodeExecutionResult,
        TraversalPhase,
    )
    from fides.api.task.temporal.signals import TaskCompletedSignal
    from fides.config import CONFIG

PHASE_ACTIVITY_MAP = {
    TraversalPhase.ACCESS: execute_access_node,
    TraversalPhase.ERASURE: execute_erasure_node,
    TraversalPhase.CONSENT: execute_consent_node,
}


@workflow.defn
class NodeExecutionWorkflow:
    """Execute a single collection node within a traversal phase."""

    def __init__(self) -> None:
        self._signal_received: TaskCompletedSignal | None = None

    @workflow.signal
    async def task_completed(self, signal: TaskCompletedSignal) -> None:
        """Signal handler for manual/callback task completion."""
        self._signal_received = signal

    @workflow.run
    async def run(self, params: NodeExecutionParams) -> NodeExecutionResult:
        if params.is_manual_task:
            return await self._execute_manual(params)
        elif params.async_type == "polling":
            return await self._execute_polling(params)
        elif params.async_type == "callback":
            return await self._execute_callback(params)
        else:
            return await self._execute_regular(params)

    async def _execute_regular(
        self, params: NodeExecutionParams
    ) -> NodeExecutionResult:
        """Standard connector execution.

        The existing @retry decorator on GraphTask handles retries internally,
        so Temporal should not add additional retry attempts on top.
        """
        activity_fn = PHASE_ACTIVITY_MAP[params.phase]
        return await workflow.execute_activity(
            activity_fn,
            params,
            start_to_close_timeout=timedelta(minutes=30),
            retry_policy=RetryPolicy(maximum_attempts=1),
        )

    async def _execute_manual(self, params: NodeExecutionParams) -> NodeExecutionResult:
        """Manual task: execute, wait for signal if input needed, re-execute."""
        activity_fn = PHASE_ACTIVITY_MAP[params.phase]

        try:
            return await workflow.execute_activity(
                activity_fn,
                params,
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(maximum_attempts=1),
            )
        except Exception as exc:
            if "requires user input" in str(exc) or "AwaitingAsyncTask" in str(exc):
                workflow.logger.info(
                    f"Manual task {params.node_address} awaiting input"
                )
                await workflow.wait_condition(
                    lambda: self._signal_received is not None,
                    timeout=timedelta(seconds=CONFIG.execution.request_task_ttl),
                )
                if self._signal_received is None:
                    return NodeExecutionResult(
                        node_address=params.node_address,
                        status="error",
                        error_message="Manual task timed out waiting for input",
                    )
                return await workflow.execute_activity(
                    activity_fn,
                    params,
                    start_to_close_timeout=timedelta(minutes=30),
                    retry_policy=RetryPolicy(maximum_attempts=3),
                )
            raise

    async def _execute_polling(
        self, params: NodeExecutionParams
    ) -> NodeExecutionResult:
        """Async polling: activity handles full poll loop with heartbeats."""
        return await workflow.execute_activity(
            execute_polling_node,
            params,
            start_to_close_timeout=timedelta(
                days=CONFIG.execution.async_polling_request_timeout_days
            ),
            heartbeat_timeout=timedelta(
                hours=CONFIG.execution.async_polling_interval_hours * 2
            ),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )

    async def _execute_callback(
        self, params: NodeExecutionParams
    ) -> NodeExecutionResult:
        """Async callback: execute, wait for signal, re-execute."""
        activity_fn = PHASE_ACTIVITY_MAP[params.phase]

        try:
            return await workflow.execute_activity(
                activity_fn,
                params,
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=RetryPolicy(maximum_attempts=1),
            )
        except Exception as exc:
            if "AwaitingAsyncTask" in str(exc):
                workflow.logger.info(
                    f"Callback task {params.node_address} awaiting external callback"
                )
                await workflow.wait_condition(
                    lambda: self._signal_received is not None,
                    timeout=timedelta(
                        days=CONFIG.execution.async_polling_request_timeout_days
                    ),
                )
                if self._signal_received is None:
                    return NodeExecutionResult(
                        node_address=params.node_address,
                        status="error",
                        error_message="Callback task timed out",
                    )
                return await workflow.execute_activity(
                    activity_fn,
                    params,
                    start_to_close_timeout=timedelta(minutes=30),
                    retry_policy=RetryPolicy(maximum_attempts=3),
                )
            raise
