"""Integration tests for graph invalidation with NodeInfo and GraphTraversalWorkflow.

Tests the integration between graph diff results, NodeInfo flags, and
the workflow's skip logic. Uses real dataclasses (no mocks for data structures).
"""

import pytest

from fides.api.task.temporal.converters import (
    GraphPlan,
    GraphTraversalParams,
    GraphTraversalResult,
    NodeExecutionParams,
    NodeExecutionResult,
    NodeInfo,
    TraversalPhase,
)
from fides.api.task.temporal.graph_diff import (
    DirtyReason,
    GraphDiffResult,
    NodeDiffResult,
    NodeStatus,
)


class TestNodeInfoDirtyFlags:
    """Test that NodeInfo properly carries dirty state from diff results."""

    def test_clean_completed_node(self):
        node = NodeInfo(
            address="ds:users",
            already_completed=True,
            is_dirty=False,
        )
        assert node.already_completed
        assert not node.is_dirty

    def test_dirty_completed_node(self):
        node = NodeInfo(
            address="ds:users",
            already_completed=False,
            is_dirty=True,
            dirty_reasons=["edges_changed", "upstream_dirty"],
        )
        assert not node.already_completed
        assert node.is_dirty
        assert "edges_changed" in node.dirty_reasons

    def test_added_node(self):
        node = NodeInfo(
            address="ds:new_table",
            already_completed=False,
            is_dirty=True,
            dirty_reasons=["node_added"],
        )
        assert node.is_dirty

    def test_default_values(self):
        node = NodeInfo(address="ds:users")
        assert not node.is_dirty
        assert node.dirty_reasons == []
        assert not node.already_completed
        assert not node.already_skipped


