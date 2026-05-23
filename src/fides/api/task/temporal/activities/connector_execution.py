"""Activities for executing connector nodes.

Wraps the existing GraphTask/ManualTaskGraphTask execution logic,
reusing the same connector code paths used by the Celery implementation.
Includes a polling activity for async connectors that need repeated status checks.
"""

from __future__ import annotations

from temporalio import activity

from fides.api.task.temporal.converters import (
    NodeExecutionParams,
    NodeExecutionResult,
    TraversalPhase,
)


@activity.defn
async def execute_access_node(params: NodeExecutionParams) -> NodeExecutionResult:
    """Execute an access request on a single collection node.

    Reuses the same code path as run_access_node in execute_request_tasks.py:
    loads the RequestTask, creates a GraphTask, gathers upstream data,
    calls connector.retrieve_data, and saves results.
    """
    from sqlalchemy.orm import selectinload

    from fides.api.models.connectionconfig import ConnectionConfig
    from fides.api.models.policy import Policy
    from fides.api.models.privacy_request import PrivacyRequest, RequestTask
    from fides.api.schemas.policy import ActionType
    from fides.api.task.execute_request_tasks import (
        _build_upstream_access_data,
        create_graph_task,
    )
    from fides.api.task.task_resources import TaskResources
    from fides.common.session_management import get_autoclose_db_session

    with get_autoclose_db_session() as session:
        privacy_request = (
            session.query(PrivacyRequest)
            .options(
                selectinload(PrivacyRequest.policy).selectinload(Policy.rules),
            )
            .filter(PrivacyRequest.id == params.privacy_request_id)
            .first()
        )
        if not privacy_request:
            raise ValueError(f"Privacy request {params.privacy_request_id} not found")

        request_task = RequestTask.get(db=session, object_id=params.request_task_id)
        if not request_task:
            raise ValueError(f"RequestTask {params.request_task_id} not found")

        upstream_results = request_task.upstream_tasks_objects(session)

        with TaskResources(
            privacy_request,
            privacy_request.policy,
            session.query(ConnectionConfig).all(),
            request_task,
            session,
        ) as resources:
            graph_task = create_graph_task(session, request_task, resources)

            upstream_access_data = _build_upstream_access_data(
                graph_task.execution_node.input_keys,
                upstream_results,
            )

            graph_task.access_request(*upstream_access_data)

        session.commit()

        from fides.api.schemas.privacy_request import ExecutionLogStatus

        session.refresh(request_task)
        if request_task.status == ExecutionLogStatus.error:
            raise RuntimeError(f"Access request failed for {params.node_address}")

        return NodeExecutionResult(
            node_address=params.node_address,
            status="complete",
            rows_processed=len(request_task.get_access_data() or []),
        )


@activity.defn
async def execute_erasure_node(params: NodeExecutionParams) -> NodeExecutionResult:
    """Execute an erasure request on a single collection node."""
    from sqlalchemy.orm import selectinload

    from fides.api.models.connectionconfig import ConnectionConfig
    from fides.api.models.policy import Policy
    from fides.api.models.privacy_request import PrivacyRequest, RequestTask
    from fides.api.task.execute_request_tasks import create_graph_task
    from fides.api.task.task_resources import TaskResources
    from fides.common.session_management import get_autoclose_db_session

    with get_autoclose_db_session() as session:
        privacy_request = (
            session.query(PrivacyRequest)
            .options(
                selectinload(PrivacyRequest.policy).selectinload(Policy.rules),
            )
            .filter(PrivacyRequest.id == params.privacy_request_id)
            .first()
        )
        if not privacy_request:
            raise ValueError(f"Privacy request {params.privacy_request_id} not found")

        request_task = RequestTask.get(db=session, object_id=params.request_task_id)
        if not request_task:
            raise ValueError(f"RequestTask {params.request_task_id} not found")

        with TaskResources(
            privacy_request,
            privacy_request.policy,
            session.query(ConnectionConfig).all(),
            request_task,
            session,
        ) as resources:
            graph_task = create_graph_task(session, request_task, resources)
            retrieved_data = request_task.get_data_for_erasures() or []
            graph_task.erasure_request(retrieved_data)

        session.commit()

        from fides.api.schemas.privacy_request import ExecutionLogStatus

        session.refresh(request_task)
        if request_task.status == ExecutionLogStatus.error:
            raise RuntimeError(f"Erasure request failed for {params.node_address}")

        return NodeExecutionResult(
            node_address=params.node_address,
            status="complete",
            rows_processed=request_task.rows_masked or 0,
        )


