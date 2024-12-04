from typing import List, Optional

from fastapi import Depends
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from fastapi_pagination.ext.async_sqlalchemy import paginate as async_paginate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from starlette.status import HTTP_200_OK

from fides.api.api.deps import get_db
from fides.api.api.v1.endpoints import API_PREFIX
from fides.api.db.ctl_session import get_async_db
from fides.api.models.detection_discovery import (
    fetch_staged_resources_by_type_query,
    mark_resources_hidden,
)
from fides.api.models.sql_models import System
from fides.api.schemas.detection_discovery import StagedResourceResponse
from fides.api.schemas.system import SystemResponseWithMonitors
from fides.api.util.api_router import APIRouter
from fides.api.models.detection_discovery import MonitorConfig, ConnectionConfig

LIFECYCLE_ROUTER = APIRouter(
    tags=["Dataset Lifecycle", "Detection and Discovery"],
    prefix=f"{API_PREFIX}/lifecycle",
)


@LIFECYCLE_ROUTER.post(
    "/project",
    status_code=HTTP_200_OK,
    response_model=Page[StagedResourceResponse],
)
async def get_projects(
    params: Params = Depends(),
    db: Session = Depends(get_db),
    show_hidden: bool = False,
    monitor_config_ids: Optional[List[str]] = None,
) -> AbstractPage[StagedResourceResponse]:
    """
    Get all lifecycle projects from the db.
    A "project" for lifecycle experience is a stagedresource "database"
    """
    query = fetch_staged_resources_by_type_query(
        resource_type="Database",
        monitor_config_ids=monitor_config_ids,
        show_hidden=show_hidden,
    )
    return paginate(db, query, params)  # type: ignore


@LIFECYCLE_ROUTER.post(
    "/dataset",
    status_code=HTTP_200_OK,
    response_model=Page[StagedResourceResponse],
)
async def get_datasets(
    params: Params = Depends(),
    db: Session = Depends(get_db),
    monitor_config_ids: Optional[List[str]] = None,
    show_hidden: bool = False,
) -> AbstractPage[StagedResourceResponse]:
    """
    Get all lifecycle datasets from the db.
    A "dataset" for lifecycle experience is a stagedresource "schema"
    """
    query = fetch_staged_resources_by_type_query(
        resource_type="schema",
        monitor_config_ids=monitor_config_ids,
        show_hidden=show_hidden,
    )
    results = paginate(db, query, params)
    return results


@LIFECYCLE_ROUTER.patch("/hide/", status_code=HTTP_200_OK)
async def hide_resources(
    urns: List[str], db_async: AsyncSession = Depends(get_async_db)
) -> None:
    """
    Hide resources, specified by urn, from the lifecycle experience
    """
    await mark_resources_hidden(db_async, urns, True)


@LIFECYCLE_ROUTER.patch("/un-hide/", status_code=HTTP_200_OK)
async def un_hide_resources(
    urns: List[str], db_async: AsyncSession = Depends(get_async_db)
) -> None:
    """
    Un-hide resources, specified by urn, from the lifecycle experience
    """
    await mark_resources_hidden(db_async, urns, False)


@LIFECYCLE_ROUTER.get(
    "/system",
    status_code=HTTP_200_OK,
    response_model=Page[SystemResponseWithMonitors],
)
async def get_systems(
    params: Params = Depends(),
    db_async: AsyncSession = Depends(get_async_db),
    show_hidden: bool = False,
) -> AbstractPage[SystemResponseWithMonitors]:
    """
    Get all DnD relevant systems from the db. Systems must either be referenced in an integration, or have at least one dataset
    """
    query = select(System).filter(
        (System.dataset_references != {}) | (System.connection_configs != None)
    )

    if not show_hidden:
        query = query.filter(System.hidden == False)

    return await async_paginate(db_async, query, params)