class TestBuildGraphPlanWithDiff:
    """Test that _build_graph_plan_from_tasks correctly integrates diff results."""

    def _make_graph_plan_with_diff(
        self, tasks_data: list[dict], diff_result: GraphDiffResult | None
    ) -> GraphPlan:
        """Build a GraphPlan manually (simulating what _build_graph_plan_from_tasks does)."""
        plan = GraphPlan(
            privacy_request_id="test-pr-id",
            phase=TraversalPhase.ACCESS,
        )

        for task in tasks_data:
            addr = task["address"]
            completed = task.get("status") == "complete"
            skipped = task.get("status") == "skipped"

            is_dirty = False
            dirty_reasons: list[str] = []
            if diff_result and addr in diff_result.nodes:
                node_diff = diff_result.nodes[addr]
                is_dirty = node_diff.status in (NodeStatus.DIRTY, NodeStatus.ADDED)
                dirty_reasons = [r.value for r in node_diff.reasons]

            should_skip = (completed or skipped) and not is_dirty

            plan.nodes[addr] = NodeInfo(
                address=addr,
                upstream=task.get("upstream", []),
                downstream=task.get("downstream", []),
                request_task_id=task.get("id", addr),
                already_completed=should_skip and completed,
                already_skipped=should_skip and skipped,
                is_dirty=is_dirty,
                dirty_reasons=dirty_reasons,
            )

        return plan

    def test_first_run_no_diff(self):
        """First run: no diff, all nodes pending."""
        tasks = [
            {"address": "ds:a", "status": "pending", "id": "1"},
            {"address": "ds:b", "status": "pending", "id": "2"},
        ]
        plan = self._make_graph_plan_with_diff(tasks, None)
        assert not plan.nodes["ds:a"].already_completed
        assert not plan.nodes["ds:a"].is_dirty
        assert not plan.nodes["ds:b"].already_completed

    def test_reprocess_clean_nodes_skipped(self):
        """Reprocess with no changes: completed nodes should be skipped."""
        diff = GraphDiffResult()
        diff.nodes["ds:a"] = NodeDiffResult(address="ds:a", status=NodeStatus.CLEAN)
        diff.nodes["ds:b"] = NodeDiffResult(address="ds:b", status=NodeStatus.CLEAN)

        tasks = [
            {"address": "ds:a", "status": "complete", "id": "1"},
            {"address": "ds:b", "status": "complete", "id": "2"},
        ]
        plan = self._make_graph_plan_with_diff(tasks, diff)
        assert plan.nodes["ds:a"].already_completed
        assert not plan.nodes["ds:a"].is_dirty
        assert plan.nodes["ds:b"].already_completed

    def test_reprocess_dirty_nodes_not_skipped(self):
        """Reprocess with changes: dirty completed nodes should NOT be skipped."""
        diff = GraphDiffResult()
        diff.nodes["ds:a"] = NodeDiffResult(
            address="ds:a",
            status=NodeStatus.DIRTY,
            reasons=[DirtyReason.EDGES_CHANGED],
        )
        diff.nodes["ds:b"] = NodeDiffResult(address="ds:b", status=NodeStatus.CLEAN)

        tasks = [
            {"address": "ds:a", "status": "complete", "id": "1"},
            {"address": "ds:b", "status": "complete", "id": "2"},
        ]
        plan = self._make_graph_plan_with_diff(tasks, diff)
        assert not plan.nodes["ds:a"].already_completed
        assert plan.nodes["ds:a"].is_dirty
        assert plan.nodes["ds:b"].already_completed
        assert not plan.nodes["ds:b"].is_dirty

    def test_reprocess_added_node(self):
        """Added node should be marked dirty."""
        diff = GraphDiffResult()
        diff.nodes["ds:a"] = NodeDiffResult(address="ds:a", status=NodeStatus.CLEAN)
        diff.nodes["ds:new"] = NodeDiffResult(
            address="ds:new",
            status=NodeStatus.ADDED,
            reasons=[DirtyReason.NODE_ADDED],
        )

        tasks = [
            {"address": "ds:a", "status": "complete", "id": "1"},
            {"address": "ds:new", "status": "pending", "id": "2"},
        ]
        plan = self._make_graph_plan_with_diff(tasks, diff)
        assert plan.nodes["ds:a"].already_completed
        assert plan.nodes["ds:new"].is_dirty
        assert not plan.nodes["ds:new"].already_completed

    def test_reprocess_errored_then_dirty(self):
        """Error + edge change: both reasons should appear."""
        diff = GraphDiffResult()
        diff.nodes["ds:a"] = NodeDiffResult(
            address="ds:a",
            status=NodeStatus.DIRTY,
            reasons=[DirtyReason.PREVIOUSLY_ERRORED, DirtyReason.EDGES_CHANGED],
        )

        tasks = [{"address": "ds:a", "status": "error", "id": "1"}]
        plan = self._make_graph_plan_with_diff(tasks, diff)
        assert plan.nodes["ds:a"].is_dirty
        assert "previously_errored" in plan.nodes["ds:a"].dirty_reasons
        assert "edges_changed" in plan.nodes["ds:a"].dirty_reasons

    def test_reprocess_mixed_clean_dirty_orphan(self):
        """Mixed scenario: clean, dirty, and orphan nodes."""
        diff = GraphDiffResult()
        diff.nodes["ds:a"] = NodeDiffResult(address="ds:a", status=NodeStatus.CLEAN)
        diff.nodes["ds:b"] = NodeDiffResult(
            address="ds:b",
            status=NodeStatus.DIRTY,
            reasons=[DirtyReason.FIELDS_CHANGED],
        )
        diff.nodes["ds:c"] = NodeDiffResult(
            address="ds:c",
            status=NodeStatus.DIRTY,
            reasons=[DirtyReason.UPSTREAM_DIRTY],
        )

        tasks = [
            {"address": "ds:a", "status": "complete", "id": "1"},
            {"address": "ds:b", "status": "complete", "id": "2"},
            {"address": "ds:c", "status": "complete", "id": "3"},
        ]
        plan = self._make_graph_plan_with_diff(tasks, diff)
        assert plan.nodes["ds:a"].already_completed
        assert not plan.nodes["ds:a"].is_dirty
        assert not plan.nodes["ds:b"].already_completed
        assert plan.nodes["ds:b"].is_dirty
        assert not plan.nodes["ds:c"].already_completed
        assert plan.nodes["ds:c"].is_dirty


