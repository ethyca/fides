"""Top-level DSR lifecycle workflow.

Replaces run_privacy_request Celery task and its checkpoint system.
Each checkpoint becomes a workflow step — Temporal's deterministic
replay provides the retry/resume semantics that checkpoints handled.
"""

from __future__ import annotations

from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from fides.api.task.temporal.activities.finalization import (
        finalize_privacy_request,
        prepare_erasure_tasks,
    )
    from fides.api.task.temporal.activities.graph_construction import (
        build_and_persist_access_graph,
        build_and_persist_consent_graph,
        build_erasure_graph_plan,
        load_privacy_request_context,
    )
    from fides.api.task.temporal.activities.status_management import (
        run_post_webhooks,
        run_pre_webhooks,
        update_privacy_request_status,
    )
    from fides.api.task.temporal.activities.upload_results import (
        upload_access_results,
    )
    from fides.api.task.temporal.converters import (
        DSRLifecycleParams,
        DSRLifecycleResult,
        GraphTraversalParams,
        GraphTraversalResult,
        PrivacyRequestContext,
        TraversalPhase,
    )
    from fides.api.task.temporal.workflows.graph_traversal import (
        GraphTraversalWorkflow,
    )

ACTIVITY_TIMEOUT = timedelta(minutes=30)
ACTIVITY_RETRY = RetryPolicy(maximum_attempts=3)

CHECKPOINT_ORDER = [
    "pre_webhooks",
    "access",
    "upload_access",
    "erasure",
    "consent",
    "post_webhooks",
    "finalization",
]


def _get_failed_nodes(result) -> list:
    """Extract failed_nodes from a GraphTraversalResult, handling both
    dataclass and dict deserialization from Temporal."""
    if isinstance(result, dict):
        return result.get("failed_nodes", [])
    return getattr(result, "failed_nodes", [])


def can_run_checkpoint(step: str, from_step: str | None) -> bool:
    """Check if a step should run given the resume point.

    Mirrors the Celery checkpoint system: when resuming from a
    specific step, skip all earlier steps.
    """
    if not from_step:
        return True
    if step not in CHECKPOINT_ORDER or from_step not in CHECKPOINT_ORDER:
        return True
    return CHECKPOINT_ORDER.index(step) >= CHECKPOINT_ORDER.index(from_step)


