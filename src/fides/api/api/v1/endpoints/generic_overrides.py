from typing import Dict, List, Optional, Type, Union

from fastapi import APIRouter, Depends, HTTPException, Query, Security
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.async_sqlalchemy import paginate as async_paginate
from fideslang.models import Dataset
from sqlalchemy import not_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import select
from starlette import status
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY, HTTP_404_NOT_FOUND

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
    DataCategoryCreateOrUpdate,
    DataSubject,
    DataSubjectCreateOrUpdate,
    DataUse,
    DataUseCreateOrUpdate,
)
from fides.api.util.errors import ForbiddenIsDefaultTaxonomyError
from fides.api.util.filter_utils import apply_filters_to_query
from fides.common.api.scope_registry import (
    DATA_CATEGORY_CREATE,
    DATA_SUBJECT_CREATE,
    DATA_USE_CREATE,
    DATASET_READ, DATA_USE_UPDATE,
)
from fides.common.api.v1.urn_registry import V1_URL_PREFIX

from fides.api.models.sql_models import (  # type: ignore[attr-defined] # isort: skip
    Dataset as CtlDataset,
    DataCategory as DataCategoryDbModel,
    DataSubject as DataSubjectDbModel,
    DataUse as DataUseDbModel, ModelWithDefaultField,
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


def activate_taxonomy_parents(
    db: Session,
    model: Union[Type[DataCategoryDbModel], Type[DataUseDbModel], Type[DataSubjectDbModel]],
    data: Union[DataCategoryCreateOrUpdate, DataUseCreateOrUpdate, DataSubjectCreateOrUpdate],
) -> None:
    """
    Activates parents to match newly-active taxonomy node.
    """
    all_parents: List[str] = get_cumulative_parts_of_fides_key(data.fides_key)
    if all_parents:
        deactivated_parents: Optional[List[model]] = db.query(model).filter(
            model.fides_key.in_(all_parents),
            model.active.is_(False),
        ).all()
        for parent in deactivated_parents:
            parent.active = True
            parent.update(db=db, data=parent.model_dump(mode="json"))


def deactivate_taxonomy_descendants(
    db: Session,
    model: Union[
        Type[DataCategoryDbModel], Type[DataUseDbModel], Type[DataSubjectDbModel]
    ],
    parent_key: str
) -> None:
    """
    Recursively de-activates all descendants of a given taxonomy node.
    """
    # Get all immediate children
    children = db.query(model).filter(
        model.parent_key == parent_key
    ).all()

    for child in children:
        # Deactivate current child
        child.active = False
        child.update(db=db, data=child.model_dump(mode="json"))

        # Recursively deactivate all descendants of this child
        deactivate_taxonomy_descendants(db, model, child.fides_key)



def get_cumulative_parts_of_fides_key(fides_key: str) -> List[str]:
    """
    Given a parent key, returns the cumulative parts of the key. Useful for obtaining all parents of a given key.

    e.g. If parent key is test.hello.something, this method returns ["test", "test.hello", "test.hello.something"]
    """
    #
    parts = fides_key.split('.')
    cumulative_parts = []
    current = parts[0]
    cumulative_parts.append(current)

    for part in parts[1:]:
        current = current + '.' + part
        cumulative_parts.append(current)

    return cumulative_parts


def validate_and_create_taxonomy(
    db: Session,
    model: Union[
        Type[DataCategoryDbModel], Type[DataUseDbModel], Type[DataSubjectDbModel]
    ],
    validation_schema: type,
    data: Union[DataCategoryCreateOrUpdate, DataUseCreateOrUpdate, DataSubjectCreateOrUpdate],
) -> Dict:
    """
    Validate and create a taxonomy element.
    """
    if isinstance(model, ModelWithDefaultField) and data.is_default:
        raise ForbiddenIsDefaultTaxonomyError(
            model.__name__, data.fides_key, action="create"
        )
    validated_taxonomy = validation_schema(**data.model_dump(mode="json"))
    return model.create(db=db, data=validated_taxonomy.model_dump(mode="json"))


def validate_and_update_taxonomy(
    db: Session,
    model: Union[
        Type[DataCategoryDbModel], Type[DataUseDbModel], Type[DataSubjectDbModel]
    ],
    resource: Union[DataCategoryDbModel, DataUseDbModel, DataSubjectDbModel],
    validation_schema: type,
    data: Union[DataCategoryCreateOrUpdate, DataUseCreateOrUpdate, DataSubjectCreateOrUpdate],
) -> Dict:
    """
    Validate and update a taxonomy element.
    """
    if isinstance(resource, ModelWithDefaultField) and data.is_default:
        raise ForbiddenIsDefaultTaxonomyError(
            resource.__name__, data.fides_key, action="update"
        )
    # If active field is being updated, cascade change either up or down
    if hasattr(data, "active"):
        if data.active:
            activate_taxonomy_parents(db, model, data)
        else:
            # Cascade down - deactivate children to match newly-deactivated taxonomy item
            deactivate_taxonomy_descendants(db, model, data.fides_key)

    validated_taxonomy = validation_schema(**data.model_dump(mode="json"))
    return resource.update(db=db, data=validated_taxonomy.model_dump(mode="json"))


def create_or_update_taxonomy(
    db: Session,
    data: Union[DataCategoryCreateOrUpdate, DataUseCreateOrUpdate, DataSubjectCreateOrUpdate],
    model: Union[
        Type[DataCategoryDbModel], Type[DataUseDbModel], Type[DataSubjectDbModel]
    ],
    validation_schema: type,
) -> Dict:
    """
    Create or update a taxonomy element.
    If the element is deactivated, it will be updated and re-activated, along with its parents.
    """
    if data.fides_key is None:
        disabled_resource_with_name = (
            db.query(model)
            .filter(
                model.active.is_(False),
                model.name == data.name,
            )
            .first()
        )
        data.fides_key = get_key_from_data(
            {"key": data.fides_key, "name": data.name}, validation_schema.__name__
        )
        if data.parent_key if hasattr(data, "parent_key") else None:
            # Updates fides_key if it is not the root level taxonomy node
            data.fides_key = f"{data.parent_key}.{data.fides_key}"  # type: ignore[union-attr]
        if disabled_resource_with_name:
            data.active = True
            activate_taxonomy_parents(db, model, data)
            return validate_and_update_taxonomy(
                db, model, disabled_resource_with_name, validation_schema, data
            )
        return validate_and_create_taxonomy(db, model, validation_schema, data)

    return validate_and_create_taxonomy(db, model, validation_schema, data)


@data_use_router.post(
    "/data_use",
    dependencies=[Security(verify_oauth_client, scopes=[DATA_USE_CREATE])],
    response_model=DataUse,
    status_code=status.HTTP_201_CREATED,
    name="Create",
)
async def create_data_use(
    data_use: DataUseCreateOrUpdate,
    db: Session = Depends(get_db),
) -> Dict:
    """
    Create a data use. Updates existing data use if data use with name already exists and is disabled.
    """
    try:
        return create_or_update_taxonomy(db, data_use, DataUseDbModel, DataUse)
    except KeyOrNameAlreadyExists:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Data use with key {data_use.fides_key} or name {data_use.name} already exists.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error creating data use: {e}",
        )


