from typing import Annotated, Any, Dict, List, Optional

import yaml
from fastapi import Depends, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.params import Security
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from fideslang.models import Dataset as FideslangDataset
from fideslang.validation import FidesKey
from loguru import logger
from pydantic import Field
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy import and_, not_, select
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_415_UNSUPPORTED_MEDIA_TYPE,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from fides.api.api import deps
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.policy import Policy
from fides.api.oauth.utils import verify_oauth_client
from fides.api.schemas.dataset import (
    BulkPutDataset,
    DatasetConfigCtlDataset,
    DatasetConfigSchema,
    DatasetReachability,
    ValidateDatasetResponse,
)
from fides.api.schemas.privacy_request import TestPrivacyRequest
from fides.api.schemas.redis_cache import DatasetTestRequest
from fides.api.service.deps import get_dataset_config_service
from fides.api.util.api_router import APIRouter
from fides.common.api.scope_registry import (
    DATASET_CREATE_OR_UPDATE,
    DATASET_DELETE,
    DATASET_READ,
    DATASET_TEST,
)
from fides.common.api.v1.urn_registry import (
    CONNECTION_DATASETS,
    DATASET_BY_KEY,
    DATASET_CONFIG_BY_KEY,
    DATASET_CONFIGS,
    DATASET_INPUTS,
    DATASET_REACHABILITY,
    DATASET_VALIDATE,
    DATASETS,
    TEST_DATASET,
    V1_URL_PREFIX,
    YAML_DATASETS,
)
from fides.config import CONFIG
from fides.service.dataset.dataset_config_service import DatasetConfigService
from fides.service.dataset.dataset_service import DatasetNotFoundException

from fides.api.models.sql_models import (  # type: ignore[attr-defined] # isort: skip
    Dataset as CtlDataset,
)

X_YAML = "application/x-yaml"
MAX_DATASET_CONFIGS_FOR_INTEGRATION_FORM = 1000

router = APIRouter(tags=["Dataset Configs"], prefix=V1_URL_PREFIX)


# Custom Params class with higher limit for dataset configs
class DatasetConfigParams(Params):
    size: int = Query(
        50, ge=1, le=MAX_DATASET_CONFIGS_FOR_INTEGRATION_FORM, description="Page size"
    )


# Helper method to inject the parent ConnectionConfig into these child routes
def _get_connection_config(
    connection_key: FidesKey, db: Session = Depends(deps.get_db)
) -> ConnectionConfig:
    logger.debug("Finding connection config with key '{}'", connection_key)
    connection_config = ConnectionConfig.get_by(db, field="key", value=connection_key)
    if not connection_config:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No connection config with key '{connection_key}'",
        )
    return connection_config


@router.put(
    DATASET_VALIDATE,
    dependencies=[Security(verify_oauth_client, scopes=[DATASET_READ])],
    status_code=HTTP_200_OK,
    response_model=ValidateDatasetResponse,
)
def validate_dataset(
    dataset: FideslangDataset,
    dataset_config_service: DatasetConfigService = Depends(get_dataset_config_service),
    connection_config: ConnectionConfig = Depends(_get_connection_config),
) -> ValidateDatasetResponse:
    """
    Run validations against a dataset without attempting to save it to the database.

    Checks that:
    - all required fields are present, all field values are valid types
    - all DataCategory values reference known keys
    - etc.

    After validating, also tests to see if the dataset is traversable. Note that
    it's possible for a dataset to be valid but not traversable; this happens
    when a dataset is dependent on references to other datasets.

    Returns a 200 OK for all valid datasets, and a traversal_details object with
    information about the traversal (or traversal errors).
    """

    try:
        return dataset_config_service.validate_dataset_config(
            connection_config, dataset
        )
    except PydanticValidationError as e:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=jsonable_encoder(e.errors(include_url=False, include_input=False)),
        )


