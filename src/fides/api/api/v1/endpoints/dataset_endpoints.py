from typing import Callable, List

import yaml
from fastapi import Depends, HTTPException, Request
from fastapi.params import Security
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from fideslang.models import Dataset
from fideslang.validation import FidesKey
from loguru import logger
from pydantic import ValidationError as PydanticValidationError
from pydantic import conlist
from sqlalchemy import and_, not_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_415_UNSUPPORTED_MEDIA_TYPE,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from fides.api.api import deps
from fides.api.common_exceptions import (
    SaaSConfigNotFoundException,
    TraversalError,
    ValidationError,
)
from fides.api.graph.graph import DatasetGraph
from fides.api.graph.traversal import Traversal
from fides.api.models.connectionconfig import ConnectionConfig, ConnectionType
from fides.api.models.datasetconfig import (
    DatasetConfig,
    convert_dataset_to_graph,
    to_graph_field,
)
from fides.api.oauth.utils import verify_oauth_client
from fides.api.schemas.api import BulkUpdateFailed
from fides.api.schemas.dataset import (
    BulkPutDataset,
    DatasetConfigCtlDataset,
    DatasetConfigSchema,
    DatasetTraversalDetails,
    ValidateDatasetResponse,
    validate_data_categories_against_db,
)
from fides.api.util.api_router import APIRouter
from fides.api.util.data_category import get_data_categories_from_db
from fides.api.util.saas_util import merge_datasets
from fides.common.api.scope_registry import (
    DATASET_CREATE_OR_UPDATE,
    DATASET_DELETE,
    DATASET_READ,
)
from fides.common.api.v1.urn_registry import (
    CONNECTION_DATASETS,
    DATASET_BY_KEY,
    DATASET_CONFIGS,
    DATASET_VALIDATE,
    DATASETCONFIG_BY_KEY,
    DATASETS,
    V1_URL_PREFIX,
    YAML_DATASETS,
)

from fides.api.models.sql_models import (  # type: ignore[attr-defined] # isort: skip
    Dataset as CtlDataset,
)

X_YAML = "application/x-yaml"

router = APIRouter(tags=["Dataset Configs"], prefix=V1_URL_PREFIX)


# Helper method to inject the parent ConnectionConfig into these child routes
def _get_connection_config(
    connection_key: FidesKey, db: Session = Depends(deps.get_db)
) -> ConnectionConfig:
    logger.info("Finding connection config with key '{}'", connection_key)
    connection_config = ConnectionConfig.get_by(db, field="key", value=connection_key)
    if not connection_config:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No connection config with key '{connection_key}'",
        )
    return connection_config


def validate_data_categories(dataset: Dataset, db: Session) -> None:
    """Validate data categories on a given Dataset

    As a separate method because we want to be able to match against data_categories in the
    database instead of a static list.
    """
    try:
        defined_data_categories: List[FidesKey] = get_data_categories_from_db(db)
        validate_data_categories_against_db(dataset, defined_data_categories)
    except PydanticValidationError as e:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors()
        )


