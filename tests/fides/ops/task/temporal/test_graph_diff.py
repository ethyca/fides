"""Unit tests for Temporal graph diff and cascading invalidation.

Tests exercise the public compute_graph_diff interface with no DB
or Temporal dependencies.
"""

import pytest

from fides.api.task.temporal.graph_diff import (
    DirtyReason,
    GraphDiffResult,
    NewNodeSnapshot,
    NodeStatus,
    OldNodeSnapshot,
    compute_graph_diff,
)

# -- Fixtures for building test snapshots --


def _old(
    address: str,
    incoming_edges: list[tuple[str, str]] | None = None,
    outgoing_edges: list[tuple[str, str]] | None = None,
    connection_key: str = "conn_a",
    fields: list[dict] | None = None,
    status: str = "complete",
    rows_masked: int = 0,
    request_task_id: str = "",
) -> OldNodeSnapshot:
    collection_json = {
        "name": address.split(":")[-1] if ":" in address else address,
        "fields": fields or [{"name": "id"}, {"name": "email"}],
    }
    return OldNodeSnapshot(
        address=address,
        incoming_edges=incoming_edges or [],
        outgoing_edges=outgoing_edges or [],
        connection_key=connection_key,
        collection_json=collection_json,
        status=status,
        rows_masked=rows_masked,
        request_task_id=request_task_id or address,
    )


def _new(
    address: str,
    incoming_edges: list[tuple[str, str]] | None = None,
    outgoing_edges: list[tuple[str, str]] | None = None,
    connection_key: str = "conn_a",
    fields: list[dict] | None = None,
    saas_config_hash: str | None = None,
) -> NewNodeSnapshot:
    collection_json = {
        "name": address.split(":")[-1] if ":" in address else address,
        "fields": fields or [{"name": "id"}, {"name": "email"}],
    }
    return NewNodeSnapshot(
        address=address,
        incoming_edges=incoming_edges or [],
        outgoing_edges=outgoing_edges or [],
        connection_key=connection_key,
        collection_json=collection_json,
        saas_config_hash=saas_config_hash,
    )


# -- Tests through compute_graph_diff public interface --