@router.put(
    DATASET_CONFIGS,
    dependencies=[Security(verify_oauth_client, scopes=[DATASET_CREATE_OR_UPDATE])],
    status_code=HTTP_200_OK,
    response_model=BulkPutDataset,
)
def put_dataset_configs(
    dataset_pairs: Annotated[List[DatasetConfigCtlDataset], Field(max_length=MAX_DATASET_CONFIGS_FOR_INTEGRATION_FORM)],  # type: ignore
    db: Session = Depends(deps.get_db),
    dataset_config_service: DatasetConfigService = Depends(get_dataset_config_service),
    connection_config: ConnectionConfig = Depends(_get_connection_config),
) -> BulkPutDataset:
    """
    Endpoint to create, update, or remove DatasetConfigs by passing in pairs of:
    1) A DatasetConfig fides_key
    2) The corresponding CtlDataset fides_key which stores the bulk of the actual dataset

    The CtlDataset contents are retrieved for extra validation before linking this
    to the DatasetConfig.

    Note: Any existing DatasetConfigs not specified in the dataset pairs will be deleted.
    """

    # first delete any dataset configs not in the dataset pairs
    existing_config_keys = set(
        db.execute(
            select([DatasetConfig.fides_key]).where(
                DatasetConfig.connection_config_id == connection_config.id
            )
        )
        .scalars()
        .all()
    )

    requested_config_keys = {pair.fides_key for pair in dataset_pairs}
    config_keys_to_remove = existing_config_keys - requested_config_keys

    if config_keys_to_remove:
        db.query(DatasetConfig).filter(
            DatasetConfig.connection_config_id == connection_config.id,
            DatasetConfig.fides_key.in_(config_keys_to_remove),
        ).delete(synchronize_session=False)
        db.commit()

    # reuse the existing patch logic once we've removed the unused dataset configs
    return patch_dataset_configs(
        dataset_pairs, dataset_config_service, connection_config
    )


@router.patch(
    DATASET_CONFIGS,
    dependencies=[Security(verify_oauth_client, scopes=[DATASET_CREATE_OR_UPDATE])],
    status_code=HTTP_200_OK,
    response_model=BulkPutDataset,
)
def patch_dataset_configs(
    dataset_pairs: Annotated[List[DatasetConfigCtlDataset], Field(max_length=MAX_DATASET_CONFIGS_FOR_INTEGRATION_FORM)],  # type: ignore
    dataset_config_service: DatasetConfigService = Depends(get_dataset_config_service),
    connection_config: ConnectionConfig = Depends(_get_connection_config),
) -> BulkPutDataset:
    """
    Endpoint to create or update DatasetConfigs by passing in pairs of:
    1) A DatasetConfig fides_key
    2) The corresponding CtlDataset fides_key which stores the bulk of the actual dataset

    The CtlDataset contents are retrieved for extra validation before linking this
    to the DatasetConfig.
    """
    try:
        return dataset_config_service.bulk_create_or_update_dataset_configs(
            connection_config,
            dataset_pairs,
        )
    except DatasetNotFoundException as e:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except PydanticValidationError as e:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=jsonable_encoder(e.errors(include_url=False, include_input=False)),
        )


@router.patch(
    CONNECTION_DATASETS,
    dependencies=[Security(verify_oauth_client, scopes=[DATASET_CREATE_OR_UPDATE])],
    status_code=HTTP_200_OK,
    response_model=BulkPutDataset,
)
def patch_datasets(
    datasets: Annotated[List[FideslangDataset], Field(max_length=1000)],  # type: ignore
    dataset_config_service: DatasetConfigService = Depends(get_dataset_config_service),
    connection_config: ConnectionConfig = Depends(_get_connection_config),
) -> BulkPutDataset:
    """
    Given a list of dataset elements, create or update corresponding Dataset objects
    or report failure

    This endpoint upserts the DatasetConfig and associated CTL Dataset.  Will shortly be deprecated.

    If the fides_key for a given DatasetConfig exists, it will be treated as an update.
    Otherwise, a new DatasetConfig will be created.
    """

    try:
        return dataset_config_service.bulk_create_or_update_dataset_configs(
            connection_config, datasets
        )
    except PydanticValidationError as e:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=jsonable_encoder(e.errors(include_url=False, include_input=False)),
        )


