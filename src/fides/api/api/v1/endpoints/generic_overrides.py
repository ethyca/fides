from functools import partial
from typing import Dict, List, Optional, Type, Union

from fastapi import Depends, HTTPException, Query, Response, Security
from fastapi.concurrency import run_in_threadpool
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.async_sqlalchemy import paginate as async_paginate
from fideslang.models import Dataset as FideslangDataset
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy import not_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, load_only
from starlette import status
from starlette.status import (
    HTTP_200_OK,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from fides.api.api.deps import get_db
from fides.api.common_exceptions import KeyOrNameAlreadyExists, ValidationError
from fides.api.db.base_class import get_key_from_data
from fides.api.db.crud import list_resource_query
from fides.api.db.ctl_session import get_async_db
from fides.api.models.connectionconfig import ConnectionConfig, ConnectionType
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.oauth.utils import verify_oauth_client
from fides.api.schemas.dataset import DatasetResponse
from fides.api.schemas.filter_params import FilterParams
from fides.api.schemas.taxonomy_extensions import (
    DataCategory,
    DataCategoryCreateOrUpdate,
    DataSubject,
    DataSubjectCreateOrUpdate,
    DataUse,
    DataUseCreateOrUpdate,
)
from fides.api.service.deps import get_dataset_service
from fides.api.util.api_router import APIRouter
from fides.api.util.errors import FidesError, ForbiddenIsDefaultTaxonomyError
from fides.api.util.filter_utils import apply_filters_to_query
from fides.common.api.scope_registry import (
    CTL_DATASET_CREATE,
    CTL_DATASET_DELETE,
    CTL_DATASET_READ,
    CTL_DATASET_UPDATE,
    DATA_CATEGORY_CREATE,
    DATA_CATEGORY_UPDATE,
    DATA_SUBJECT_CREATE,
    DATA_USE_CREATE,
    DATA_USE_UPDATE,
)
from fides.common.api.v1.urn_registry import DATASETS_CLEAN, V1_URL_PREFIX
from fides.service.dataset.dataset_service import (
    DatasetNotFoundException,
    DatasetService,
)

from fides.api.models.sql_models import (  # type: ignore[attr-defined] # isort: skip
    Dataset as CtlDataset,
)

from fides.api.models.sql_models import (  # type: ignore[attr-defined] # isort: skip
    DataCategory as DataCategoryDbModel,
    DataSubject as DataSubjectDbModel,
    DataUse as DataUseDbModel,
    ModelWithDefaultField,
)

# We create routers to override specific methods in those defined in generic.py
# when we need more custom implementations for only some of the methods in a router.

dataset_router = APIRouter(tags=["Dataset"], prefix=V1_URL_PREFIX)
data_use_router = APIRouter(tags=["DataUse"], prefix=V1_URL_PREFIX)
data_category_router = APIRouter(tags=["DataCategory"], prefix=V1_URL_PREFIX)
data_subject_router = APIRouter(tags=["DataSubject"], prefix=V1_URL_PREFIX)


@dataset_router.post(
    "/dataset",
    dependencies=[Security(verify_oauth_client, scopes=[CTL_DATASET_CREATE])],
    response_model=FideslangDataset,
    status_code=status.HTTP_201_CREATED,
    name="Create dataset",
)
async def create_dataset(
    dataset: FideslangDataset,
    dataset_service: DatasetService = Depends(get_dataset_service),
) -> Dict:
    """Create a new dataset"""
    try:
        return dataset_service.create_dataset(dataset)
    except (ValidationError, PydanticValidationError) as exc:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=jsonable_encoder(
                exc.errors(include_url=False, include_input=False)
                if isinstance(exc, PydanticValidationError)
                else exc.message
            ),
        )
    except KeyOrNameAlreadyExists as exc:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )


@dataset_router.put(
    "/dataset",
    dependencies=[Security(verify_oauth_client, scopes=[CTL_DATASET_UPDATE])],
    response_model=FideslangDataset,
    status_code=status.HTTP_200_OK,
    name="Update dataset",
)
async def update_dataset(
    dataset: FideslangDataset,
    dataset_service: DatasetService = Depends(get_dataset_service),
) -> Dict:
    """Update an existing dataset"""
    try:
        return dataset_service.update_dataset(dataset)
    except (ValidationError, PydanticValidationError) as exc:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=jsonable_encoder(
                exc.errors(include_url=False, include_input=False)
                if isinstance(exc, PydanticValidationError)
                else exc.message
            ),
        )
    except DatasetNotFoundException as e:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail={"message": str(e)},
        )