class TestComputeGraphDiffSingleNode:
    """Test single-node diff behaviors via compute_graph_diff with one node."""

    def test_clean_when_identical(self):
        result = compute_graph_diff({"ds:a": _old("ds:a")}, {"ds:a": _new("ds:a")})
        assert result.nodes["ds:a"].status == NodeStatus.CLEAN

    def test_dirty_when_incoming_edge_added(self):
        result = compute_graph_diff(
            {"ds:a": _old("ds:a", incoming_edges=[])},
            {"ds:a": _new("ds:a", incoming_edges=[("ds:b.id", "ds:a.ref")])},
        )
        assert result.nodes["ds:a"].status == NodeStatus.DIRTY
        assert DirtyReason.EDGES_CHANGED in result.nodes["ds:a"].reasons

    def test_dirty_when_incoming_edge_removed(self):
        result = compute_graph_diff(
            {"ds:a": _old("ds:a", incoming_edges=[("ds:b.id", "ds:a.ref")])},
            {"ds:a": _new("ds:a", incoming_edges=[])},
        )
        assert result.nodes["ds:a"].status == NodeStatus.DIRTY
        assert DirtyReason.EDGES_CHANGED in result.nodes["ds:a"].reasons

    def test_clean_when_only_outgoing_edge_changes(self):
        result = compute_graph_diff(
            {"ds:a": _old("ds:a", outgoing_edges=[("ds:a.id", "ds:b.ref")])},
            {"ds:a": _new("ds:a", outgoing_edges=[("ds:a.id", "ds:c.ref")])},
        )
        assert result.nodes["ds:a"].status == NodeStatus.CLEAN

    def test_dirty_when_field_added(self):
        result = compute_graph_diff(
            {"ds:a": _old("ds:a", fields=[{"name": "id"}])},
            {"ds:a": _new("ds:a", fields=[{"name": "id"}, {"name": "email"}])},
        )
        assert result.nodes["ds:a"].status == NodeStatus.DIRTY
        assert DirtyReason.FIELDS_CHANGED in result.nodes["ds:a"].reasons

    def test_dirty_when_field_removed(self):
        result = compute_graph_diff(
            {"ds:a": _old("ds:a", fields=[{"name": "id"}, {"name": "email"}])},
            {"ds:a": _new("ds:a", fields=[{"name": "id"}])},
        )
        assert result.nodes["ds:a"].status == NodeStatus.DIRTY
        assert DirtyReason.FIELDS_CHANGED in result.nodes["ds:a"].reasons

    def test_dirty_when_connection_key_changed(self):
        result = compute_graph_diff(
            {"ds:a": _old("ds:a", connection_key="pg")},
            {"ds:a": _new("ds:a", connection_key="mysql")},
        )
        assert result.nodes["ds:a"].status == NodeStatus.DIRTY
        assert DirtyReason.CONNECTION_CHANGED in result.nodes["ds:a"].reasons

    def test_dirty_when_previously_errored(self):
        result = compute_graph_diff(
            {"ds:a": _old("ds:a", status="error")},
            {"ds:a": _new("ds:a")},
        )
        assert result.nodes["ds:a"].status == NodeStatus.DIRTY
        assert DirtyReason.PREVIOUSLY_ERRORED in result.nodes["ds:a"].reasons

    def test_dirty_when_pending(self):
        result = compute_graph_diff(
            {"ds:a": _old("ds:a", status="pending")},
            {"ds:a": _new("ds:a")},
        )
        assert result.nodes["ds:a"].status == NodeStatus.DIRTY

    def test_multiple_reasons(self):
        result = compute_graph_diff(
            {
                "ds:a": _old(
                    "ds:a",
                    status="error",
                    connection_key="old",
                    fields=[{"name": "id"}],
                )
            },
            {
                "ds:a": _new(
                    "ds:a",
                    connection_key="new",
                    fields=[{"name": "id"}, {"name": "email"}],
                )
            },
        )
        reasons = result.nodes["ds:a"].reasons
        assert DirtyReason.PREVIOUSLY_ERRORED in reasons
        assert DirtyReason.CONNECTION_CHANGED in reasons
        assert DirtyReason.FIELDS_CHANGED in reasons

    def test_field_reference_change_detected(self):
        result = compute_graph_diff(
            {
                "ds:a": _old(
                    "ds:a",
                    fields=[
                        {
                            "name": "id",
                            "references": [{"dataset": "ds", "field": "col.id"}],
                        }
                    ],
                )
            },
            {
                "ds:a": _new(
                    "ds:a",
                    fields=[
                        {
                            "name": "id",
                            "references": [{"dataset": "ds2", "field": "col.id"}],
                        }
                    ],
                )
            },
        )
        assert result.nodes["ds:a"].status == NodeStatus.DIRTY
        assert DirtyReason.FIELDS_CHANGED in result.nodes["ds:a"].reasons

    def test_masking_strategy_override_change_detected(self):
        result = compute_graph_diff(
            {"ds:a": _old("ds:a", fields=[{"name": "email"}])},
            {"ds:a": _new("ds:a", fields=[{"name": "email"}])},
        )
        assert result.nodes["ds:a"].status == NodeStatus.CLEAN

        old = _old("ds:a")
        old.collection_json["masking_strategy_override"] = {"strategy": "null"}
        new = _new("ds:a")
        new.collection_json["masking_strategy_override"] = {"strategy": "hash"}
        result = compute_graph_diff({"ds:a": old}, {"ds:a": new})
        assert result.nodes["ds:a"].status == NodeStatus.DIRTY

    def test_property_scope_change_detected(self):
        old = _old("ds:a")
        old.collection_json["property_scope"] = "IN_SCOPE"
        new = _new("ds:a")
        new.collection_json["property_scope"] = "TRAVERSAL_ONLY"
        result = compute_graph_diff({"ds:a": old}, {"ds:a": new})
        assert result.nodes["ds:a"].status == NodeStatus.DIRTY