@router.patch(
    YAML_DATASETS,
    dependencies=[Security(verify_oauth_client, scopes=[DATASET_CREATE_OR_UPDATE])],
    status_code=HTTP_200_OK,
    response_model=BulkPutDataset,
)
async def patch_yaml_datasets(
    request: Request,
    dataset_config_service: DatasetConfigService = Depends(get_dataset_config_service),
    connection_config: ConnectionConfig = Depends(_get_connection_config),
) -> BulkPutDataset:
    """
    Bulk create or update datasets from YAML format.
    Accepts application/x-yaml content type.
    """
    if request.headers.get("content-type") != X_YAML:
        raise HTTPException(
            status_code=HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Content type must be {X_YAML}",
        )

    try:
        # Read and parse YAML content
        body = await request.body()
        yaml_request_body = yaml.safe_load(body)

        # Convert YAML datasets to Dataset objects
        datasets = [
            FideslangDataset.model_validate(dataset_dict)
            for dataset_dict in yaml_request_body["dataset"]
        ]

        return dataset_config_service.bulk_create_or_update_dataset_configs(
            connection_config, datasets
        )

    except yaml.MarkedYAMLError as e:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Invalid YAML format: {str(e)}",
        )
    except PydanticValidationError as e:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Dataset validation failed: {str(e)}",
        )


@router.get(
    CONNECTION_DATASETS,
    dependencies=[Security(verify_oauth_client, scopes=[DATASET_READ])],
    response_model=Page[FideslangDataset],
    deprecated=True,
)
def get_datasets(
    db: Session = Depends(deps.get_db),
    params: Params = Depends(),
    connection_config: ConnectionConfig = Depends(_get_connection_config),
) -> AbstractPage[FideslangDataset]:
    """Returns all CTL datasets attached to the ConnectionConfig via the Dataset Config.

    Soon to be deprecated.
    """

    logger.debug(
        "Finding all datasets for connection '{}' with pagination params {}",
        connection_config.key,
        params,
    )
    dataset_configs = DatasetConfig.filter(
        db=db, conditions=(DatasetConfig.connection_config_id == connection_config.id)
    ).order_by(DatasetConfig.created_at.desc())

    # Generate the paginated results, but don't return them as-is. Instead,
    # modify the items array to be just the Dataset instead of the full
    # DatasetConfig. This has to be done *afterwards* to ensure that the
    # paginated query is handled by paginate()
    paginated_results = paginate(dataset_configs, params=params)
    paginated_results.items = [  # type: ignore
        dataset_config.ctl_dataset for dataset_config in paginated_results.items  # type: ignore
    ]
    return paginated_results


@router.get(
    DATASET_BY_KEY,
    dependencies=[Security(verify_oauth_client, scopes=[DATASET_READ])],
    response_model=FideslangDataset,
    deprecated=True,
)
def get_dataset(
    dataset_key: FidesKey,
    db: Session = Depends(deps.get_db),
    connection_config: ConnectionConfig = Depends(_get_connection_config),
) -> FideslangDataset:
    """Returns a single ctl dataset linked to the given DatasetConfig.

    Soon to be deprecated
    """

    logger.debug(
        "Finding dataset '{}' for connection '{}'", dataset_key, connection_config.key
    )
    dataset_config = DatasetConfig.filter(
        db=db,
        conditions=(
            (DatasetConfig.connection_config_id == connection_config.id)
            & (DatasetConfig.fides_key == dataset_key)
        ),
    ).first()
    if not dataset_config:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No dataset with fides_key '{dataset_key}' and connection key {connection_config.key}'",
        )
    return dataset_config.ctl_dataset