@data_use_router.put(
    "/data_use",
    dependencies=[Security(verify_oauth_client, scopes=[DATA_USE_UPDATE])],
    response_model=DataUse,
    status_code=status.HTTP_201_CREATED,
    name="Update",
)
async def update_data_use(
        data_use: DataUseCreateOrUpdate,
        db: Session = Depends(get_db),
) -> Dict:
    """
    Update a data use. Ensures updates to "active" are appropriately cascaded.
    """
    try:
        resource = DataUseDbModel.get_by(db, field="fides_key", value=data_use.fides_key)
        if not resource:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND, detail=f"Data use not found with key: {data_use.fides_key}"
            )
        return validate_and_update_taxonomy(
            db, DataUseDbModel, resource, DataUse, data_use
        )
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error updating data use: {e}",
        )


@data_category_router.post(
    "/data_category",
    dependencies=[Security(verify_oauth_client, scopes=[DATA_CATEGORY_CREATE])],
    response_model=DataCategory,
    status_code=status.HTTP_201_CREATED,
    name="Create",
)
async def create_data_category(
    data_category: DataCategoryCreateOrUpdate,
    db: Session = Depends(get_db),
) -> Dict:
    """
    Create a data category
    """

    try:
        return create_or_update_taxonomy(
            db, data_category, DataCategoryDbModel, DataCategory
        )
    except KeyOrNameAlreadyExists:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Data category with key {data_category.fides_key} or name {data_category.name} already exists.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error creating data category: {e}",
        )


@data_subject_router.post(
    "/data_subject",
    dependencies=[Security(verify_oauth_client, scopes=[DATA_SUBJECT_CREATE])],
    response_model=DataSubject,
    status_code=status.HTTP_201_CREATED,
    name="Create",
)
async def create_data_subject(
    data_subject: DataSubjectCreateOrUpdate,
    db: Session = Depends(get_db),
) -> Dict:
    """
    Create a data subject
    """

    try:
        return create_or_update_taxonomy(
            db, data_subject, DataSubjectDbModel, DataSubject
        )
    except KeyOrNameAlreadyExists:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Data subject with key {data_subject.fides_key} or name {data_subject.name} already exists.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error creating data subject: {e}",
        )


GENERIC_OVERRIDES_ROUTER = APIRouter()
GENERIC_OVERRIDES_ROUTER.include_router(dataset_router)
GENERIC_OVERRIDES_ROUTER.include_router(data_use_router)
GENERIC_OVERRIDES_ROUTER.include_router(data_category_router)
GENERIC_OVERRIDES_ROUTER.include_router(data_subject_router)
