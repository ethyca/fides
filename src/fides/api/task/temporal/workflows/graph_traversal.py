"""Phase-level graph traversal child workflow.

Orchestrates the execution of all nodes in a single phase (access, erasure,
or consent) by spawning NodeExecutionWorkflow child workflows for each
collection, respecting DAG dependencies via wait_condition.
"""

from __future__ import annotations

import asyncio
from datetime import timedelta

from temporalio import workflow
from temporalio.workflow import ParentClosePolicy

with workflow.unsafe.imports_passed_through():
    from fides.api.task.temporal.converters import (
        GraphTraversalParams,
        GraphTraversalResult,
        NodeExecutionParams,
        NodeExecutionResult,
        NodeInfo,
    )
    from fides.api.task.temporal.workflows.node_execution import (
        NodeExecutionWorkflow,
    )


@workflow.defn
class GraphTraversalWorkflow:
    """Execute all nodes in a traversal phase, respecting DAG ordering.

    Nodes whose upstream dependencies are satisfied run concurrently
    as child workflows. The root node is pre-completed (identity data),
    and the terminator node completes when all predecessors finish.
    """

    def __init__(self) -> None:
        self._completed: dict[str, NodeExecutionResult] = {}
        self._failed: dict[str, str] = {}

    @workflow.query
    def get_progress(self) -> dict:
        """Query handler for real-time execution progress."""
        return {
            "completed": list(self._completed.keys()),
            "failed": list(self._failed.keys()),
        }

    @workflow.run
    async def run(self, params: GraphTraversalParams) -> GraphTraversalResult:
        graph = params.graph_plan

        # Root is pre-completed (holds identity/seed data)
        for addr, node in graph.nodes.items():
            if node.is_root:
                self._completed[addr] = NodeExecutionResult(
                    node_address=addr, status="complete"
                )

        # Collect executable nodes (not root, not terminator)
        executable_nodes = [
            node
            for node in graph.nodes.values()
            if not node.is_root and not node.is_terminator
        ]

        # Launch all executable nodes concurrently; each waits on its deps
        tasks = []
        for node in executable_nodes:
            tasks.append(asyncio.ensure_future(self._execute_node(params, node)))

        # Wait for all to complete (or fail)
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, BaseException):
                    workflow.logger.error(f"Node execution failed: {result}")

        # Mark terminator complete
        for addr, node in graph.nodes.items():
            if node.is_terminator:
                self._completed[addr] = NodeExecutionResult(
                    node_address=addr, status="complete"
                )

        return GraphTraversalResult(
            status="complete" if not self._failed else "partial_failure",
            completed_nodes=list(self._completed.keys()),
            failed_nodes=list(self._failed.keys()),
        )

    async def _execute_node(
        self,
        params: GraphTraversalParams,
        node: NodeInfo,
    ) -> None:
        """Execute a single node after its upstream dependencies complete."""

        # Skip nodes that are already completed and not dirty (clean on reprocess)
        if (node.already_completed or node.already_skipped) and not node.is_dirty:
            status = "skipped" if node.already_skipped else "complete"
            self._completed[node.address] = NodeExecutionResult(
                node_address=node.address, status=status
            )
            workflow.logger.info(
                f"Skipping clean node {node.address} (already {status})"
            )
            return

        # Wait for all upstream nodes to be completed
        def _deps_satisfied() -> bool:
            return all(
                dep in self._completed or dep in self._failed for dep in node.upstream
            )

        await workflow.wait_condition(_deps_satisfied)

        # If any upstream failed, mark this node failed too (cascade)
        failed_upstreams = [dep for dep in node.upstream if dep in self._failed]
        if failed_upstreams:
            self._failed[node.address] = f"Upstream nodes failed: {failed_upstreams}"
            return

        try:
            result = await workflow.execute_child_workflow(
                NodeExecutionWorkflow.run,
                NodeExecutionParams(
                    privacy_request_id=params.privacy_request_id,
                    phase=params.phase,
                    node_address=node.address,
                    request_task_id=node.request_task_id or "",
                    is_manual_task=node.is_manual_task,
                    async_type=node.async_type,
                ),
                id=f"{params.phase}-{params.privacy_request_id}-{node.address}",
                parent_close_policy=ParentClosePolicy.TERMINATE,
                execution_timeout=timedelta(hours=24),
            )
            self._completed[node.address] = result

        except Exception as exc:
            workflow.logger.error(f"Node {node.address} failed: {exc}")
            self._failed[node.address] = str(exc)