class TestWorkflowSkipLogic:
    """Test the skip logic that GraphTraversalWorkflow._execute_node uses."""

    def _should_skip(self, node: NodeInfo) -> bool:
        """Replicates the skip check from GraphTraversalWorkflow._execute_node."""
        return (node.already_completed or node.already_skipped) and not node.is_dirty

    def test_skip_clean_completed(self):
        node = NodeInfo(address="ds:a", already_completed=True, is_dirty=False)
        assert self._should_skip(node)

    def test_skip_clean_skipped(self):
        node = NodeInfo(address="ds:a", already_skipped=True, is_dirty=False)
        assert self._should_skip(node)

    def test_no_skip_dirty_completed(self):
        node = NodeInfo(address="ds:a", already_completed=False, is_dirty=True)
        assert not self._should_skip(node)

    def test_no_skip_pending(self):
        node = NodeInfo(address="ds:a", already_completed=False, is_dirty=False)
        assert not self._should_skip(node)

    def test_no_skip_dirty_even_if_marked_completed(self):
        """Edge case: if somehow both already_completed and is_dirty are True."""
        node = NodeInfo(address="ds:a", already_completed=True, is_dirty=True)
        assert not self._should_skip(node)


class TestEndToEndDiffToGraphPlan:
    """End-to-end: from diff result to GraphPlan to skip decisions."""

    def test_tc15_simple_retry(self):
        """TC-15: No config changes, A complete, B and C errored."""
        from fides.api.task.temporal.graph_diff import (
            NewNodeSnapshot,
            OldNodeSnapshot,
            compute_graph_diff,
        )

        old = {
            "ds:a": OldNodeSnapshot(
                address="ds:a",
                status="complete",
                collection_json={"fields": [{"name": "id"}]},
                connection_key="c",
                request_task_id="1",
            ),
            "ds:b": OldNodeSnapshot(
                address="ds:b",
                status="error",
                collection_json={"fields": [{"name": "id"}]},
                connection_key="c",
                request_task_id="2",
            ),
            "ds:c": OldNodeSnapshot(
                address="ds:c",
                status="error",
                collection_json={"fields": [{"name": "id"}]},
                connection_key="c",
                request_task_id="3",
            ),
        }
        new = {
            "ds:a": NewNodeSnapshot(
                address="ds:a",
                collection_json={"fields": [{"name": "id"}]},
                connection_key="c",
            ),
            "ds:b": NewNodeSnapshot(
                address="ds:b",
                collection_json={"fields": [{"name": "id"}]},
                connection_key="c",
            ),
            "ds:c": NewNodeSnapshot(
                address="ds:c",
                collection_json={"fields": [{"name": "id"}]},
                connection_key="c",
            ),
        }

        diff = compute_graph_diff(old, new)

        tasks = [
            {"address": "ds:a", "status": "complete"},
            {"address": "ds:b", "status": "error"},
            {"address": "ds:c", "status": "error"},
        ]
        plan = GraphPlan(privacy_request_id="pr", phase=TraversalPhase.ACCESS)
        for t in tasks:
            addr = t["address"]
            completed = t["status"] == "complete"
            nd = diff.nodes[addr]
            is_dirty = nd.status in (NodeStatus.DIRTY, NodeStatus.ADDED)
            should_skip = completed and not is_dirty
            plan.nodes[addr] = NodeInfo(
                address=addr,
                already_completed=should_skip,
                is_dirty=is_dirty,
                dirty_reasons=[r.value for r in nd.reasons],
            )

        assert plan.nodes["ds:a"].already_completed
        assert not plan.nodes["ds:a"].is_dirty

        assert not plan.nodes["ds:b"].already_completed
        assert plan.nodes["ds:b"].is_dirty

        assert not plan.nodes["ds:c"].already_completed
        assert plan.nodes["ds:c"].is_dirty