@router.put(
    DATASET_VALIDATE,
    dependencies=[Security(verify_oauth_client, scopes=[DATASET_READ])],
    status_code=HTTP_200_OK,
    response_model=ValidateDatasetResponse,
)
def validate_dataset(
    dataset: Dataset,
    db: Session = Depends(deps.get_db),
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
    validate_data_categories(dataset, db)

    try:
        # Attempt to generate a traversal for this dataset by providing an empty
        # dictionary of all unique identity keys
        graph = convert_dataset_to_graph(dataset, connection_config.key)  # type: ignore

        # Datasets for SaaS connections need to be merged with a SaaS config to
        # be able to generate a valid traversal
        if connection_config.connection_type == ConnectionType.saas:
            _validate_saas_dataset(connection_config, dataset)
            graph = merge_datasets(
                graph, connection_config.get_saas_config().get_graph(connection_config.secrets)  # type: ignore
            )
        complete_graph = DatasetGraph(graph)
        unique_identities = set(complete_graph.identity_keys.values())
        Traversal(complete_graph, {k: None for k in unique_identities})
    except (TraversalError, ValidationError) as err:
        logger.warning(
            "Traversal validation failed for dataset '{}': {}", dataset.fides_key, err
        )
        return ValidateDatasetResponse(
            dataset=dataset,
            traversal_details=DatasetTraversalDetails(
                is_traversable=False,
                msg=str(err),
            ),
        )

    logger.info("Validation successful for dataset '{}'!", dataset.fides_key)
    return ValidateDatasetResponse(
        dataset=dataset,
        traversal_details=DatasetTraversalDetails(
            is_traversable=True,
            msg=None,
        ),
    )


@router.patch(
    DATASET_CONFIGS,
    dependencies=[Security(verify_oauth_client, scopes=[DATASET_CREATE_OR_UPDATE])],
    status_code=HTTP_200_OK,
    response_model=BulkPutDataset,
)
def patch_dataset_configs(
    dataset_pairs: conlist(DatasetConfigCtlDataset, max_items=50),  # type: ignore
    db: Session = Depends(deps.get_db),
    connection_config: ConnectionConfig = Depends(_get_connection_config),
) -> BulkPutDataset:
    """
    Endpoint to create or update DatasetConfigs by passing in pairs of:
    1) A DatasetConfig fides_key
    2) The corresponding CtlDataset fides_key which stores the bulk of the actual dataset

    The CtlDataset contents are retrieved for extra validation before linking this
    to the DatasetConfig.

    """
    created_or_updated: List[Dataset] = []
    failed: List[BulkUpdateFailed] = []
    logger.info("Starting bulk upsert for {} Dataset Configs", len(dataset_pairs))

    for dataset_pair in dataset_pairs:
        logger.info(
            "Finding ctl_dataset with key '{}'", dataset_pair.ctl_dataset_fides_key
        )
        ctl_dataset: CtlDataset = (
            db.query(CtlDataset)
            .filter_by(fides_key=dataset_pair.ctl_dataset_fides_key)
            .first()
        )
        if not ctl_dataset:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"No ctl dataset with key '{dataset_pair.ctl_dataset_fides_key}'",
            )

        try:
            fetched_dataset: Dataset = Dataset.from_orm(ctl_dataset)
        except PydanticValidationError as e:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors()
            )
        validate_data_categories(fetched_dataset, db)

        data = {
            "connection_config_id": connection_config.id,
            "fides_key": dataset_pair.fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        }

        create_or_update_dataset(
            connection_config,
            created_or_updated,
            data,
            fetched_dataset,
            db,
            failed,
            DatasetConfig.create_or_update,
        )

    return BulkPutDataset(
        succeeded=created_or_updated,
        failed=failed,
    )


@router.patch(
    CONNECTION_DATASETS,
    dependencies=[Security(verify_oauth_client, scopes=[DATASET_CREATE_OR_UPDATE])],
    status_code=HTTP_200_OK,
    response_model=BulkPutDataset,
)
def patch_datasets(
    datasets: conlist(Dataset, max_items=50),  # type: ignore
    db: Session = Depends(deps.get_db),
    connection_config: ConnectionConfig = Depends(_get_connection_config),
) -> BulkPutDataset:
    """
    Given a list of dataset elements, create or update corresponding Dataset objects
    or report failure

    This endpoint upserts the DatasetConfig and associated CTL Dataset.  Will shortly be deprecated.

    If the fides_key for a given DatasetConfig exists, it will be treated as an update.
    Otherwise, a new DatasetConfig will be created.
    """

    created_or_updated: List[Dataset] = []
    failed: List[BulkUpdateFailed] = []
    logger.info("Starting bulk upsert for {} datasets", len(datasets))

    # warn if there are duplicate fides_keys within the datasets
    # valid datasets with the same fides_key will override each other
    key_list = [dataset.fides_key for dataset in datasets]
    if len(key_list) != len(set(key_list)):
        logger.warning(
            "Datasets with duplicate fides_keys detected, may result in unintended behavior."
        )

    for dataset in datasets:
        validate_data_categories(dataset, db)
        data = {
            "connection_config_id": connection_config.id,
            "fides_key": dataset.fides_key,
            "dataset": dataset.dict(),  # Currently used for upserting a CTL Dataset
        }
        create_or_update_dataset(
            connection_config,
            created_or_updated,
            data,
            dataset,
            db,
            failed,
            DatasetConfig.upsert_with_ctl_dataset,
        )
    return BulkPutDataset(
        succeeded=created_or_updated,
        failed=failed,
    )