@activity.defn
async def execute_consent_node(params: NodeExecutionParams) -> NodeExecutionResult:
    """Execute a consent request on a single collection node."""
    from sqlalchemy.orm import selectinload

    from fides.api.models.connectionconfig import ConnectionConfig
    from fides.api.models.policy import Policy
    from fides.api.models.privacy_request import PrivacyRequest, RequestTask
    from fides.api.task.execute_request_tasks import create_graph_task
    from fides.api.task.task_resources import TaskResources
    from fides.common.session_management import get_autoclose_db_session

    with get_autoclose_db_session() as session:
        privacy_request = (
            session.query(PrivacyRequest)
            .options(
                selectinload(PrivacyRequest.policy).selectinload(Policy.rules),
            )
            .filter(PrivacyRequest.id == params.privacy_request_id)
            .first()
        )
        if not privacy_request:
            raise ValueError(f"Privacy request {params.privacy_request_id} not found")

        request_task = RequestTask.get(db=session, object_id=params.request_task_id)
        if not request_task:
            raise ValueError(f"RequestTask {params.request_task_id} not found")

        identity_data = {
            key: value["value"] if isinstance(value, dict) else value
            for key, value in privacy_request.get_cached_identity_data().items()
        }

        with TaskResources(
            privacy_request,
            privacy_request.policy,
            session.query(ConnectionConfig).all(),
            request_task,
            session,
        ) as resources:
            graph_task = create_graph_task(session, request_task, resources)
            graph_task.consent_request(identity_data)

        session.commit()

        from fides.api.schemas.privacy_request import ExecutionLogStatus

        session.refresh(request_task)
        if request_task.status == ExecutionLogStatus.error:
            raise RuntimeError(f"Consent request failed for {params.node_address}")

        return NodeExecutionResult(
            node_address=params.node_address,
            status="complete",
            rows_processed=1 if request_task.consent_sent else 0,
        )


@activity.defn
async def execute_polling_node(params: NodeExecutionParams) -> NodeExecutionResult:
    """Execute an async polling node with heartbeats.

    Sends the initial request, then enters a polling loop that checks
    sub-request statuses at configured intervals. Heartbeats to Temporal
    at each poll cycle so the activity isn't considered timed out.

    Replaces the separate APScheduler polling job + Celery re-queue pattern.
    """
    import asyncio

    from sqlalchemy.orm import selectinload

    from fides.api.models.connectionconfig import ConnectionConfig
    from fides.api.models.policy import Policy
    from fides.api.models.privacy_request import PrivacyRequest, RequestTask
    from fides.api.task.execute_request_tasks import (
        _build_upstream_access_data,
        create_graph_task,
    )
    from fides.api.task.task_resources import TaskResources
    from fides.common.session_management import get_autoclose_db_session
    from fides.config import CONFIG

    poll_interval = CONFIG.execution.async_polling_interval_hours * 3600

    while True:
        with get_autoclose_db_session() as session:
            privacy_request = (
                session.query(PrivacyRequest)
                .options(
                    selectinload(PrivacyRequest.policy).selectinload(Policy.rules),
                )
                .filter(PrivacyRequest.id == params.privacy_request_id)
                .first()
            )
            if not privacy_request:
                raise ValueError(
                    f"Privacy request {params.privacy_request_id} not found"
                )

            request_task = RequestTask.get(db=session, object_id=params.request_task_id)
            if not request_task:
                raise ValueError(f"RequestTask {params.request_task_id} not found")

            upstream_results = request_task.upstream_tasks_objects(session)

            try:
                with TaskResources(
                    privacy_request,
                    privacy_request.policy,
                    session.query(ConnectionConfig).all(),
                    request_task,
                    session,
                ) as resources:
                    graph_task = create_graph_task(session, request_task, resources)

                    if params.phase == TraversalPhase.ACCESS:
                        upstream_data = _build_upstream_access_data(
                            graph_task.execution_node.input_keys,
                            upstream_results,
                        )
                        graph_task.access_request(*upstream_data)
                    else:
                        retrieved_data = request_task.get_data_for_erasures() or []
                        graph_task.erasure_request(retrieved_data)

                # If we get here without exception, polling is complete
                return NodeExecutionResult(
                    node_address=params.node_address,
                    status="complete",
                    rows_processed=len(request_task.get_access_data() or []),
                )

            except Exception as exc:
                if "AwaitingAsyncProcessing" in type(exc).__name__:
                    activity.heartbeat(f"Polling {params.node_address}")
                    await asyncio.sleep(poll_interval)
                    continue
                raise
