from typing import List

import yaml
from fastapi import Depends, HTTPException, Request
from fastapi.params import Security
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from loguru import logger
from pydantic import conlist
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_415_UNSUPPORTED_MEDIA_TYPE,
)

from fides.api.ops.api import deps
from fides.api.ops.api.v1.scope_registry import (
    DATASET_CREATE_OR_UPDATE,
    DATASET_DELETE,
    DATASET_READ,
)
from fides.api.ops.api.v1.urn_registry import (
    DATASET_BY_KEY,
    DATASET_VALIDATE,
    DATASETS,
    V1_URL_PREFIX,
    YAML_DATASETS,
)
from fides.api.ops.common_exceptions import (
    SaaSConfigNotFoundException,
    TraversalError,
    ValidationError,
)
from fides.api.ops.graph.graph import DatasetGraph
from fides.api.ops.graph.traversal import Traversal
from fides.api.ops.models.connectionconfig import ConnectionConfig, ConnectionType
from fides.api.ops.models.datasetconfig import (
    DatasetConfig,
    convert_dataset_to_graph,
    to_graph_field,
)
from fides.api.ops.schemas.api import BulkUpdateFailed
from fides.api.ops.schemas.dataset import (
    BulkPutDataset,
    DatasetTraversalDetails,
    FidesopsDataset,
    ValidateDatasetResponse,
)
from fides.api.ops.schemas.shared_schemas import FidesOpsKey
from fides.api.ops.util.api_router import APIRouter
from fides.api.ops.util.oauth_util import verify_oauth_client
from fides.api.ops.util.saas_util import merge_datasets

X_YAML = "application/x-yaml"

router = APIRouter(tags=["Datasets"], prefix=V1_URL_PREFIX)


# Helper method to inject the parent ConnectionConfig into these child routes
def _get_connection_config(
    connection_key: FidesOpsKey, db: Session = Depends(deps.get_db)
) -> ConnectionConfig:
    logger.info("Finding connection config with key '{}'", connection_key)
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
    dataset: FidesopsDataset,
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
    DATASETS,
    dependencies=[Security(verify_oauth_client, scopes=[DATASET_CREATE_OR_UPDATE])],
    status_code=HTTP_200_OK,
    response_model=BulkPutDataset,
)
def patch_datasets(
    datasets: conlist(FidesopsDataset, max_items=50),  # type: ignore
    db: Session = Depends(deps.get_db),
    connection_config: ConnectionConfig = Depends(_get_connection_config),
) -> BulkPutDataset:
    """
    Given a list of dataset elements, create or update corresponding Dataset objects
    or report failure

    Use for bulk creating and/or updating datasets.

    If the fides_key for a given dataset exists, it will be treated as an update.
    Otherwise, a new dataset will be created.
    """

    created_or_updated: List[FidesopsDataset] = []
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
        data = {
            "connection_config_id": connection_config.id,
            "fides_key": dataset.fides_key,
            "dataset": dataset.dict(),
        }
        create_or_update_dataset(
            connection_config, created_or_updated, data, dataset, db, failed
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
    include_in_schema=False  # Not including this path in the schema.
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
    created_or_updated: List[FidesopsDataset] = []
    failed: List[BulkUpdateFailed] = []
    if isinstance(datasets, list):
        for dataset in datasets:  # type: ignore
            data: dict = {
                "connection_config_id": connection_config.id,
                "fides_key": dataset["fides_key"],
                "dataset": dataset,
            }
            create_or_update_dataset(
                connection_config,
                created_or_updated,
                data,
                yaml_request_body,
                db,
                failed,
            )
    return BulkPutDataset(
        succeeded=created_or_updated,
        failed=failed,
    )


def create_or_update_dataset(
    connection_config: ConnectionConfig,
    created_or_updated: List[FidesopsDataset],
    data: dict,
    dataset: dict,
    db: Session,
    failed: List[BulkUpdateFailed],
) -> None:
    try:
        if connection_config.connection_type == ConnectionType.saas:
            _validate_saas_dataset(connection_config, dataset)  # type: ignore
        # Try to find an existing DatasetConfig matching the given connection & key
        dataset_config = DatasetConfig.create_or_update(db, data=data)
        created_or_updated.append(dataset_config.dataset)
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
    connection_config: ConnectionConfig, dataset: FidesopsDataset
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
    DATASETS,
    dependencies=[Security(verify_oauth_client, scopes=[DATASET_READ])],
    response_model=Page[FidesopsDataset],
)
def get_datasets(
    db: Session = Depends(deps.get_db),
    params: Params = Depends(),
    connection_config: ConnectionConfig = Depends(_get_connection_config),
) -> AbstractPage[FidesopsDataset]:
    """Returns all datasets in the database."""

    logger.info(
        "Finding all datasets for connection '{}' with pagination params {}",
        connection_config.key,
        params,
    )
    dataset_configs = DatasetConfig.filter(
        db=db, conditions=(DatasetConfig.connection_config_id == connection_config.id)
    ).order_by(DatasetConfig.created_at.desc())

    # Generate the paginated results, but don't return them as-is. Instead,
    # modify the items array to be just the FidesopsDataset instead of the full
    # DatasetConfig. This has to be done *afterwards* to ensure that the
    # paginated query is handled by paginate()
    paginated_results = paginate(dataset_configs, params=params)
    paginated_results.items = [  # type: ignore
        dataset_config.dataset for dataset_config in paginated_results.items  # type: ignore
    ]
    return paginated_results


@router.get(
    DATASET_BY_KEY,
    dependencies=[Security(verify_oauth_client, scopes=[DATASET_READ])],
    response_model=FidesopsDataset,
)
def get_dataset(
    fides_key: FidesOpsKey,
    db: Session = Depends(deps.get_db),
    connection_config: ConnectionConfig = Depends(_get_connection_config),
) -> FidesopsDataset:
    """Returns a single dataset based on the given key."""

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
    return dataset_config.dataset


@router.delete(
    DATASET_BY_KEY,
    dependencies=[Security(verify_oauth_client, scopes=[DATASET_DELETE])],
    status_code=HTTP_204_NO_CONTENT,
)
def delete_dataset(
    fides_key: FidesOpsKey,
    *,
    db: Session = Depends(deps.get_db),
    connection_config: ConnectionConfig = Depends(_get_connection_config),
) -> None:
    """Removes the dataset based on the given key."""

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