@router.patch(
    YAML_DATASETS,
    dependencies=[Security(verify_oauth_client, scopes=[DATASET_CREATE_OR_UPDATE])],
    status_code=200,
    response_model=BulkPutDataset,
    include_in_schema=False,  # Not including this path in the schema.
    # Since this yaml function needs to access the request, the open api spec will not be generated correctly.
    # To include this path, extend open api: https://fastapi.tiangolo.com/advanced/extending-openapi/
)
async def patch_yaml_datasets(
    request: Request,
    db: Session = Depends(deps.get_db),
    connection_config: ConnectionConfig = Depends(_get_connection_config),
) -> BulkPutDataset:
    if request.headers.get("content-type") != X_YAML:
        raise HTTPException(
            status_code=HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Supported type: " + X_YAML,
        )
    body = await request.body()
    try:
        yaml_request_body: dict = yaml.safe_load(body)
    except yaml.MarkedYAMLError as e:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="Error in YAML: " + str(e)
        )
    datasets = (
        yaml_request_body.get("dataset") if isinstance(yaml_request_body, dict) else []
    )
    created_or_updated: List[Dataset] = []
    failed: List[BulkUpdateFailed] = []
    if isinstance(datasets, list):
        for dataset in datasets:  # type: ignore
            validate_data_categories(Dataset(**dataset), db)
            data: dict = {
                "connection_config_id": connection_config.id,
                "fides_key": dataset["fides_key"],
                "dataset": dataset,  # Currently used for upserting a CTL Dataset
            }
            create_or_update_dataset(
                connection_config,
                created_or_updated,
                data,
                Dataset(**dataset),
                db,
                failed,
                DatasetConfig.upsert_with_ctl_dataset,
            )
    return BulkPutDataset(
        succeeded=created_or_updated,
        failed=failed,
    )


def create_or_update_dataset(
    connection_config: ConnectionConfig,
    created_or_updated: List[Dataset],
    data: dict,
    dataset: Dataset,
    db: Session,
    failed: List[BulkUpdateFailed],
    create_method: Callable,
) -> None:
    try:
        if connection_config.connection_type == ConnectionType.saas:
            # Validating here instead of on ctl_dataset creation because this only applies
            # when a ctl_dataset is being linked to a Saas Connector.
            _validate_saas_dataset(connection_config, dataset)  # type: ignore
        # Try to find an existing DatasetConfig matching the given connection & key
        dataset_config = create_method(db, data=data)
        created_or_updated.append(dataset_config.ctl_dataset)
    except (
        SaaSConfigNotFoundException,
        ValidationError,
    ) as exception:
        logger.warning(exception.message)
        failed.append(
            BulkUpdateFailed(
                message=exception.message,
                data=data,
            )
        )
    except IntegrityError:
        message = "Dataset with key '%s' already exists." % data["fides_key"]
        logger.warning(message)
        failed.append(
            BulkUpdateFailed(
                message=message,
                data=data,
            )
        )
    except Exception:
        logger.warning("Create/update failed for dataset '{}'.", data["fides_key"])
        failed.append(
            BulkUpdateFailed(
                message="Dataset create/update failed.",
                data=data,
            )
        )


def _validate_saas_dataset(
    connection_config: ConnectionConfig, dataset: Dataset
) -> None:
    if connection_config.saas_config is None:
        raise SaaSConfigNotFoundException(
            f"Connection config '{connection_config.key}' must have a "
            "SaaS config before validating or adding a dataset"
        )

    fides_key = connection_config.saas_config["fides_key"]
    if fides_key != dataset.fides_key:
        raise ValidationError(
            f"The fides_key '{dataset.fides_key}' of the dataset "
            f"does not match the fides_key '{fides_key}' "
            "of the connection config"
        )
    for collection in dataset.collections:
        for field in collection.fields:
            graph_field = to_graph_field(field)
            if graph_field.references or graph_field.identity:
                raise ValidationError(
                    "A dataset for a ConnectionConfig type of 'saas' is not "
                    "allowed to have references or identities. Please add "
                    "them to the SaaS config."
                )


