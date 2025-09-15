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
from fides.api.models.detection_discovery.monitor_task import (
    MonitorTask,
    MonitorTaskType,
)
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.oauth.utils import verify_oauth_client
from fides.api.schemas.monitor_task import MonitorTaskInProgressResponse
from fides.common.api.scope_registry import SYSTEM_READ
from fides.common.api.v1.urn_registry import V1_URL_PREFIX

router = APIRouter(tags=["Monitor Tasks"], prefix=V1_URL_PREFIX)


@router.get(
    "/monitor-tasks/in-progress",
    dependencies=[Security(verify_oauth_client, scopes=[SYSTEM_READ])],
    status_code=HTTP_200_OK,
    response_model=Page[MonitorTaskInProgressResponse],
)
def get_in_progress_monitor_tasks(
    db: Session = Depends(deps.get_db),
    params: Params = Depends(),
    search: Optional[str] = Query(None, description="Search by monitor name"),
    show_completed: Optional[bool] = Query(
        False, description="Include completed tasks"
    ),
    connection_names: Optional[List[str]] = Query(
        None, description="Filter by connection names"
    ),
    task_types: Optional[List[str]] = Query(
        None, description="Filter by task types (classification, promotion)"
    ),
    statuses: Optional[List[str]] = Query(None, description="Filter by task statuses"),
) -> Page[MonitorTaskInProgressResponse]:
    """
    Get monitor tasks (classification and promotion).

    By default, this endpoint retrieves tasks that are actively being processed:
    - Classification tasks with status: pending, in_processing
    - Promotion tasks with status: pending, in_processing

    When show_completed=true, it includes all tasks regardless of status.

    The response includes monitor name, task type, last updated date, current status,
    associated staged resources, and connection type.
    """

    # Build base query for classification and promotion tasks
    query = (
        db.query(MonitorTask)
        .options(
            joinedload(MonitorTask.monitor_config).joinedload(
                MonitorConfig.connection_config
            )
        )
        .filter(
            MonitorTask.action_type.in_(
                [MonitorTaskType.CLASSIFICATION.value, MonitorTaskType.PROMOTION.value]
            )
        )
    )

    # Add status filter unless we want to show completed tasks
    if not show_completed:
        query = query.filter(
            MonitorTask.status.in_(
                [
                    ExecutionLogStatus.pending.value,
                    ExecutionLogStatus.in_processing.value,
                ]
            )
        )

    # Add search filter if provided
    if search:
        query = query.filter(
            MonitorTask.monitor_config.has(MonitorConfig.name.ilike(f"%{search}%"))
        )

    # Add connection name filter if provided
    if connection_names:
        query = query.filter(
            MonitorTask.monitor_config.has(
                MonitorConfig.connection_config.has(
                    ConnectionConfig.name.in_(connection_names)
                )
            )
        )

    # Add task type filter if provided
    if task_types:
        query = query.filter(MonitorTask.action_type.in_(task_types))

    # Add status filter if provided
    if statuses:
        query = query.filter(MonitorTask.status.in_(statuses))

    # Order by most recently updated first
    query = query.order_by(MonitorTask.updated_at.desc())

    # Use pagination to return results
    page_result = paginate(query, params)

    # Transform to response schema
    response_items = []
    for task in page_result.items:
        connection_type = None
        connection_name = None
        if task.monitor_config and task.monitor_config.connection_config:
            connection_type = (
                task.monitor_config.connection_config.connection_type.value
            )
            connection_name = task.monitor_config.connection_config.name

        response_items.append(
            MonitorTaskInProgressResponse(
                id=task.id,
                created_at=task.created_at,
                updated_at=task.updated_at,
                monitor_config_id=task.monitor_config_id,
                monitor_name=task.monitor_config.name if task.monitor_config else None,
                action_type=task.action_type,
                status=task.status,
                message=task.message,
                staged_resource_urns=task.staged_resource_urns,
                connection_type=connection_type,
                connection_name=connection_name,
            )
        )

    # Return paginated response with transformed items
    return Page.create(
        items=response_items,
        total=page_result.total,
        params=params,
    )
