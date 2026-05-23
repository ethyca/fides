"""Temporal worker process entrypoint.

Registers all DSR workflows and activities with a Temporal worker
and starts polling the configured task queue.
"""

from __future__ import annotations

import asyncio

from loguru import logger
from temporalio.client import Client
from temporalio.worker import Worker

from fides.api.db.base import Base  # noqa: F401 — register all SQLAlchemy models
from fides.config import CONFIG


async def _run_worker() -> None:
    """Connect to Temporal and run the worker until interrupted."""
    server_url = CONFIG.temporal.server_url
    namespace = CONFIG.temporal.namespace
    task_queue = CONFIG.temporal.task_queue

    logger.info(
        "Connecting to Temporal at {} namespace={} queue={}",
        server_url,
        namespace,
        task_queue,
    )

    client = await Client.connect(server_url, namespace=namespace)

    from temporalio.worker.workflow_sandbox import (
        SandboxedWorkflowRunner,
        SandboxRestrictions,
    )

    from fides.api.task.temporal.activities.connector_execution import (
        execute_access_node,
        execute_consent_node,
        execute_erasure_node,
        execute_polling_node,
    )
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
        mark_request_task_failed,
        run_post_webhooks,
        run_pre_webhooks,
        update_privacy_request_status,
    )
    from fides.api.task.temporal.activities.upload_results import (
        upload_access_results,
    )
    from fides.api.task.temporal.workflows.dsr_lifecycle import (
        DSRLifecycleWorkflow,
    )
    from fides.api.task.temporal.workflows.graph_traversal import (
        GraphTraversalWorkflow,
    )
    from fides.api.task.temporal.workflows.node_execution import (
        NodeExecutionWorkflow,
    )

    worker = Worker(
        client,
        task_queue=task_queue,
        workflow_runner=SandboxedWorkflowRunner(
            restrictions=SandboxRestrictions.default.with_passthrough_modules(
                "fides",
            )
        ),
        workflows=[
            DSRLifecycleWorkflow,
            GraphTraversalWorkflow,
            NodeExecutionWorkflow,
        ],
        activities=[
            load_privacy_request_context,
            build_and_persist_access_graph,
            build_and_persist_consent_graph,
            build_erasure_graph_plan,
            execute_access_node,
            execute_erasure_node,
            execute_consent_node,
            execute_polling_node,
            upload_access_results,
            run_pre_webhooks,
            run_post_webhooks,
            update_privacy_request_status,
            mark_request_task_failed,
            finalize_privacy_request,
            prepare_erasure_tasks,
        ],
    )

    logger.info("Temporal worker started on queue '{}'", task_queue)
    await worker.run()


def start_temporal_worker() -> None:
    """Start the Temporal worker (blocking)."""
    try:
        asyncio.run(_run_worker())
    except KeyboardInterrupt:
        logger.info("Temporal worker shutting down")