@dataset_router.get(
    "/dataset",
    dependencies=[Security(verify_oauth_client, scopes=[CTL_DATASET_READ])],
    response_model=Union[Page[DatasetResponse], List[DatasetResponse]],
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
    connection_type: Optional[ConnectionType] = Query(None),
    minimal: Optional[bool] = Query(False),
) -> Union[Page[DatasetResponse], List[DatasetResponse]]:
    """
    Get a list of all of the Datasets.
    If any pagination parameters (size or page) are provided, then the response will be paginated.
    Otherwise all Datasets will be returned (this may be a slow operation if there are many datasets,
    so using the pagination parameters is recommended).
    Provided filters (search, data_categories, exclude_saas_datasets, only_unlinked_datasets) will be applied,
    returning only the datasets that match ALL of the filters.
    """

    query = select(CtlDataset)

    if minimal:
        # .options() allows us to modify how the query loads data by configuring the query's loading behavior
        # load_only() optimizes the query by only loading the specified columns from the database
        # This reduces memory usage and query time by not loading unnecessary columns
        # The columns specified below are the minimal set needed for the DatasetResponse model
        query = query.options(  # type: ignore[attr-defined]
            load_only(
                CtlDataset.id,
                CtlDataset.fides_key,
                CtlDataset.organization_fides_key,
                CtlDataset.name,
                CtlDataset.created_at,
                CtlDataset.updated_at,
                CtlDataset.meta,
                CtlDataset.fides_meta,
                CtlDataset.description,
            )
        )

    # Add filters for search and data categories
    filter_params = FilterParams(search=search, data_categories=data_categories)
    filtered_query = apply_filters_to_query(
        query=query,
        search_model=CtlDataset,
        taxonomy_model=CtlDataset,
        filter_params=filter_params,
    )

    # If applicable, filter by connection type
    if connection_type:
        filtered_query = filtered_query.where(
            CtlDataset.fides_meta["namespace"]["connection_type"].as_string()
            == connection_type.value
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
        results = await list_resource_query(db, filtered_query, CtlDataset)
        response = [
            DatasetResponse.model_validate(result.__dict__) for result in results
        ]
        return response

    pagination_params = Params(page=page or 1, size=size or 50)
    results = await async_paginate(db, filtered_query, pagination_params)

    validated_items = []
    for result in results.items:  # type: ignore[attr-defined]
        # run pydantic validation in a threadpool to avoid blocking the main thread
        validated_item = await run_in_threadpool(
            partial(DatasetResponse.model_validate, result.__dict__)
        )
        validated_items.append(validated_item)

    results.items = validated_items  # type: ignore[attr-defined]

    return results


@dataset_router.get(
    "/dataset/{fides_key}",
    dependencies=[Security(verify_oauth_client, scopes=[CTL_DATASET_READ])],
    response_model=FideslangDataset,
    name="Get dataset",
)
async def get_dataset(
    fides_key: str,
    dataset_service: DatasetService = Depends(get_dataset_service),
) -> Dict:
    """Get a single dataset by fides key"""
    try:
        return dataset_service.get_dataset(fides_key)
    except DatasetNotFoundException as e:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail={"message": str(e)},
        )


@dataset_router.delete(
    "/dataset/{fides_key}",
    dependencies=[Security(verify_oauth_client, scopes=[CTL_DATASET_DELETE])],
    name="Delete dataset",
)
async def delete_dataset(
    fides_key: str,
    dataset_service: DatasetService = Depends(get_dataset_service),
) -> JSONResponse:
    """Delete a dataset by fides key"""
    try:
        dataset = dataset_service.delete_dataset(fides_key)
        return JSONResponse(
            content={
                "message": "resource deleted",
                "resource": FideslangDataset.model_validate(dataset).model_dump(
                    mode="json"
                ),
            },
        )
    except DatasetNotFoundException as e:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail={"message": str(e)},
        )


@dataset_router.post(
    "/dataset/upsert",
    dependencies=[
        Security(
            verify_oauth_client,
            scopes=[CTL_DATASET_CREATE, CTL_DATASET_UPDATE],
        )
    ],
)
async def upsert_datasets(
    datasets: List[FideslangDataset],
    response: Response,
    dataset_service: DatasetService = Depends(get_dataset_service),
) -> Dict:
    """
    For any dataset in `datasets` that already exists in the database,
    update the dataset by its `fides_key`. Otherwise, create a new dataset.

    Responds with a `201 Created` if even a single dataset in `datasets`
    did not previously exist. Otherwise, responds with a `200 OK`.
    """
    try:
        inserted, updated = dataset_service.upsert_datasets(datasets)

        response.status_code = (
            status.HTTP_201_CREATED if inserted > 0 else response.status_code
        )

        return {
            "message": f"Upserted {len(datasets)} Dataset(s)",
            "inserted": inserted,
            "updated": updated,
        }
    except (ValidationError, PydanticValidationError) as exc:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=jsonable_encoder(
                exc.errors(include_url=False, include_input=False)
                if isinstance(exc, PydanticValidationError)
                else exc.message
            ),
        )


@dataset_router.get(
    DATASETS_CLEAN,
    dependencies=[Security(verify_oauth_client, scopes=[CTL_DATASET_READ])],
    response_model=List[FideslangDataset],
    deprecated=True,
)
def clean_datasets(
    dataset_service: DatasetService = Depends(get_dataset_service),
) -> JSONResponse:
    """
    Clean up names of datasets and upsert them.
    """

    succeeded, failed = dataset_service.clean_datasets()
    return JSONResponse(
        status_code=HTTP_200_OK,
        content={
            "succeeded": succeeded,
            "failed": failed,
        },
    )