class TestErasureDiffFromAccessState:
    """Test build_erasure_diff_from_access_state propagation logic."""

    def _mock_task(self, address: str, status: str, task_id: str = ""):
        """Create a minimal object mimicking a RequestTask."""
        from types import SimpleNamespace

        from fides.api.schemas.privacy_request import ExecutionLogStatus

        status_map = {
            "complete": ExecutionLogStatus.complete,
            "error": ExecutionLogStatus.error,
            "pending": ExecutionLogStatus.pending,
            "skipped": ExecutionLogStatus.skipped,
            "in_processing": ExecutionLogStatus.in_processing,
        }
        return SimpleNamespace(
            collection_address=address,
            status=status_map[status],
            id=task_id or address,
        )

    def test_no_changes(self):
        from fides.api.task.temporal.activities.graph_construction import (
            build_erasure_diff_from_access_state,
        )

        access = {
            "ds:a": self._mock_task("ds:a", "complete"),
            "ds:b": self._mock_task("ds:b", "complete"),
        }
        erasure_tasks = [
            self._mock_task("ds:a", "complete", "e1"),
            self._mock_task("ds:b", "complete", "e2"),
        ]
        result = build_erasure_diff_from_access_state(access, erasure_tasks)
        assert result is None

    def test_access_pending_makes_erasure_dirty(self):
        from fides.api.task.temporal.activities.graph_construction import (
            build_erasure_diff_from_access_state,
        )

        access = {
            "ds:a": self._mock_task("ds:a", "pending"),
            "ds:b": self._mock_task("ds:b", "complete"),
        }
        erasure_tasks = [
            self._mock_task("ds:a", "complete", "e1"),
            self._mock_task("ds:b", "complete", "e2"),
        ]
        result = build_erasure_diff_from_access_state(access, erasure_tasks)
        assert result is not None
        assert result.nodes["ds:a"].status == NodeStatus.DIRTY
        assert DirtyReason.UPSTREAM_DIRTY in result.nodes["ds:a"].reasons
        assert result.nodes["ds:b"].status == NodeStatus.CLEAN

    def test_erasure_error_is_dirty(self):
        from fides.api.task.temporal.activities.graph_construction import (
            build_erasure_diff_from_access_state,
        )

        access = {
            "ds:a": self._mock_task("ds:a", "complete"),
        }
        erasure_tasks = [
            self._mock_task("ds:a", "error", "e1"),
        ]
        result = build_erasure_diff_from_access_state(access, erasure_tasks)
        assert result is not None
        assert result.nodes["ds:a"].status == NodeStatus.DIRTY
        assert DirtyReason.PREVIOUSLY_ERRORED in result.nodes["ds:a"].reasons

    def test_both_access_pending_and_erasure_error(self):
        from fides.api.task.temporal.activities.graph_construction import (
            build_erasure_diff_from_access_state,
        )

        access = {
            "ds:a": self._mock_task("ds:a", "pending"),
        }
        erasure_tasks = [
            self._mock_task("ds:a", "error", "e1"),
        ]
        result = build_erasure_diff_from_access_state(access, erasure_tasks)
        assert result is not None
        node = result.nodes["ds:a"]
        assert node.status == NodeStatus.DIRTY
        assert DirtyReason.PREVIOUSLY_ERRORED in node.reasons
        assert DirtyReason.UPSTREAM_DIRTY in node.reasons


