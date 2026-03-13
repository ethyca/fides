from typing import Optional

from fastapi import Depends, Security
from loguru import logger
from sqlalchemy import func
from sqlalchemy.orm import Session
from starlette.status import HTTP_200_OK

from fides.api.deps import get_db
from fides.api.models.privacy_request.execution_log import ExecutionLog
from fides.api.models.privacy_request.request_task import RequestTask
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.oauth.utils import verify_oauth_client
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import (
    EXECUTION_STATUS_DISPLAY_MAP,
    ExecutionGraphNodeResponse,
    ExecutionGraphResponse,
)
from fides.api.util.api_router import APIRouter
from fides.api.v1.endpoints.privacy_request_endpoints import (
    get_privacy_request_or_error,
)
from fides.common.scope_registry import PRIVACY_REQUEST_READ
from fides.common.urn_registry import (
    PRIVACY_REQUEST_EXECUTION_GRAPH,
    V1_URL_PREFIX,
)

router = APIRouter(tags=["Privacy Requests"], prefix=V1_URL_PREFIX)


def _get_error_messages(
    db: Session, privacy_request_id: str, action_type: Optional[str]
) -> dict[str, str]:
    """Fetch the latest error message per collection address from ExecutionLog."""
    addr_expr = func.concat(
        ExecutionLog.dataset_name, ":", ExecutionLog.collection_name
    )
    latest_ts_query = db.query(
        addr_expr.label("addr"),
        func.max(ExecutionLog.created_at).label("max_ts"),
    ).filter(
        ExecutionLog.privacy_request_id == privacy_request_id,
        ExecutionLog.status == ExecutionLogStatus.error,
    )
    if action_type:
        latest_ts_query = latest_ts_query.filter(
            ExecutionLog.action_type == action_type
        )
    latest_ts = latest_ts_query.group_by(addr_expr).subquery()

    rows = (
        db.query(addr_expr.label("addr"), ExecutionLog.message)
        .join(
            latest_ts,
            (addr_expr == latest_ts.c.addr)
            & (ExecutionLog.created_at == latest_ts.c.max_ts),
        )
        .filter(
            ExecutionLog.privacy_request_id == privacy_request_id,
            ExecutionLog.status == ExecutionLogStatus.error,
        )
        .all()
    )
    return {row.addr: row.message for row in rows if row.message}


@router.get(
    PRIVACY_REQUEST_EXECUTION_GRAPH,
    dependencies=[Security(verify_oauth_client, scopes=[PRIVACY_REQUEST_READ])],
    status_code=HTTP_200_OK,
    response_model=ExecutionGraphResponse,
)
def get_execution_graph(
    privacy_request_id: str,
    *,
    db: Session = Depends(get_db),
    action_type: Optional[ActionType] = None,
) -> ExecutionGraphResponse:
    """Returns the execution graph for a privacy request.

    Each node represents a collection task with its current status,
    upstream/downstream dependencies, and optional error messages.
    """
    get_privacy_request_or_error(db, privacy_request_id, error_if_deleted=False)

    logger.info("Getting execution graph for '{}'", privacy_request_id)

    query = RequestTask.query_with_deferred_data(db.query(RequestTask)).filter(
        RequestTask.privacy_request_id == privacy_request_id
    )
    if action_type:
        query = query.filter(RequestTask.action_type == action_type.value)

    tasks = query.order_by(
        RequestTask.created_at.asc(), RequestTask.collection_address.asc()
    ).all()

    resolved_action_type = (
        action_type.value if action_type else _infer_action_type(tasks)
    )

    error_messages = _get_error_messages(db, privacy_request_id, resolved_action_type)

    nodes = [
        ExecutionGraphNodeResponse(
            id=task.id,
            collection_address=task.collection_address,
            dataset_name=task.dataset_name,
            collection_name=task.collection_name,
            status=EXECUTION_STATUS_DISPLAY_MAP.get(
                task.status, task.status.name if task.status else "unknown"
            ),
            action_type=task.action_type,
            created_at=task.created_at,
            updated_at=task.updated_at,
            upstream_tasks=task.upstream_tasks or [],
            downstream_tasks=task.downstream_tasks or [],
            message=error_messages.get(task.collection_address),
        )
        for task in tasks
    ]

    return ExecutionGraphResponse(
        privacy_request_id=privacy_request_id,
        action_type=resolved_action_type,
        nodes=nodes,
    )


def _infer_action_type(tasks: list[RequestTask]) -> str:
    """If no action_type filter was provided, infer the active phase from task statuses."""
    in_progress = [
        t
        for t in tasks
        if t.status in (ExecutionLogStatus.in_processing, ExecutionLogStatus.pending)
    ]
    if in_progress:
        return in_progress[0].action_type
    if tasks:
        return tasks[-1].action_type
    return ActionType.access.value
