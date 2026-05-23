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


def _get_failed_nodes(result) -> list:
    """Extract failed_nodes from a GraphTraversalResult, handling both
    dataclass and dict deserialization from Temporal."""
    if isinstance(result, dict):
        return result.get("failed_nodes", [])
    return getattr(result, "failed_nodes", [])


@workflow.defn
class DSRLifecycleWorkflow:
    """Orchestrate the full privacy request lifecycle.

    Phases: pre-webhooks -> access -> upload -> erasure -> consent ->
    post-webhooks -> finalization. The graph is built fresh (not from
    stale cache), solving the retry/regeneration problem.
    """

    @workflow.run
    async def run(self, params: DSRLifecycleParams) -> DSRLifecycleResult:
        # Step 1: Load request context
        ctx: PrivacyRequestContext = await workflow.execute_activity(
            load_privacy_request_context,
            params.privacy_request_id,
            start_to_close_timeout=ACTIVITY_TIMEOUT,
            retry_policy=ACTIVITY_RETRY,
        )

        # Step 2: Pre-webhooks
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

        # Step 3: Access phase — graph built fresh here
        if ctx.has_access_rules:
            graph_plan = await workflow.execute_activity(
                build_and_persist_access_graph,
                params.privacy_request_id,
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=ACTIVITY_RETRY,
            )

            access_result: GraphTraversalResult = await workflow.execute_child_workflow(
                GraphTraversalWorkflow.run,
                GraphTraversalParams(
                    privacy_request_id=params.privacy_request_id,
                    phase=TraversalPhase.ACCESS,
                    graph_plan=graph_plan,
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

            # Step 4: Upload access results
            await workflow.execute_activity(
                upload_access_results,
                params.privacy_request_id,
                start_to_close_timeout=ACTIVITY_TIMEOUT,
                retry_policy=ACTIVITY_RETRY,
            )

        # Step 5: Erasure phase
        if ctx.has_erasure_rules:
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

        # Step 6: Consent phase
        if ctx.has_consent_rules:
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

        # Step 7: Post-webhooks
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

        # Step 8: Finalization
        final_status = await workflow.execute_activity(
            finalize_privacy_request,
            params.privacy_request_id,
            start_to_close_timeout=ACTIVITY_TIMEOUT,
            retry_policy=ACTIVITY_RETRY,
        )

        return DSRLifecycleResult(status=final_status)
