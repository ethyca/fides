from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Security
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, joinedload
from starlette.status import HTTP_200_OK

from fides.api.api import deps
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.detection_discovery.core import MonitorConfig
from fides.api.models.detection_discovery.monitor_task import MonitorTask, MonitorTaskType
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.oauth.utils import verify_oauth_client
from fides.api.schemas.monitor_task import MonitorTaskInProgressResponse
from fides.common.api.scope_registry import MONITOR_READ
from fides.common.api.v1.urn_registry import V1_URL_PREFIX

router = APIRouter(tags=["Monitor Tasks"], prefix=V1_URL_PREFIX)


@router.get(
    "/monitor-tasks/in-progress",
    dependencies=[Security(verify_oauth_client, scopes=[MONITOR_READ])],
    status_code=HTTP_200_OK,
    response_model=Page[MonitorTaskInProgressResponse],
)
def get_in_progress_monitor_tasks(
    db: Session = Depends(deps.get_db),
    params: Params = Depends(),
    search: Optional[str] = Query(None, description="Search by monitor name"),
) -> Page[MonitorTaskInProgressResponse]:
    """
    Get all monitor tasks that are currently in progress (classification and promotion).

    This endpoint retrieves tasks that are actively being processed, including:
    - Classification tasks with status: pending, in_processing
    - Promotion tasks with status: pending, in_processing

    The response includes monitor name, task type, last updated date, current status,
    associated staged resources, and connection type.
    """

    # Build base query for in-progress classification and promotion tasks
    query = (
        db.query(MonitorTask)
        .options(joinedload(MonitorTask.monitor_config).joinedload(MonitorConfig.connection_config))
        .filter(
            and_(
                MonitorTask.action_type.in_([
                    MonitorTaskType.CLASSIFICATION.value,
                    MonitorTaskType.PROMOTION.value
                ]),
                MonitorTask.status.in_([
                    ExecutionLogStatus.pending.value,
                    ExecutionLogStatus.in_processing.value
                ])
            )
        )
    )

    # Add search filter if provided
    if search:
        query = query.filter(
            MonitorTask.monitor_config.has(
                MonitorConfig.name.ilike(f"%{search}%")
            )
        )

    # Order by most recently updated first
    query = query.order_by(MonitorTask.updated_at.desc())

    # Use pagination to return results
    page_result = paginate(query, params)

    # Transform to response schema
    response_items = []
    for task in page_result.items:
        connection_type = None
        if task.monitor_config and task.monitor_config.connection_config:
            connection_type = task.monitor_config.connection_config.connection_type.value

        response_items.append(
            MonitorTaskInProgressResponse(
                id=task.id,
                monitor_name=task.monitor_config.name if task.monitor_config else "Unknown",
                task_type=task.action_type,
                last_updated=task.updated_at,
                status=task.status,
                staged_resource_urns=task.staged_resource_urns,
                connection_type=connection_type,
                monitor_config_id=task.monitor_config_id,
                message=task.message,
            )
        )

    # Return paginated response with transformed items
    return Page.create(
        items=response_items,
        total=page_result.total,
        params=params,
    )