class TestConsentDiff:
    """Test build_consent_diff logic."""

    def _mock_task(self, address: str, status: str, task_id: str = ""):
        from types import SimpleNamespace

        from fides.api.schemas.privacy_request import ExecutionLogStatus

        status_map = {
            "complete": ExecutionLogStatus.complete,
            "error": ExecutionLogStatus.error,
            "pending": ExecutionLogStatus.pending,
            "skipped": ExecutionLogStatus.skipped,
        }
        return SimpleNamespace(
            collection_address=address,
            status=status_map[status],
            id=task_id or address,
        )

    def test_no_changes(self):
        from fides.api.task.temporal.activities.graph_construction import (
            build_consent_diff,
        )

        tasks = [
            self._mock_task("ds:a", "complete", "c1"),
            self._mock_task("ds:b", "complete", "c2"),
        ]
        result = build_consent_diff(tasks, {"ds:a", "ds:b"})
        assert result is None

    def test_node_added(self):
        from fides.api.task.temporal.activities.graph_construction import (
            build_consent_diff,
        )

        tasks = [self._mock_task("ds:a", "complete", "c1")]
        result = build_consent_diff(tasks, {"ds:a", "ds:new"})
        assert result is not None
        assert result.nodes["ds:a"].status == NodeStatus.CLEAN
        assert result.nodes["ds:new"].status == NodeStatus.ADDED

    def test_node_removed(self):
        from fides.api.task.temporal.activities.graph_construction import (
            build_consent_diff,
        )

        tasks = [
            self._mock_task("ds:a", "complete", "c1"),
            self._mock_task("ds:old", "complete", "c2"),
        ]
        result = build_consent_diff(tasks, {"ds:a"})
        assert result is not None
        assert result.nodes["ds:a"].status == NodeStatus.CLEAN
        assert result.nodes["ds:old"].status == NodeStatus.ORPHAN

    def test_errored_node_dirty(self):
        from fides.api.task.temporal.activities.graph_construction import (
            build_consent_diff,
        )

        tasks = [self._mock_task("ds:a", "error", "c1")]
        result = build_consent_diff(tasks, {"ds:a"})
        assert result is not None
        assert result.nodes["ds:a"].status == NodeStatus.DIRTY
        assert DirtyReason.PREVIOUSLY_ERRORED in result.nodes["ds:a"].reasons

    def test_mixed_scenario(self):
        from fides.api.task.temporal.activities.graph_construction import (
            build_consent_diff,
        )

        tasks = [
            self._mock_task("ds:a", "complete", "c1"),
            self._mock_task("ds:b", "error", "c2"),
            self._mock_task("ds:old", "complete", "c3"),
        ]
        result = build_consent_diff(tasks, {"ds:a", "ds:b", "ds:new"})
        assert result is not None
        assert result.nodes["ds:a"].status == NodeStatus.CLEAN
        assert result.nodes["ds:b"].status == NodeStatus.DIRTY
        assert result.nodes["ds:old"].status == NodeStatus.ORPHAN
        assert result.nodes["ds:new"].status == NodeStatus.ADDED


class TestCleanupAsyncState:
    """Test cleanup_async_state for polling and callback tasks."""

    def test_polling_sub_requests_marked_skipped(self):
        from types import SimpleNamespace
        from unittest.mock import MagicMock

        from fides.api.task.temporal.activities.graph_construction import (
            cleanup_async_state,
        )

        sub1 = SimpleNamespace(status="pending")
        sub2 = SimpleNamespace(status="complete")
        sub3 = SimpleNamespace(status="in_processing")

        task = SimpleNamespace(
            async_type=SimpleNamespace(value="polling"),
            sub_requests=[sub1, sub2, sub3],
            collection_address="ds:polling_node",
        )

        session = MagicMock()
        cleanup_async_state(session, task)

        assert sub1.status == "skipped"
        assert sub2.status == "complete"
        assert sub3.status == "skipped"
        assert session.add.call_count == 2

    def test_no_sub_requests(self):
        from types import SimpleNamespace
        from unittest.mock import MagicMock

        from fides.api.task.temporal.activities.graph_construction import (
            cleanup_async_state,
        )

        task = SimpleNamespace(
            async_type=SimpleNamespace(value="polling"),
            sub_requests=[],
            collection_address="ds:polling_node",
        )

        session = MagicMock()
        cleanup_async_state(session, task)
        session.add.assert_not_called()

    def test_callback_task_noop(self):
        from types import SimpleNamespace
        from unittest.mock import MagicMock

        from fides.api.task.temporal.activities.graph_construction import (
            cleanup_async_state,
        )

        task = SimpleNamespace(
            async_type=SimpleNamespace(value="callback"),
            sub_requests=None,
            collection_address="ds:callback_node",
        )

        session = MagicMock()
        cleanup_async_state(session, task)
        session.add.assert_not_called()

    def test_regular_task_noop(self):
        from types import SimpleNamespace
        from unittest.mock import MagicMock

        from fides.api.task.temporal.activities.graph_construction import (
            cleanup_async_state,
        )

        task = SimpleNamespace(
            async_type=None,
            sub_requests=None,
            collection_address="ds:regular_node",
        )

        session = MagicMock()
        cleanup_async_state(session, task)
        session.add.assert_not_called()