@workflow.defn
class DSRLifecycleWorkflow:
    """Orchestrate the full privacy request lifecycle.

    Graph rebuild + diff always runs so config changes are detected.
    Checkpoints control which phases execute. If the diff reveals
    dirty access nodes while resuming past the access phase, access
    re-runs for those nodes before proceeding (cross-phase invalidation).
    """

    @workflow.run
    async def run(self, params: DSRLifecycleParams) -> DSRLifecycleResult:
        from_step = params.from_step

        ctx: PrivacyRequestContext = await workflow.execute_activity(
            load_privacy_request_context,
            params.privacy_request_id,
            start_to_close_timeout=ACTIVITY_TIMEOUT,
            retry_policy=ACTIVITY_RETRY,
        )

        # --- Graph rebuild always runs (detects config changes) ---

        access_graph_plan = None
        if ctx.has_access_rules:
            access_graph_plan = await workflow.execute_activity(
                build_and_persist_access_graph,
                params.privacy_request_id,
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=ACTIVITY_RETRY,
            )

        # --- Checkpointed execution ---

        if can_run_checkpoint("pre_webhooks", from_step):
            proceed = await workflow.execute_activity(
                run_pre_webhooks,
                args=[params.privacy_request_id, params.from_webhook_id],
                start_to_close_timeout=timedelta(hours=1),
                retry_policy=ACTIVITY_RETRY,
            )
            if not proceed:
                return DSRLifecycleResult(
                    status="paused", error_message="Pre-webhook halted execution"
                )

        # Access execution: run if checkpoint allows, OR if dirty nodes
        # exist and we're resuming past access (cross-phase invalidation)
        access_has_dirty = access_graph_plan is not None and graph_plan_has_dirty(
            access_graph_plan
        )
        run_access = can_run_checkpoint("access", from_step) or access_has_dirty

        if ctx.has_access_rules and run_access and access_graph_plan is not None:
            access_result: GraphTraversalResult = await workflow.execute_child_workflow(
                GraphTraversalWorkflow.run,
                GraphTraversalParams(
                    privacy_request_id=params.privacy_request_id,
                    phase=TraversalPhase.ACCESS,
                    graph_plan=access_graph_plan,
                ),
                id=f"access-{params.privacy_request_id}",
                execution_timeout=timedelta(hours=24),
            )

            failed = _get_failed_nodes(access_result)
            if failed:
                await workflow.execute_activity(
                    update_privacy_request_status,
                    args=[params.privacy_request_id, "error"],
                    start_to_close_timeout=ACTIVITY_TIMEOUT,
                )
                return DSRLifecycleResult(
                    status="error",
                    error_message=f"Access phase failed for {len(failed)} collections: "
                    + ", ".join(failed[:5]),
                )

        # Upload: run if checkpoint allows, or if access re-ran with dirty nodes
        run_upload = can_run_checkpoint("upload_access", from_step) or access_has_dirty
        if ctx.has_access_rules and run_upload:
            await workflow.execute_activity(
                upload_access_results,
                params.privacy_request_id,
                start_to_close_timeout=ACTIVITY_TIMEOUT,
                retry_policy=ACTIVITY_RETRY,
            )

        if ctx.has_erasure_rules and can_run_checkpoint("erasure", from_step):
            has_erasure_tasks = await workflow.execute_activity(
                prepare_erasure_tasks,
                params.privacy_request_id,
                start_to_close_timeout=ACTIVITY_TIMEOUT,
                retry_policy=ACTIVITY_RETRY,
            )

            if has_erasure_tasks:
                erasure_plan = await workflow.execute_activity(
                    build_erasure_graph_plan,
                    params.privacy_request_id,
                    start_to_close_timeout=timedelta(minutes=5),
                    retry_policy=ACTIVITY_RETRY,
                )

                erasure_result: GraphTraversalResult = (
                    await workflow.execute_child_workflow(
                        GraphTraversalWorkflow.run,
                        GraphTraversalParams(
                            privacy_request_id=params.privacy_request_id,
                            phase=TraversalPhase.ERASURE,
                            graph_plan=erasure_plan,
                        ),
                        id=f"erasure-{params.privacy_request_id}",
                        execution_timeout=timedelta(hours=24),
                    )
                )

                failed = _get_failed_nodes(erasure_result)
                if failed:
                    await workflow.execute_activity(
                        update_privacy_request_status,
                        args=[params.privacy_request_id, "error"],
                        start_to_close_timeout=ACTIVITY_TIMEOUT,
                    )
                    return DSRLifecycleResult(
                        status="error",
                        error_message=f"Erasure phase failed for {len(failed)} collections: "
                        + ", ".join(failed[:5]),
                    )

        if ctx.has_consent_rules and can_run_checkpoint("consent", from_step):
            consent_plan = await workflow.execute_activity(
                build_and_persist_consent_graph,
                args=[params.privacy_request_id, ctx.identity_data],
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=ACTIVITY_RETRY,
            )

            consent_result: GraphTraversalResult = (
                await workflow.execute_child_workflow(
                    GraphTraversalWorkflow.run,
                    GraphTraversalParams(
                        privacy_request_id=params.privacy_request_id,
                        phase=TraversalPhase.CONSENT,
                        graph_plan=consent_plan,
                    ),
                    id=f"consent-{params.privacy_request_id}",
                    execution_timeout=timedelta(hours=24),
                )
            )

            failed = _get_failed_nodes(consent_result)
            if failed:
                await workflow.execute_activity(
                    update_privacy_request_status,
                    args=[params.privacy_request_id, "error"],
                    start_to_close_timeout=ACTIVITY_TIMEOUT,
                )
                return DSRLifecycleResult(
                    status="error",
                    error_message=f"Consent phase failed for {len(failed)} collections: "
                    + ", ".join(failed[:5]),
                )

        if can_run_checkpoint("post_webhooks", from_step):
            proceed = await workflow.execute_activity(
                run_post_webhooks,
                params.privacy_request_id,
                start_to_close_timeout=timedelta(hours=1),
                retry_policy=ACTIVITY_RETRY,
            )
            if not proceed:
                return DSRLifecycleResult(
                    status="paused", error_message="Post-webhook halted execution"
                )

        if can_run_checkpoint("finalization", from_step):
            final_status = await workflow.execute_activity(
                finalize_privacy_request,
                params.privacy_request_id,
                start_to_close_timeout=ACTIVITY_TIMEOUT,
                retry_policy=ACTIVITY_RETRY,
            )
            return DSRLifecycleResult(status=final_status)

        return DSRLifecycleResult(status="complete")


def graph_plan_has_dirty(plan) -> bool:
    """Check if a GraphPlan has dirty nodes, handling both
    dataclass and dict deserialization from Temporal."""
    if isinstance(plan, dict):
        nodes = plan.get("nodes", {})
        return any(
            (
                n.get("is_dirty")
                if isinstance(n, dict)
                else getattr(n, "is_dirty", False)
            )
            for n in nodes.values()
        )
    return getattr(plan, "has_dirty_nodes", False)
