from typing import List, Optional

from fastapi import Depends
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from starlette.status import HTTP_200_OK

from fides.api.api.deps import get_db
from fides.api.db.ctl_session import get_async_db
from fides.api.models.detection_discovery import (
    fetch_staged_resources_by_type_query,
    mark_resources_hidden,
)
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
    db: Session = Depends(get_db),
    show_hidden: bool = False,
    monitor_config_id: Optional[str] = None,
) -> AbstractPage[StagedResourceResponse]:
    """
    Get all lifecycle projects from the db.
    A "project" for lifecycle experience is a stagedresource "database"
    """
    query = fetch_staged_resources_by_type_query(
        resource_type="Database",
        monitor_config_id=monitor_config_id,
        show_hidden=show_hidden,
    )
    return paginate(db, query, params)  # type: ignore


@LIFECYCLE_ROUTER.get(
    "/get/datasets",
    status_code=HTTP_200_OK,
    response_model=Page[StagedResourceResponse],
)
async def get_datasets(
    params: Params = Depends(),
    db: Session = Depends(get_db),
    monitor_config_id: Optional[str] = None,
    show_hidden: bool = False,
) -> AbstractPage[StagedResourceResponse]:
    """
    Get all lifecycle datasets from the db.
    A "dataset" for lifecycle experience is a stagedresource "schema"
    """
    query = fetch_staged_resources_by_type_query(
        resource_type="schema",
        monitor_config_id=monitor_config_id,
        show_hidden=show_hidden,
    )
    return paginate(db, query, params)  # type: ignore


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