class TestComputeGraphDiff:
    def test_no_changes(self):
        old = {"ds:users": _old("ds:users"), "ds:orders": _old("ds:orders")}
        new = {"ds:users": _new("ds:users"), "ds:orders": _new("ds:orders")}
        result = compute_graph_diff(old, new)
        assert len(result.clean_nodes) == 2
        assert len(result.dirty_nodes) == 0
        assert len(result.added_nodes) == 0
        assert len(result.orphan_nodes) == 0

    def test_node_added(self):
        old = {"ds:users": _old("ds:users")}
        new = {"ds:users": _new("ds:users"), "ds:orders": _new("ds:orders")}
        result = compute_graph_diff(old, new)
        assert "ds:orders" in result.added_nodes
        assert DirtyReason.NODE_ADDED in result.nodes["ds:orders"].reasons

    def test_node_removed(self):
        old = {"ds:users": _old("ds:users"), "ds:orders": _old("ds:orders")}
        new = {"ds:users": _new("ds:users")}
        result = compute_graph_diff(old, new)
        assert "ds:orders" in result.orphan_nodes
        assert result.nodes["ds:orders"].old_request_task_id == "ds:orders"

    def test_errored_node_dirty(self):
        old = {"ds:users": _old("ds:users", status="error")}
        new = {"ds:users": _new("ds:users")}
        result = compute_graph_diff(old, new)
        assert "ds:users" in result.dirty_nodes

    def test_nodes_needing_execution(self):
        old = {"ds:users": _old("ds:users"), "ds:old": _old("ds:old")}
        new = {
            "ds:users": _new("ds:users", fields=[{"name": "new_field"}]),
            "ds:new": _new("ds:new"),
        }
        result = compute_graph_diff(old, new)
        needs_exec = result.nodes_needing_execution
        assert "ds:users" in needs_exec
        assert "ds:new" in needs_exec
        assert "ds:old" not in needs_exec

    def test_summary(self):
        old = {"ds:a": _old("ds:a", status="error")}
        new = {"ds:a": _new("ds:a"), "ds:b": _new("ds:b")}
        result = compute_graph_diff(old, new)
        summary = result.to_summary()
        assert summary["dirty"] == 1
        assert summary["added"] == 1
        assert summary["orphan"] == 0


# -- Cascade invalidation tests via compute_graph_diff --