@router.get(
    DATASET_CONFIGS,
    dependencies=[Security(verify_oauth_client, scopes=[DATASET_READ])],
    response_model=Page[DatasetConfigSchema],
)
def get_dataset_configs(
    db: Session = Depends(deps.get_db),
    params: DatasetConfigParams = Depends(),
    connection_config: ConnectionConfig = Depends(_get_connection_config),
) -> AbstractPage[DatasetConfig]:
    """Returns all Dataset Configs attached to current Connection Config."""

    logger.debug(
        "Finding all dataset configs for connection '{}' with pagination params {}",
        connection_config.key,
        params,
    )
    dataset_configs = DatasetConfig.filter(
        db=db, conditions=(DatasetConfig.connection_config_id == connection_config.id)
    ).order_by(DatasetConfig.created_at.desc())

    return paginate(dataset_configs, params)


@router.get(
    DATASET_CONFIG_BY_KEY,
    dependencies=[Security(verify_oauth_client, scopes=[DATASET_READ])],
    response_model=DatasetConfigSchema,
)
def get_dataset_config(
    dataset_key: FidesKey,
    db: Session = Depends(deps.get_db),
    connection_config: ConnectionConfig = Depends(_get_connection_config),
) -> DatasetConfig:
    """Returns the specific Dataset Config linked to the Connection Config."""

    logger.debug(
        "Finding dataset config '{}' for connection '{}'",
        dataset_key,
        connection_config.key,
    )
    dataset_config = DatasetConfig.filter(
        db=db,
        conditions=(
            (DatasetConfig.connection_config_id == connection_config.id)
            & (DatasetConfig.fides_key == dataset_key)
        ),
    ).first()
    if not dataset_config:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No dataset config with fides_key '{dataset_key}' and connection key {connection_config.key}'",
        )
    return dataset_config


@router.delete(
    DATASET_BY_KEY,
    dependencies=[Security(verify_oauth_client, scopes=[DATASET_DELETE])],
    status_code=HTTP_204_NO_CONTENT,
)
def delete_dataset(
    dataset_key: FidesKey,
    *,
    db: Session = Depends(deps.get_db),
    connection_config: ConnectionConfig = Depends(_get_connection_config),
) -> None:
    """Removes the DatasetConfig based on the given key."""

    logger.info(
        "Finding dataset '{}' for connection '{}'", dataset_key, connection_config.key
    )
    dataset_config = DatasetConfig.filter(
        db=db,
        conditions=(
            (DatasetConfig.connection_config_id == connection_config.id)
            & (DatasetConfig.fides_key == dataset_key)
        ),
    ).first()
    if not dataset_config:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No dataset with fides_key '{dataset_key}' and connection_key '{connection_config.key}'",
        )

    logger.info(
        "Deleting dataset '{}' for connection '{}'", dataset_key, connection_config.key
    )
    dataset_config.delete(db)


@router.get(
    f"/filter{DATASETS}",
    dependencies=[Security(verify_oauth_client, scopes=[DATASET_READ])],
    response_model=List[FideslangDataset],
    deprecated=True,
)
def get_ctl_datasets(
    db: Session = Depends(deps.get_db),
    remove_saas_datasets: bool = True,
    only_unlinked_datasets: bool = False,
) -> List[FideslangDataset]:
    """
    Deprecated. Use `GET /datasets` instead.
    Returns all CTL datasets .
    """

    logger.debug(
        f"Finding all datasets {remove_saas_datasets=} {only_unlinked_datasets=}"
    )
    filters = []
    if only_unlinked_datasets:
        unlinked_subquery = select([DatasetConfig.ctl_dataset_id])
        filters.append(not_(CtlDataset.id.in_(unlinked_subquery)))

    if remove_saas_datasets:
        saas_subquery = (
            select([ConnectionConfig.saas_config["fides_key"].astext])
            .select_from(ConnectionConfig)  # type: ignore[arg-type]
            .where(ConnectionConfig.saas_config.is_not(None))  # type: ignore[attr-defined]
        )
        filters.append(not_(CtlDataset.fides_key.in_(saas_subquery)))

    conditions = []

    if len(filters) > 0:
        if len(filters) == 1:
            conditions.append(filters[0])
        else:
            conditions.append(and_(*filters))

    query = db.query(CtlDataset).filter(*conditions).order_by(CtlDataset.name.desc())
    datasets = query.all()

    return datasets


