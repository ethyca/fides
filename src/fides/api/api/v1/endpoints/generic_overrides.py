from typing import Dict, List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query, Security
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.async_sqlalchemy import paginate as async_paginate
from fideslang.models import Dataset
from sqlalchemy import not_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import select
from starlette import status
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from fides.api.api.deps import get_db
from fides.api.common_exceptions import KeyOrNameAlreadyExists
from fides.api.db.base_class import get_key_from_data
from fides.api.db.crud import list_resource_query
from fides.api.db.ctl_session import get_async_db
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.oauth.utils import verify_oauth_client
from fides.api.schemas.filter_params import FilterParams
from fides.api.schemas.taxonomy_extensions import (
    DataCategory,
    DataCategoryCreate,
    DataSubject,
    DataSubjectCreate,
    DataUse,
    DataUseCreate,
)
from fides.api.util.filter_utils import apply_filters_to_query
from fides.common.api.scope_registry import (
    DATA_CATEGORY_CREATE,
    DATA_SUBJECT_CREATE,
    DATA_USE_CREATE,
    DATASET_READ,
)
from fides.common.api.v1.urn_registry import V1_URL_PREFIX

from fides.api.models.sql_models import (  # type: ignore[attr-defined] # isort: skip
    Dataset as CtlDataset,
    DataCategory as DataCategoryDbModel,
    DataSubject as DataSubjectDbModel,
    DataUse as DataUseDbModel,
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


@data_use_router.post(
    "/data_use",
    dependencies=[Security(verify_oauth_client, scopes=[DATA_USE_CREATE])],
    response_model=DataUse,
    status_code=status.HTTP_201_CREATED,
    name="Create",
)
async def create_data_use(
    data_use: DataUseCreate,
    db: Session = Depends(get_db),
) -> Dict:
    """
    Create a data use. Updates existing data use if data use with name already exists and is disabled.
    """
    if data_use.fides_key is None:
        disabled_resource_with_name = (
            db.query(DataUseDbModel)
            .filter(
                DataUseDbModel.active.is_(False),
                DataUseDbModel.name == data_use.name,
            )
            .first()
        )
        data_use.fides_key = get_key_from_data(
            {"key": data_use.fides_key, "name": data_use.name}, DataUse.__name__
        )
        if disabled_resource_with_name:
            data_use.active = True
            return disabled_resource_with_name.update(db, data=data_use.model_dump(mode="json"))  # type: ignore[union-attr]
        try:
            return DataUseDbModel.create(db=db, data=data_use.model_dump(mode="json"))  # type: ignore[union-attr]
        except KeyOrNameAlreadyExists:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Data use with key {data_use.fides_key} or name {data_use.name} already exists.",
            )
    return DataUseDbModel.create(db=db, data=data_use.model_dump(mode="json"))


@data_category_router.post(
    "/data_category",
    dependencies=[Security(verify_oauth_client, scopes=[DATA_CATEGORY_CREATE])],
    response_model=DataCategory,
    status_code=status.HTTP_201_CREATED,
    name="Create",
)
async def create_data_category(
    data_category: DataCategoryCreate,
    db: Session = Depends(get_db),
) -> Dict:
    """
    Create a data category
    """

    if data_category.fides_key is None:
        disabled_resource_with_name = (
            db.query(DataCategoryDbModel)
            .filter(
                DataCategoryDbModel.active.is_(False),
                DataCategoryDbModel.name == data_category.name,
            )
            .first()
        )
        data_category.fides_key = get_key_from_data(
            {"key": data_category.fides_key, "name": data_category.name},
            DataCategory.__name__,
        )
        if disabled_resource_with_name:
            data_category.active = True
            return disabled_resource_with_name.update(db, data=data_category.model_dump(mode="json"))  # type: ignore[union-attr]
        try:
            return DataCategoryDbModel.create(db=db, data=data_category.model_dump(mode="json"))  # type: ignore[union-attr]
        except KeyOrNameAlreadyExists:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Data category with key {data_category.fides_key} or name {data_category.name} already exists.",
            )
    return DataCategoryDbModel.create(db=db, data=data_category.model_dump(mode="json"))


@data_subject_router.post(
    "/data_subject",
    dependencies=[Security(verify_oauth_client, scopes=[DATA_SUBJECT_CREATE])],
    response_model=DataSubject,
    status_code=status.HTTP_201_CREATED,
    name="Create",
)
async def create_data_subject(
    data_subject: DataSubjectCreate,
    db: Session = Depends(get_db),
) -> Dict:
    """
    Create a data subject
    """

    if data_subject.fides_key is None:
        disabled_resource_with_name = (
            db.query(DataSubjectDbModel)
            .filter(
                DataSubjectDbModel.active.is_(False),
                DataSubjectDbModel.name == data_subject.name,
            )
            .first()
        )
        data_subject.fides_key = get_key_from_data(
            {"key": data_subject.fides_key, "name": data_subject.name},
            DataSubject.__name__,
        )
        if disabled_resource_with_name:
            data_subject.active = True
            return disabled_resource_with_name.update(db, data=data_subject.model_dump(mode="json"))  # type: ignore[union-attr]
        try:
            return DataSubjectDbModel.create(db=db, data=data_subject.model_dump(mode="json"))  # type: ignore[union-attr]
        except KeyOrNameAlreadyExists:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Data subject with key {data_subject.fides_key} or name {data_subject.name} already exists.",
            )
    return DataSubjectDbModel.create(db=db, data=data_subject.model_dump(mode="json"))


GENERIC_OVERRIDES_ROUTER = APIRouter()
GENERIC_OVERRIDES_ROUTER.include_router(dataset_router)
GENERIC_OVERRIDES_ROUTER.include_router(data_use_router)
GENERIC_OVERRIDES_ROUTER.include_router(data_category_router)
GENERIC_OVERRIDES_ROUTER.include_router(data_subject_router)