class TestCascadeDirty:
    """Test downstream cascade through compute_graph_diff.

    To trigger cascade, make root node dirty via a field change,
    then verify downstream nodes get UPSTREAM_DIRTY.
    """

    def test_cascade_from_dirty_root(self):
        """A(dirty via field change) → B → C: B and C get UPSTREAM_DIRTY."""
        old = {
            "ds:a": _old(
                "ds:a",
                fields=[{"name": "id"}],
                outgoing_edges=[("ds:a.id", "ds:b.user_id")],
            ),
            "ds:b": _old(
                "ds:b",
                incoming_edges=[("ds:a.id", "ds:b.user_id")],
                outgoing_edges=[("ds:b.id", "ds:c.order_id")],
            ),
            "ds:c": _old("ds:c", incoming_edges=[("ds:b.id", "ds:c.order_id")]),
        }
        new = {
            "ds:a": _new(
                "ds:a",
                fields=[{"name": "id"}, {"name": "new"}],
                outgoing_edges=[("ds:a.id", "ds:b.user_id")],
            ),
            "ds:b": _new(
                "ds:b",
                incoming_edges=[("ds:a.id", "ds:b.user_id")],
                outgoing_edges=[("ds:b.id", "ds:c.order_id")],
            ),
            "ds:c": _new("ds:c", incoming_edges=[("ds:b.id", "ds:c.order_id")]),
        }
        result = compute_graph_diff(old, new)
        assert result.nodes["ds:a"].status == NodeStatus.DIRTY
        assert DirtyReason.FIELDS_CHANGED in result.nodes["ds:a"].reasons
        assert result.nodes["ds:b"].status == NodeStatus.DIRTY
        assert DirtyReason.UPSTREAM_DIRTY in result.nodes["ds:b"].reasons
        assert result.nodes["ds:c"].status == NodeStatus.DIRTY
        assert DirtyReason.UPSTREAM_DIRTY in result.nodes["ds:c"].reasons

    def test_cascade_from_middle(self):
        """A clean, B(dirty via error), C gets cascade."""
        old = {
            "ds:a": _old("ds:a", outgoing_edges=[("ds:a.id", "ds:b.ref")]),
            "ds:b": _old(
                "ds:b",
                status="error",
                incoming_edges=[("ds:a.id", "ds:b.ref")],
                outgoing_edges=[("ds:b.id", "ds:c.ref")],
            ),
            "ds:c": _old("ds:c", incoming_edges=[("ds:b.id", "ds:c.ref")]),
        }
        new = {
            "ds:a": _new("ds:a", outgoing_edges=[("ds:a.id", "ds:b.ref")]),
            "ds:b": _new(
                "ds:b",
                incoming_edges=[("ds:a.id", "ds:b.ref")],
                outgoing_edges=[("ds:b.id", "ds:c.ref")],
            ),
            "ds:c": _new("ds:c", incoming_edges=[("ds:b.id", "ds:c.ref")]),
        }
        result = compute_graph_diff(old, new)
        assert result.nodes["ds:a"].status == NodeStatus.CLEAN
        assert result.nodes["ds:b"].status == NodeStatus.DIRTY
        assert result.nodes["ds:c"].status == NodeStatus.DIRTY

    def test_no_cascade_when_all_clean(self):
        old = {
            "ds:a": _old("ds:a", outgoing_edges=[("ds:a.id", "ds:b.ref")]),
            "ds:b": _old(
                "ds:b",
                incoming_edges=[("ds:a.id", "ds:b.ref")],
                outgoing_edges=[("ds:b.id", "ds:c.ref")],
            ),
            "ds:c": _old("ds:c", incoming_edges=[("ds:b.id", "ds:c.ref")]),
        }
        new = {
            "ds:a": _new("ds:a", outgoing_edges=[("ds:a.id", "ds:b.ref")]),
            "ds:b": _new(
                "ds:b",
                incoming_edges=[("ds:a.id", "ds:b.ref")],
                outgoing_edges=[("ds:b.id", "ds:c.ref")],
            ),
            "ds:c": _new("ds:c", incoming_edges=[("ds:b.id", "ds:c.ref")]),
        }
        result = compute_graph_diff(old, new)
        assert all(n.status == NodeStatus.CLEAN for n in result.nodes.values())

    def test_cascade_independent_subtrees(self):
        """A(dirty)→B and C→D. Only A's subtree cascades."""
        old = {
            "ds:a": _old(
                "ds:a",
                fields=[{"name": "id"}],
                outgoing_edges=[("ds:a.id", "ds:b.ref")],
            ),
            "ds:b": _old("ds:b", incoming_edges=[("ds:a.id", "ds:b.ref")]),
            "ds:c": _old("ds:c", outgoing_edges=[("ds:c.id", "ds:d.ref")]),
            "ds:d": _old("ds:d", incoming_edges=[("ds:c.id", "ds:d.ref")]),
        }
        new = {
            "ds:a": _new(
                "ds:a",
                fields=[{"name": "id"}, {"name": "new"}],
                outgoing_edges=[("ds:a.id", "ds:b.ref")],
            ),
            "ds:b": _new("ds:b", incoming_edges=[("ds:a.id", "ds:b.ref")]),
            "ds:c": _new("ds:c", outgoing_edges=[("ds:c.id", "ds:d.ref")]),
            "ds:d": _new("ds:d", incoming_edges=[("ds:c.id", "ds:d.ref")]),
        }
        result = compute_graph_diff(old, new)
        assert result.nodes["ds:a"].status == NodeStatus.DIRTY
        assert result.nodes["ds:b"].status == NodeStatus.DIRTY
        assert result.nodes["ds:c"].status == NodeStatus.CLEAN
        assert result.nodes["ds:d"].status == NodeStatus.CLEAN

    def test_cascade_diamond_dependency(self):
        """A(dirty)→B, A→C, B→D, C→D. All cascade."""
        old = {
            "ds:a": _old(
                "ds:a",
                fields=[{"name": "id"}],
                outgoing_edges=[
                    ("ds:a.id", "ds:b.user_id"),
                    ("ds:a.id", "ds:c.user_id"),
                ],
            ),
            "ds:b": _old(
                "ds:b",
                incoming_edges=[("ds:a.id", "ds:b.user_id")],
                outgoing_edges=[("ds:b.id", "ds:d.order_id")],
            ),
            "ds:c": _old(
                "ds:c",
                incoming_edges=[("ds:a.id", "ds:c.user_id")],
                outgoing_edges=[("ds:c.ref", "ds:d.ref")],
            ),
            "ds:d": _old(
                "ds:d",
                incoming_edges=[("ds:b.id", "ds:d.order_id"), ("ds:c.ref", "ds:d.ref")],
            ),
        }
        new = {
            "ds:a": _new(
                "ds:a",
                fields=[{"name": "id"}, {"name": "new"}],
                outgoing_edges=[
                    ("ds:a.id", "ds:b.user_id"),
                    ("ds:a.id", "ds:c.user_id"),
                ],
            ),
            "ds:b": _new(
                "ds:b",
                incoming_edges=[("ds:a.id", "ds:b.user_id")],
                outgoing_edges=[("ds:b.id", "ds:d.order_id")],
            ),
            "ds:c": _new(
                "ds:c",
                incoming_edges=[("ds:a.id", "ds:c.user_id")],
                outgoing_edges=[("ds:c.ref", "ds:d.ref")],
            ),
            "ds:d": _new(
                "ds:d",
                incoming_edges=[("ds:b.id", "ds:d.order_id"), ("ds:c.ref", "ds:d.ref")],
            ),
        }
        result = compute_graph_diff(old, new)
        assert all(n.status == NodeStatus.DIRTY for n in result.nodes.values())