@router.get(
    DATASET_INPUTS,
    dependencies=[Security(verify_oauth_client, scopes=[DATASET_READ])],
)
def dataset_identities_and_references(
    *,
    db: Session = Depends(deps.get_db),
    connection_config: ConnectionConfig = Depends(_get_connection_config),
    dataset_key: FidesKey,
) -> Dict[str, Any]:
    """
    Returns a dictionary containing the immediate identity and dataset reference
    dependencies for the given dataset.
    """

    dataset_config = DatasetConfig.filter(
        db=db,
        conditions=(
            (DatasetConfig.connection_config_id == connection_config.id)
            & (DatasetConfig.fides_key == dataset_key)
        ),
    ).first()
    if not dataset_config:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No dataset config with fides_key '{dataset_key}'",
        )

    inputs = dataset_config.get_identities_and_references()
    return {input: None for input in inputs}


@router.get(
    DATASET_REACHABILITY,
    dependencies=[Security(verify_oauth_client, scopes=[DATASET_READ])],
    response_model=DatasetReachability,
)
def dataset_reachability(
    *,
    db: Session = Depends(deps.get_db),
    connection_config: ConnectionConfig = Depends(_get_connection_config),
    dataset_config_service: DatasetConfigService = Depends(get_dataset_config_service),
    dataset_key: FidesKey,
    policy_key: Optional[FidesKey] = None,
) -> Dict[str, Any]:
    """
    Returns a dictionary containing the immediate identity and dataset reference
    dependencies for the given dataset.
    """

    dataset_config = DatasetConfig.filter(
        db=db,
        conditions=(
            (DatasetConfig.connection_config_id == connection_config.id)
            & (DatasetConfig.fides_key == dataset_key)
        ),
    ).first()
    if not dataset_config:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No dataset config with fides_key '{dataset_key}'",
        )

    access_policy = (
        Policy.get_by(db, field="key", value=policy_key) if policy_key else None
    )
    if policy_key and not access_policy:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f'Policy with key "{policy_key}" not found',
        )

    reachable, details = dataset_config_service.get_dataset_reachability(
        dataset_config, access_policy
    )
    return {"reachable": reachable, "details": details}


@router.post(
    TEST_DATASET,
    status_code=HTTP_200_OK,
    dependencies=[Security(verify_oauth_client, scopes=[DATASET_TEST])],
    response_model=TestPrivacyRequest,
)
def test_connection_datasets(
    *,
    db: Session = Depends(deps.get_db),
    dataset_config_service: DatasetConfigService = Depends(get_dataset_config_service),
    connection_config: ConnectionConfig = Depends(_get_connection_config),
    dataset_key: FidesKey,
    test_request: DatasetTestRequest,
) -> Dict[str, Any]:

    if not CONFIG.security.dsr_testing_tools_enabled:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="DSR testing tools are not enabled.",
        )

    dataset_config = DatasetConfig.filter(
        db=db,
        conditions=(
            (DatasetConfig.connection_config_id == connection_config.id)
            & (DatasetConfig.fides_key == dataset_key)
        ),
    ).first()
    if not dataset_config:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No dataset config with fides_key '{dataset_key}'",
        )

    access_policy = Policy.get_by(db, field="key", value=test_request.policy_key)
    if not access_policy:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f'Policy with key "{test_request.policy_key}" not found',
        )

    privacy_request = dataset_config_service.run_test_access_request(
        access_policy,
        dataset_config,
        input_data=test_request.identities.data,
    )
    return {"privacy_request_id": privacy_request.id}
