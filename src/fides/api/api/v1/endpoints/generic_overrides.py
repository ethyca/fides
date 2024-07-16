from typing import List, Optional, Union

from fastapi import APIRouter, Depends, Query, Security
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.async_sqlalchemy import paginate as async_paginate
from fideslang.models import Dataset
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import select

from fides.api.db.crud import list_resource
from fides.api.db.ctl_session import get_async_db
from fides.api.oauth.utils import verify_oauth_client
from fides.api.schemas.filter_params import FilterParams
from fides.api.util.filter_utils import apply_filters_to_query
from fides.common.api.scope_registry import DATASET_READ
from fides.common.api.v1.urn_registry import V1_URL_PREFIX

from fides.api.models.sql_models import (  # type: ignore[attr-defined] # isort: skip
    Dataset as CtlDataset,
)

# We create routers to override specific methods in those defined in generic.py
# when we need more custom implementations for only some of the methods in a router.

dataset_router = APIRouter(tags=["Dataset"], prefix=V1_URL_PREFIX)


@dataset_router.get(
    "/dataset",
    dependencies=[Security(verify_oauth_client, scopes=[DATASET_READ])],
    response_model=Union[Page[Dataset], List[Dataset]],
    name="List datasets (optionally paginated)",
)
async def list_dataset_paginated(
    db: AsyncSession = Depends(get_async_db),
    size: Optional[int] = Query(None, ge=1, le=100),
    page: Optional[int] = Query(None, ge=1),
    search: Optional[str] = Query(None),
    data_categories: Optional[List[str]] = Query(None),
) -> Union[Page[Dataset], List[Dataset]]:
    """
    Get a list of all of the Datasets.
    If any pagination parameters (size or page) are provided, then the response will be paginated
    & provided filters (search, data_categories) will be applied.
    Otherwise all Datasets will be returned (this may be a slow operation if there are many datasets,
    so using the pagination parameters is recommended).
    """
    if page or size:
        query = select(CtlDataset)
        filter_params = FilterParams(search=search, data_categories=data_categories)
        filtered_query = apply_filters_to_query(
            query=query,
            search_model=CtlDataset,
            taxonomy_model=CtlDataset,
            filter_params=filter_params,
        )
        pagination_params = Params(page=page or 1, size=size or 50)
        return await async_paginate(db, filtered_query, pagination_params)

    return await list_resource(CtlDataset, db)


GENERIC_OVERRIDES_ROUTER = APIRouter()
GENERIC_OVERRIDES_ROUTER.include_router(dataset_router)
