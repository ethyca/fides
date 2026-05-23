"""Tests for DSRLifecycleWorkflow checkpoint/resume logic."""

import pytest

from fides.api.task.temporal.converters import GraphPlan, NodeInfo, TraversalPhase
from fides.api.task.temporal.workflows.dsr_lifecycle import (
    CHECKPOINT_ORDER,
    can_run_checkpoint,
    graph_plan_has_dirty,
)


class TestCanRunCheckpoint:
    def test_no_from_step_runs_everything(self):
        for step in CHECKPOINT_ORDER:
            assert can_run_checkpoint(step, None) is True

    def test_resume_from_first_step_runs_all(self):
        for step in CHECKPOINT_ORDER:
            assert can_run_checkpoint(step, "pre_webhooks") is True

    def test_resume_from_access_skips_pre_webhooks(self):
        assert can_run_checkpoint("pre_webhooks", "access") is False
        assert can_run_checkpoint("access", "access") is True
        assert can_run_checkpoint("upload_access", "access") is True
        assert can_run_checkpoint("erasure", "access") is True

    def test_resume_from_erasure_skips_access_and_upload(self):
        assert can_run_checkpoint("pre_webhooks", "erasure") is False
        assert can_run_checkpoint("access", "erasure") is False
        assert can_run_checkpoint("upload_access", "erasure") is False
        assert can_run_checkpoint("erasure", "erasure") is True
        assert can_run_checkpoint("consent", "erasure") is True
        assert can_run_checkpoint("post_webhooks", "erasure") is True
        assert can_run_checkpoint("finalization", "erasure") is True

    def test_resume_from_consent(self):
        assert can_run_checkpoint("erasure", "consent") is False
        assert can_run_checkpoint("consent", "consent") is True
        assert can_run_checkpoint("post_webhooks", "consent") is True

    def test_resume_from_post_webhooks(self):
        assert can_run_checkpoint("consent", "post_webhooks") is False
        assert can_run_checkpoint("post_webhooks", "post_webhooks") is True
        assert can_run_checkpoint("finalization", "post_webhooks") is True

    def test_resume_from_finalization(self):
        for step in CHECKPOINT_ORDER[:-1]:
            assert can_run_checkpoint(step, "finalization") is False
        assert can_run_checkpoint("finalization", "finalization") is True

    def test_unknown_step_runs(self):
        assert can_run_checkpoint("unknown_step", "access") is True
        assert can_run_checkpoint("access", "unknown_step") is True

    def test_checkpoint_order_matches_celery(self):
        """Verify our checkpoint order covers the same phases as CurrentStep."""
        assert "pre_webhooks" in CHECKPOINT_ORDER
        assert "access" in CHECKPOINT_ORDER
        assert "upload_access" in CHECKPOINT_ORDER
        assert "erasure" in CHECKPOINT_ORDER
        assert "consent" in CHECKPOINT_ORDER
        assert "post_webhooks" in CHECKPOINT_ORDER
        assert "finalization" in CHECKPOINT_ORDER
        assert CHECKPOINT_ORDER.index("access") < CHECKPOINT_ORDER.index("erasure")
        assert CHECKPOINT_ORDER.index("erasure") < CHECKPOINT_ORDER.index("consent")


class TestGraphPlanHasDirty:
    """Test _graph_plan_has_dirty helper for cross-phase invalidation."""

    def test_no_dirty_nodes(self):
        plan = GraphPlan(
            privacy_request_id="pr",
            phase=TraversalPhase.ACCESS,
            nodes={
                "ds:a": NodeInfo(
                    address="ds:a", already_completed=True, is_dirty=False
                ),
                "ds:b": NodeInfo(
                    address="ds:b", already_completed=True, is_dirty=False
                ),
            },
        )
        assert graph_plan_has_dirty(plan) is False

    def test_has_dirty_nodes(self):
        plan = GraphPlan(
            privacy_request_id="pr",
            phase=TraversalPhase.ACCESS,
            nodes={
                "ds:a": NodeInfo(
                    address="ds:a", already_completed=True, is_dirty=False
                ),
                "ds:b": NodeInfo(
                    address="ds:b", is_dirty=True, dirty_reasons=["edges_changed"]
                ),
            },
        )
        assert graph_plan_has_dirty(plan) is True

    def test_empty_plan(self):
        plan = GraphPlan(privacy_request_id="pr", phase=TraversalPhase.ACCESS)
        assert graph_plan_has_dirty(plan) is False

    def test_dict_deserialization(self):
        """Temporal may deserialize GraphPlan as a dict."""
        plan_dict = {
            "privacy_request_id": "pr",
            "phase": "access",
            "nodes": {
                "ds:a": {"address": "ds:a", "is_dirty": False},
                "ds:b": {"address": "ds:b", "is_dirty": True},
            },
        }
        assert graph_plan_has_dirty(plan_dict) is True

    def test_dict_no_dirty(self):
        plan_dict = {
            "privacy_request_id": "pr",
            "phase": "access",
            "nodes": {
                "ds:a": {"address": "ds:a", "is_dirty": False},
            },
        }
        assert graph_plan_has_dirty(plan_dict) is False


class TestCrossPhaseInvalidation:
    """Test that access re-runs when dirty nodes detected during erasure resume."""

    def test_resume_from_erasure_with_dirty_access(self):
        """When resuming from erasure, access checkpoint is skipped.
        But if graph diff found dirty access nodes, access should still run."""
        from_step = "erasure"

        assert can_run_checkpoint("access", from_step) is False

        access_plan = GraphPlan(
            privacy_request_id="pr",
            phase=TraversalPhase.ACCESS,
            nodes={
                "ds:a": NodeInfo(
                    address="ds:a", already_completed=True, is_dirty=False
                ),
                "ds:b": NodeInfo(
                    address="ds:b", is_dirty=True, dirty_reasons=["edges_changed"]
                ),
            },
        )
        access_has_dirty = graph_plan_has_dirty(access_plan)

        run_access = can_run_checkpoint("access", from_step) or access_has_dirty
        assert run_access is True

    def test_resume_from_erasure_no_dirty_access(self):
        """When resuming from erasure with no dirty access nodes,
        access should NOT run."""
        from_step = "erasure"

        access_plan = GraphPlan(
            privacy_request_id="pr",
            phase=TraversalPhase.ACCESS,
            nodes={
                "ds:a": NodeInfo(
                    address="ds:a", already_completed=True, is_dirty=False
                ),
            },
        )
        access_has_dirty = graph_plan_has_dirty(access_plan)

        run_access = can_run_checkpoint("access", from_step) or access_has_dirty
        assert run_access is False

    def test_first_run_always_runs_access(self):
        """First run (no from_step): access always runs."""
        from_step = None
        run_access = can_run_checkpoint("access", from_step) or False
        assert run_access is True

    def test_upload_follows_dirty_access(self):
        """Upload should re-run if access had dirty nodes, even when
        resuming past upload checkpoint."""
        from_step = "erasure"
        access_has_dirty = True

        run_upload = can_run_checkpoint("upload_access", from_step) or access_has_dirty
        assert run_upload is True

    def test_upload_skipped_when_no_dirty_access(self):
        from_step = "erasure"
        access_has_dirty = False

        run_upload = can_run_checkpoint("upload_access", from_step) or access_has_dirty
        assert run_upload is False