# -- Test scenarios from the invalidation plan --


class TestInvalidationScenarios:
    def test_tc1_connection_disabled(self):
        """TC-1: Connection disabled. B removed, A clean, C loses upstream."""
        old = {
            "ds:a": _old("ds:a", outgoing_edges=[("ds:a.id", "ds:b.user_id")]),
            "ds:b": _old(
                "ds:b",
                incoming_edges=[("ds:a.id", "ds:b.user_id")],
                outgoing_edges=[("ds:b.id", "ds:c.ref")],
            ),
            "ds:c": _old("ds:c", incoming_edges=[("ds:b.id", "ds:c.ref")]),
        }
        new = {
            "ds:a": _new("ds:a"),
            "ds:c": _new("ds:c"),
        }
        result = compute_graph_diff(old, new)
        assert result.nodes["ds:a"].status == NodeStatus.CLEAN
        assert result.nodes["ds:b"].status == NodeStatus.ORPHAN
        assert result.nodes["ds:c"].status == NodeStatus.DIRTY
        assert DirtyReason.EDGES_CHANGED in result.nodes["ds:c"].reasons

    def test_tc2_connection_reenabled(self):
        """TC-2: B re-enabled. A clean, B added, C dirty (gained upstream)."""
        old = {
            "ds:a": _old("ds:a"),
            "ds:c": _old("ds:c"),
        }
        new = {
            "ds:a": _new("ds:a", outgoing_edges=[("ds:a.id", "ds:b.user_id")]),
            "ds:b": _new(
                "ds:b",
                incoming_edges=[("ds:a.id", "ds:b.user_id")],
                outgoing_edges=[("ds:b.id", "ds:c.ref")],
            ),
            "ds:c": _new("ds:c", incoming_edges=[("ds:b.id", "ds:c.ref")]),
        }
        result = compute_graph_diff(old, new)
        assert result.nodes["ds:a"].status == NodeStatus.CLEAN
        assert result.nodes["ds:b"].status == NodeStatus.ADDED
        assert result.nodes["ds:c"].status == NodeStatus.DIRTY
        assert DirtyReason.EDGES_CHANGED in result.nodes["ds:c"].reasons

    def test_tc3_field_reference_added(self):
        """TC-3: Field reference added between previously independent nodes.
        A gains outgoing edge (clean - its data unchanged). B gains incoming (dirty)."""
        old = {
            "ds:a": _old("ds:a"),
            "ds:b": _old("ds:b"),
        }
        new = {
            "ds:a": _new("ds:a", outgoing_edges=[("ds:a.email", "ds:b.user_email")]),
            "ds:b": _new("ds:b", incoming_edges=[("ds:a.email", "ds:b.user_email")]),
        }
        result = compute_graph_diff(old, new)
        assert result.nodes["ds:a"].status == NodeStatus.CLEAN
        assert result.nodes["ds:b"].status == NodeStatus.DIRTY
        assert DirtyReason.EDGES_CHANGED in result.nodes["ds:b"].reasons

    def test_tc5_field_added(self):
        """TC-5: Field added to collection."""
        old = {"ds:a": _old("ds:a", fields=[{"name": "id"}, {"name": "email"}])}
        new = {
            "ds:a": _new(
                "ds:a", fields=[{"name": "id"}, {"name": "email"}, {"name": "phone"}]
            )
        }
        result = compute_graph_diff(old, new)
        assert result.nodes["ds:a"].status == NodeStatus.DIRTY
        assert DirtyReason.FIELDS_CHANGED in result.nodes["ds:a"].reasons

    def test_tc13_connection_key_changed(self):
        """TC-13: Collection moved to different connection."""
        old = {"ds:users": _old("ds:users", connection_key="postgres_a")}
        new = {"ds:users": _new("ds:users", connection_key="postgres_b")}
        result = compute_graph_diff(old, new)
        assert result.nodes["ds:users"].status == NodeStatus.DIRTY
        assert DirtyReason.CONNECTION_CHANGED in result.nodes["ds:users"].reasons

    def test_tc15_no_changes_retry(self):
        """TC-15: No config changes, just retrying errored tasks."""
        old = {
            "ds:a": _old("ds:a"),
            "ds:b": _old("ds:b", status="error"),
            "ds:c": _old("ds:c", status="error"),
        }
        new = {
            "ds:a": _new("ds:a"),
            "ds:b": _new("ds:b"),
            "ds:c": _new("ds:c"),
        }
        result = compute_graph_diff(old, new)
        assert result.nodes["ds:a"].status == NodeStatus.CLEAN
        assert result.nodes["ds:b"].status == NodeStatus.DIRTY
        assert DirtyReason.PREVIOUSLY_ERRORED in result.nodes["ds:b"].reasons
        assert result.nodes["ds:c"].status == NodeStatus.DIRTY

    def test_tc17_independent_subtrees(self):
        """TC-17: Two independent subtrees, one has field change."""
        old = {
            "ds:a": _old("ds:a", outgoing_edges=[("ds:a.id", "ds:b.ref")]),
            "ds:b": _old(
                "ds:b",
                incoming_edges=[("ds:a.id", "ds:b.ref")],
                outgoing_edges=[("ds:b.id", "ds:c.ref")],
            ),
            "ds:c": _old(
                "ds:c", incoming_edges=[("ds:b.id", "ds:c.ref")], status="error"
            ),
            "ds:d": _old(
                "ds:d",
                outgoing_edges=[("ds:d.id", "ds:e.ref")],
                fields=[{"name": "id"}],
            ),
            "ds:e": _old(
                "ds:e",
                incoming_edges=[("ds:d.id", "ds:e.ref")],
                outgoing_edges=[("ds:e.id", "ds:f.ref")],
            ),
            "ds:f": _old("ds:f", incoming_edges=[("ds:e.id", "ds:f.ref")]),
        }
        new = {
            "ds:a": _new("ds:a", outgoing_edges=[("ds:a.id", "ds:b.ref")]),
            "ds:b": _new(
                "ds:b",
                incoming_edges=[("ds:a.id", "ds:b.ref")],
                outgoing_edges=[("ds:b.id", "ds:c.ref")],
            ),
            "ds:c": _new("ds:c", incoming_edges=[("ds:b.id", "ds:c.ref")]),
            "ds:d": _new(
                "ds:d",
                outgoing_edges=[("ds:d.id", "ds:e.ref")],
                fields=[{"name": "id"}, {"name": "new_field"}],
            ),
            "ds:e": _new(
                "ds:e",
                incoming_edges=[("ds:d.id", "ds:e.ref")],
                outgoing_edges=[("ds:e.id", "ds:f.ref")],
            ),
            "ds:f": _new("ds:f", incoming_edges=[("ds:e.id", "ds:f.ref")]),
        }
        result = compute_graph_diff(old, new)
        assert result.nodes["ds:a"].status == NodeStatus.CLEAN
        assert result.nodes["ds:b"].status == NodeStatus.CLEAN
        assert result.nodes["ds:c"].status == NodeStatus.DIRTY
        assert DirtyReason.PREVIOUSLY_ERRORED in result.nodes["ds:c"].reasons
        assert result.nodes["ds:d"].status == NodeStatus.DIRTY
        assert DirtyReason.FIELDS_CHANGED in result.nodes["ds:d"].reasons
        assert result.nodes["ds:e"].status == NodeStatus.DIRTY
        assert DirtyReason.UPSTREAM_DIRTY in result.nodes["ds:e"].reasons
        assert result.nodes["ds:f"].status == NodeStatus.DIRTY
        assert DirtyReason.UPSTREAM_DIRTY in result.nodes["ds:f"].reasons

    def test_tc19_bidirectional_to_directional(self):
        """TC-19: Bidirectional edge changed to directional.
        A loses incoming from B (dirty). B is dirty via cascade (upstream A changed)."""
        old = {
            "ds:a": _old(
                "ds:a",
                incoming_edges=[("ds:b.id", "ds:a.ref")],
                outgoing_edges=[("ds:a.id", "ds:b.ref")],
            ),
            "ds:b": _old(
                "ds:b",
                incoming_edges=[("ds:a.id", "ds:b.ref")],
                outgoing_edges=[("ds:b.id", "ds:a.ref")],
            ),
        }
        new = {
            "ds:a": _new("ds:a", outgoing_edges=[("ds:a.id", "ds:b.ref")]),
            "ds:b": _new("ds:b", incoming_edges=[("ds:a.id", "ds:b.ref")]),
        }
        result = compute_graph_diff(old, new)
        assert result.nodes["ds:a"].status == NodeStatus.DIRTY
        assert DirtyReason.EDGES_CHANGED in result.nodes["ds:a"].reasons
        assert result.nodes["ds:b"].status == NodeStatus.DIRTY
        assert DirtyReason.UPSTREAM_DIRTY in result.nodes["ds:b"].reasons