@router.get(
    CONNECTION_DATASETS,
    dependencies=[Security(verify_oauth_client, scopes=[DATASET_READ])],
    response_model=Page[Dataset],
)
def get_datasets(
    db: Session = Depends(deps.get_db),
    params: Params = Depends(),
    connection_config: ConnectionConfig = Depends(_get_connection_config),
) -> AbstractPage[Dataset]:
    """Returns all CTL datasets attached to the ConnectionConfig via the Dataset Config.

    Soon to be deprecated.
    """

    logger.info(
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
    response_model=Dataset,
)
def get_dataset(
    fides_key: FidesKey,
    db: Session = Depends(deps.get_db),
    connection_config: ConnectionConfig = Depends(_get_connection_config),
) -> Dataset:
    """Returns a single ctl dataset linked to the given DatasetConfig.

    Soon to be deprecated
    """

    logger.info(
        "Finding dataset '{}' for connection '{}'", fides_key, connection_config.key
    )
    dataset_config = DatasetConfig.filter(
        db=db,
        conditions=(
            (DatasetConfig.connection_config_id == connection_config.id)
            & (DatasetConfig.fides_key == fides_key)
        ),
    ).first()
    if not dataset_config:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No dataset with fides_key '{fides_key}' and connection key {connection_config.key}'",
        )
    return dataset_config.ctl_dataset


@router.get(
    DATASET_CONFIGS,
    dependencies=[Security(verify_oauth_client, scopes=[DATASET_READ])],
    response_model=Page[DatasetConfigSchema],
)
def get_dataset_configs(
    db: Session = Depends(deps.get_db),
    params: Params = Depends(),
    connection_config: ConnectionConfig = Depends(_get_connection_config),
) -> AbstractPage[DatasetConfig]:
    """Returns all Dataset Configs attached to current Connection Config."""

    logger.info(
        "Finding all dataset configs for connection '{}' with pagination params {}",
        connection_config.key,
        params,
    )
    dataset_configs = DatasetConfig.filter(
        db=db, conditions=(DatasetConfig.connection_config_id == connection_config.id)
    ).order_by(DatasetConfig.created_at.desc())

    return paginate(dataset_configs, params)


@router.get(
    DATASETCONFIG_BY_KEY,
    dependencies=[Security(verify_oauth_client, scopes=[DATASET_READ])],
    response_model=DatasetConfigSchema,
)
def get_dataset_config(
    fides_key: FidesKey,
    db: Session = Depends(deps.get_db),
    connection_config: ConnectionConfig = Depends(_get_connection_config),
) -> DatasetConfig:
    """Returns the specific Dataset Config linked to the Connection Config."""

    logger.info(
        "Finding dataset config '{}' for connection '{}'",
        fides_key,
        connection_config.key,
    )
    dataset_config = DatasetConfig.filter(
        db=db,
        conditions=(
            (DatasetConfig.connection_config_id == connection_config.id)
            & (DatasetConfig.fides_key == fides_key)
        ),
    ).first()
    if not dataset_config:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No dataset config with fides_key '{fides_key}' and connection key {connection_config.key}'",
        )
    return dataset_config


@router.delete(
    DATASET_BY_KEY,
    dependencies=[Security(verify_oauth_client, scopes=[DATASET_DELETE])],
    status_code=HTTP_204_NO_CONTENT,
)
def delete_dataset(
    fides_key: FidesKey,
    *,
    db: Session = Depends(deps.get_db),
    connection_config: ConnectionConfig = Depends(_get_connection_config),
) -> None:
    """Removes the DatasetConfig based on the given key."""

    logger.info(
        "Finding dataset '{}' for connection '{}'", fides_key, connection_config.key
    )
    dataset_config = DatasetConfig.filter(
        db=db,
        conditions=(
            (DatasetConfig.connection_config_id == connection_config.id)
            & (DatasetConfig.fides_key == fides_key)
        ),
    ).first()
    if not dataset_config:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No dataset with fides_key '{fides_key}' and connection_key '{connection_config.key}'",
        )

    logger.info(
        "Deleting dataset '{}' for connection '{}'", fides_key, connection_config.key
    )
    dataset_config.delete(db)


@router.get(
    f"/filter{DATASETS}",
    dependencies=[Security(verify_oauth_client, scopes=[DATASET_READ])],
    response_model=List[Dataset],
)
def get_ctl_datasets(
    db: Session = Depends(deps.get_db),
    remove_saas_datasets: bool = True,
    only_unlinked_datasets: bool = False,
) -> List[Dataset]:
    """
    Returns all CTL datasets .
    """

    logger.info(
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
