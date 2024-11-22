from typing import Optional

from fastapi import Depends
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.async_sqlalchemy import paginate as async_paginate
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_200_OK

from fides.api.db.ctl_session import get_async_db
from fides.api.models.detection_discovery import fetch_staged_resources_by_type_query
from fides.api.schemas.detection_discovery import StagedResourceResponse
from fides.api.util.api_router import APIRouter

LIFECYCLE_ROUTER = APIRouter(
    tags=["Dataset Lifecycle", "Detection and Discovery"], prefix="/lifecycle"
)


@LIFECYCLE_ROUTER.get(
    "/get/projects",
    status_code=HTTP_200_OK,
    response_model=Page[StagedResourceResponse],
)
async def get_projects(
    params: Params = Depends(),
    db: AsyncSession = Depends(get_async_db),
    show_hidden: bool = False,
    monitor_config_id: Optional[str] = None,
) -> AbstractPage[StagedResourceResponse]:
    """
    Get all lifecycle projects from the db.
    A "project" for lifecycle experience is a stagedresource "database"
    """
    query = fetch_staged_resources_by_type_query(
        db=db,
        resource_type="database",
        monitor_config_id=monitor_config_id,
        show_hidden=show_hidden,
    )
    return await async_paginate(db, query, params)  # type: ignore


@LIFECYCLE_ROUTER.get(
    "/get/datasets",
    status_code=HTTP_200_OK,
    response_model=Page[StagedResourceResponse],
)
async def get_datasets(
    params: Params = Depends(),
    db: AsyncSession = Depends(get_async_db),
    monitor_config_id: Optional[str] = None,
    show_hidden: bool = False,
) -> AbstractPage[StagedResourceResponse]:
    """
    Get all lifecycle datasets from the db.
    A "dataset" for lifecycle experience is a stagedresource "schema"
    """
    query = fetch_staged_resources_by_type_query(
        db=db,
        resource_type="schema",
        monitor_config_id=monitor_config_id,
        show_hidden=show_hidden,
    )
    return await async_paginate(db, query, params)  # type: ignore