class TestHasDirtyManualNodes:
    """Test has_dirty_manual_nodes detection of manual task addresses."""

    def test_detects_dirty_manual_node(self):
        from fides.api.task.temporal.activities.graph_construction import (
            has_dirty_manual_nodes,
        )

        diff = GraphDiffResult()
        diff.nodes["manual_conn:manual_data"] = NodeDiffResult(
            address="manual_conn:manual_data",
            status=NodeStatus.DIRTY,
            reasons=[DirtyReason.FIELDS_CHANGED],
        )

        assert has_dirty_manual_nodes(diff) is True

    def test_no_manual_nodes(self):
        from fides.api.task.temporal.activities.graph_construction import (
            has_dirty_manual_nodes,
        )

        diff = GraphDiffResult()
        diff.nodes["ds:regular"] = NodeDiffResult(
            address="ds:regular",
            status=NodeStatus.DIRTY,
            reasons=[DirtyReason.EDGES_CHANGED],
        )

        assert has_dirty_manual_nodes(diff) is False

    def test_detects_added_manual_node(self):
        from fides.api.task.temporal.activities.graph_construction import (
            has_dirty_manual_nodes,
        )

        diff = GraphDiffResult()
        diff.nodes["new_manual:manual_data"] = NodeDiffResult(
            address="new_manual:manual_data",
            status=NodeStatus.ADDED,
            reasons=[DirtyReason.NODE_ADDED],
        )

        assert has_dirty_manual_nodes(diff) is True

    def test_clean_manual_node_not_detected(self):
        from fides.api.task.temporal.activities.graph_construction import (
            has_dirty_manual_nodes,
        )

        diff = GraphDiffResult()
        diff.nodes["manual_conn:manual_data"] = NodeDiffResult(
            address="manual_conn:manual_data",
            status=NodeStatus.CLEAN,
        )

        assert has_dirty_manual_nodes(diff) is False

    def test_orphan_manual_node_not_detected(self):
        from fides.api.task.temporal.activities.graph_construction import (
            has_dirty_manual_nodes,
        )

        diff = GraphDiffResult()
        diff.nodes["manual_conn:manual_data"] = NodeDiffResult(
            address="manual_conn:manual_data",
            status=NodeStatus.ORPHAN,
        )

        assert has_dirty_manual_nodes(diff) is False

    def test_mixed_dirty_regular_and_manual(self):
        from fides.api.task.temporal.activities.graph_construction import (
            has_dirty_manual_nodes,
        )

        diff = GraphDiffResult()
        diff.nodes["ds:regular"] = NodeDiffResult(
            address="ds:regular",
            status=NodeStatus.DIRTY,
            reasons=[DirtyReason.EDGES_CHANGED],
        )
        diff.nodes["manual_conn:manual_data"] = NodeDiffResult(
            address="manual_conn:manual_data",
            status=NodeStatus.DIRTY,
            reasons=[DirtyReason.FIELDS_CHANGED],
        )

        assert has_dirty_manual_nodes(diff) is True