def activate_taxonomy_parents(
    resource: Union[DataCategoryDbModel, DataUseDbModel, DataSubjectDbModel],
    db: Session,
) -> None:
    """
    Activates parents to match newly-active taxonomy node.
    """
    parent = resource.parent
    if parent:
        parent.active = True
        db.commit()

        activate_taxonomy_parents(parent, db)


def deactivate_taxonomy_node_and_descendants(
    resource: Union[DataCategoryDbModel, DataUseDbModel, DataSubjectDbModel],
    db: Session,
) -> None:
    """
    Recursively de-activates all descendants of a given taxonomy node.
    """
    resource.active = False
    db.commit()
    children = resource.children

    for child in children:
        # Deactivate current child
        child.active = False
        db.commit()

        # Recursively deactivate all descendants of this child
        deactivate_taxonomy_node_and_descendants(child, db)


def validate_and_create_taxonomy(
    db: Session,
    model: Union[
        Type[DataCategoryDbModel], Type[DataUseDbModel], Type[DataSubjectDbModel]
    ],
    validation_schema: type,
    data: Union[
        DataCategoryCreateOrUpdate, DataUseCreateOrUpdate, DataSubjectCreateOrUpdate
    ],
) -> Dict:
    """
    Validate and create a taxonomy element.
    """
    if not data.fides_key:
        raise FidesError(f"Fides key is required to create a {model.__name__} resource")
    if isinstance(data, ModelWithDefaultField) and data.is_default:
        raise ForbiddenIsDefaultTaxonomyError(
            model.__name__, data.fides_key, action="create"
        )
    validated_taxonomy = validation_schema(**data.model_dump(mode="json"))
    return model.create(db=db, data=validated_taxonomy.model_dump(mode="json"))


def validate_and_update_taxonomy(
    db: Session,
    resource: Union[DataCategoryDbModel, DataUseDbModel, DataSubjectDbModel],
    validation_schema: type,
    data: Union[
        DataCategoryCreateOrUpdate, DataUseCreateOrUpdate, DataSubjectCreateOrUpdate
    ],
) -> Dict:
    """
    Validate and update a taxonomy element.
    """
    if (
        isinstance(data, ModelWithDefaultField)
        and data.is_default != resource.is_default
    ):
        raise ForbiddenIsDefaultTaxonomyError(
            "resource", data.fides_key, action="modify"
        )

    # If active field is being updated, cascade change either up or down
    if hasattr(data, "active"):
        if data.active:
            activate_taxonomy_parents(resource, db)
        else:
            # Cascade down - deactivate current node and children to match newly-deactivated taxonomy item
            deactivate_taxonomy_node_and_descendants(resource, db)

    validated_taxonomy = validation_schema(**data.model_dump(mode="json"))
    return resource.update(db=db, data=validated_taxonomy.model_dump(mode="json"))


def create_or_update_taxonomy(
    db: Session,
    data: Union[
        DataCategoryCreateOrUpdate, DataUseCreateOrUpdate, DataSubjectCreateOrUpdate
    ],
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
            activate_taxonomy_parents(disabled_resource_with_name, db)
            return validate_and_update_taxonomy(
                db, disabled_resource_with_name, validation_schema, data
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
    except PydanticValidationError as e:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
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


@data_use_router.put(
    "/data_use",
    dependencies=[Security(verify_oauth_client, scopes=[DATA_USE_UPDATE])],
    response_model=DataUse,
    status_code=status.HTTP_200_OK,
    name="Update",
)
async def update_data_use(
    data_use: DataUseCreateOrUpdate,
    db: Session = Depends(get_db),
) -> Dict:
    """
    Update a data use. Ensures updates to "active" are appropriately cascaded.
    """

    resource = DataUseDbModel.get_by(db, field="fides_key", value=data_use.fides_key)
    if not resource:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Data use not found with key: {data_use.fides_key}",
        )
    return validate_and_update_taxonomy(db, resource, DataUse, data_use)


@data_category_router.put(
    "/data_category",
    dependencies=[Security(verify_oauth_client, scopes=[DATA_CATEGORY_UPDATE])],
    response_model=DataCategory,
    status_code=status.HTTP_200_OK,
    name="Update",
)
async def update_data_category(
    data_category: DataCategoryCreateOrUpdate,
    db: Session = Depends(get_db),
) -> Dict:
    """
    Update a data category. Ensures updates to "active" are appropriately cascaded.
    """

    resource = DataCategoryDbModel.get_by(
        db, field="fides_key", value=data_category.fides_key
    )
    if not resource:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Data category not found with key: {data_category.fides_key}",
        )
    return validate_and_update_taxonomy(db, resource, DataCategory, data_category)


GENERIC_OVERRIDES_ROUTER = APIRouter()
GENERIC_OVERRIDES_ROUTER.include_router(dataset_router)
GENERIC_OVERRIDES_ROUTER.include_router(data_use_router)
GENERIC_OVERRIDES_ROUTER.include_router(data_category_router)
GENERIC_OVERRIDES_ROUTER.include_router(data_subject_router)
