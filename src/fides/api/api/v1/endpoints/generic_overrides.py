from typing import List, Optional, Union, Dict

from fastapi import APIRouter, Depends, Query, Security
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.async_sqlalchemy import paginate as async_paginate
from fideslang.models import Dataset
from sqlalchemy import not_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import select
from starlette import status

from fides.api.db.base_class import get_key_from_data
from fides.api.db.crud import list_resource_query
from fides.api.db.ctl_session import get_async_db
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.oauth.utils import verify_oauth_client
from fides.api.schemas.filter_params import FilterParams
from fides.api.util.filter_utils import apply_filters_to_query
from fides.common.api.scope_registry import DATASET_READ, DATA_USE_CREATE, DATA_CATEGORY_CREATE, DATA_SUBJECT_CREATE
from fides.common.api.v1.urn_registry import V1_URL_PREFIX

from fides.api.models.sql_models import (  # type: ignore[attr-defined] # isort: skip
    Dataset as CtlDataset, DataUse, DataCategory, DataSubject,
)

# We create routers to override specific methods in those defined in generic.py
# when we need more custom implementations for only some of the methods in a router.

dataset_router = APIRouter(tags=["Dataset"], prefix=V1_URL_PREFIX)
data_use_router = APIRouter(tags=["DataUse"], prefix=V1_URL_PREFIX)
data_category_router = APIRouter(tags=["DataCategory"], prefix=V1_URL_PREFIX)
data_subject_router = APIRouter(tags=["DataSubject"], prefix=V1_URL_PREFIX)


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
    exclude_saas_datasets: Optional[bool] = Query(False),
    only_unlinked_datasets: Optional[bool] = Query(False),
) -> Union[Page[Dataset], List[Dataset]]:
    """
    Get a list of all of the Datasets.
    If any pagination parameters (size or page) are provided, then the response will be paginated.
    Otherwise all Datasets will be returned (this may be a slow operation if there are many datasets,
    so using the pagination parameters is recommended).
    Provided filters (search, data_categories, exclude_saas_datasets, only_unlinked_datasets) will be applied,
    returning only the datasets that match ALL of the filters.
    """
    query = select(CtlDataset)

    # Add filters for search and data categories
    filter_params = FilterParams(search=search, data_categories=data_categories)
    filtered_query = apply_filters_to_query(
        query=query,
        search_model=CtlDataset,
        taxonomy_model=CtlDataset,
        filter_params=filter_params,
    )

    # If applicable, keep only unlinked datasets
    if only_unlinked_datasets:
        linked_datasets = select([DatasetConfig.ctl_dataset_id])
        filtered_query = filtered_query.where(not_(CtlDataset.id.in_(linked_datasets)))

    # If applicable, remove saas config datasets
    if exclude_saas_datasets:
        saas_subquery = (
            select([ConnectionConfig.saas_config["fides_key"].astext])
            .select_from(ConnectionConfig)  # type: ignore[arg-type]
            .where(ConnectionConfig.saas_config.is_not(None))  # type: ignore[attr-defined]
        )
        filtered_query = filtered_query.where(
            not_(CtlDataset.fides_key.in_(saas_subquery))
        )

    if not page and not size:
        return await list_resource_query(db, filtered_query, CtlDataset)

    pagination_params = Params(page=page or 1, size=size or 50)
    return await async_paginate(db, filtered_query, pagination_params)


async def create_with_key(data, model, db):
    """
    helper to create taxonomy resource when not given a fides_key
    """
    # If data with same name exists but is disabled, re-enable it
    disabled_resource_with_name = db.query(model).filter(
        model.key == data.name,
        model.active == False,
        )
    if disabled_resource_with_name:
        return model.update(db=db, data=disabled_resource_with_name, active=True)
    data.fides_key = get_key_from_data({"key": data.fides_key, "name": data.name}, model.__name__)
    return model.create(db=db, data=data.model_dump(mode="json"))


@data_use_router.post(
"/data_use",
    dependencies=[Security(verify_oauth_client, scopes=[DATA_USE_CREATE])],
    response_model=DataUse,
    status_code=status.HTTP_201_CREATED,
    name="Create",
)
async def create_data_use(
        data_use: DataUse,
        db: AsyncSession = Depends(get_async_db),
) -> Dict:
    """
    Create a data use. Updates existing data use if data use with key already exists and is disabled.
    """
    if data_use.fides_key is None:
        await create_with_key(data_use, DataUse, db)

    # add test that this fails if key already exists
    return await DataUse.create(db=db, data=data_use.model_dump(mode="json"))


@data_category_router.post(
    "/data_category",
    dependencies=[Security(verify_oauth_client, scopes=[DATA_CATEGORY_CREATE])],
    response_model=DataCategory,
    status_code=status.HTTP_201_CREATED,
    name="Create",
)
async def create_data_category(
        data_category: DataCategory,
        db: AsyncSession = Depends(get_async_db),
) -> Dict:
    """
    Create a data category
    """

    if data_category.fides_key is None:
        await create_with_key(data_category, DataCategory, db)

    # add test that this fails if key already exists
    return await DataCategory.create(db=db, data=data_category.model_dump(mode="json"))


@data_subject_router.post(
    "/data_subject",
    dependencies=[Security(verify_oauth_client, scopes=[DATA_SUBJECT_CREATE])],
    response_model=DataSubject,
    status_code=status.HTTP_201_CREATED,
    name="Create",
)
async def create_data_subject(
        data_subject: DataSubject,
        db: AsyncSession = Depends(get_async_db),
) -> Dict:
    """
    Create a data subject
    """

    if data_subject.fides_key is None:
        await create_with_key(data_subject, DataSubject, db)

    # add test that this fails if key already exists
    return await DataSubject.create(db=db, data=data_subject.model_dump(mode="json"))



GENERIC_OVERRIDES_ROUTER = APIRouter()
GENERIC_OVERRIDES_ROUTER.include_router(dataset_router)
GENERIC_OVERRIDES_ROUTER.include_router(data_use_router)
GENERIC_OVERRIDES_ROUTER.include_router(data_category_router)
GENERIC_OVERRIDES_ROUTER.include_router(data_subject_router)
