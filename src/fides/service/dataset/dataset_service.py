from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Type, Union

from fideslang.models import Dataset as FideslangDataset
from fideslang.models import DatasetCollection, DatasetField
from fideslang.validation import FidesKey
from loguru import logger
from pydantic import BaseModel, ConfigDict
from pydantic import ValidationError as PydanticValidationError
from pydantic import field_validator, model_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fides.api import common_exceptions
from fides.api.common_exceptions import (
    SaaSConfigNotFoundException,
    TraversalError,
    UnreachableNodesError,
    ValidationError,
)
from fides.api.graph.config import GraphDataset
from fides.api.graph.graph import DatasetGraph
from fides.api.graph.traversal import Traversal
from fides.api.models.connectionconfig import ConnectionConfig, ConnectionType
from fides.api.models.datasetconfig import (
    DatasetConfig,
    convert_dataset_to_graph,
    to_graph_field,
    validate_masking_strategy_override,
)
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import (
    PrivacyRequest,
    PrivacyRequestSource,
    PrivacyRequestStatus,
)
from fides.api.schemas.api import BulkUpdateFailed
from fides.api.schemas.dataset import (
    BulkPutDataset,
    DatasetConfigCtlDataset,
    DatasetTraversalDetails,
    ValidateDatasetResponse,
)
from fides.api.schemas.redis_cache import Identity, LabeledIdentity
from fides.api.util.data_category import DataCategory as DefaultTaxonomyDataCategories
from fides.api.util.data_category import get_data_categories_from_db
from fides.api.util.saas_util import merge_datasets

from fides.api.models.sql_models import (  # type: ignore[attr-defined] # isort: skip
    Dataset as CtlDataset,
)


class DatasetInput(BaseModel):
    """Schema for dataset input data"""

    dataset: FideslangDataset
    connection_config_id: str
    fides_key: FidesKey


class YAMLDatasetInput(BaseModel):
    """Schema for YAML dataset input"""

    dataset: List[FideslangDataset]


class DatasetCreateOrUpdateData(BaseModel):
    """Schema for dataset creation/update data"""

    connection_config_id: str
    fides_key: FidesKey
    ctl_dataset_id: Optional[str] = None
    dataset: Optional[FideslangDataset] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    def validate_dataset_or_ctl_id(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Either dataset or ctl_dataset_id must be provided"""
        if not values.get("dataset") and not values.get("ctl_dataset_id"):
            raise ValueError("Either dataset or ctl_dataset_id must be provided")
        return values


class DatasetError(Exception):
    """Base class for dataset-related errors"""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class DatasetNotFoundException(DatasetError):
    """Raised when a dataset is not found"""


class DatasetValidationError(DatasetError):
    """Raised when dataset validation fails"""

    def __init__(self, message: str, errors: Optional[List[Dict[str, Any]]] = None):
        self.errors = errors or []
        super().__init__(message)


class DuplicateDatasetError(DatasetError):
    """Raised when attempting to create a dataset with a duplicate key"""


class DatasetCreationError(DatasetError):
    """Raised when dataset creation fails"""


class DatasetService:
    def __init__(self, db: Session):
        self.db = db

    def create_or_update_dataset(
        self,
        connection_config: ConnectionConfig,
        dataset_pair: Union[DatasetConfigCtlDataset, DatasetInput],
    ) -> Tuple[Optional[FideslangDataset], Optional[BulkUpdateFailed]]:
        """Create or update a single dataset"""
        try:
            # Handle different input types
            if isinstance(dataset_pair, DatasetConfigCtlDataset):
                ctl_dataset, fetched_dataset = _get_and_validate_ctl_dataset(
                    self.db, dataset_pair.ctl_dataset_fides_key
                )
                data = DatasetCreateOrUpdateData(
                    connection_config_id=connection_config.id,
                    fides_key=dataset_pair.fides_key,
                    ctl_dataset_id=ctl_dataset.id,
                )
                dataset_to_validate = fetched_dataset
            else:  # DatasetInput
                data = DatasetCreateOrUpdateData(
                    connection_config_id=connection_config.id,
                    fides_key=dataset_pair.fides_key,
                    dataset=dataset_pair.dataset,
                )
                dataset_to_validate = dataset_pair.dataset

            # Validate dataset
            if connection_config.connection_type == ConnectionType.saas:
                _validate_saas_dataset(connection_config, dataset_to_validate)
            validate_masking_strategy_override(dataset_to_validate)
            validate_data_categories(dataset_to_validate, self.db)

            # Create or update the dataset
            if isinstance(dataset_pair, DatasetConfigCtlDataset):
                dataset_config = _create_or_update_dataset_config(
                    self.db, data, ctl_dataset.id
                )
            else:
                dataset_config = _create_or_update_dataset_config(self.db, data)

            return dataset_config.ctl_dataset, None

        except (SaaSConfigNotFoundException, ValidationError) as exception:
            error = BulkUpdateFailed(
                message=str(exception),
                data=dataset_pair.model_dump(),
            )
            logger.warning(f"Dataset validation failed: {str(exception)}")
            return None, error

        except IntegrityError:
            message = f"Dataset with key '{dataset_pair.fides_key}' already exists."
            error = BulkUpdateFailed(
                message=message,
                data=dataset_pair.model_dump(),
            )
            logger.warning(message)
            return None, error

        except Exception as e:
            if isinstance(e, (PydanticValidationError, DatasetNotFoundException)):
                raise

            message = f"Create/update failed for dataset '{dataset_pair.fides_key}'"
            logger.warning(f"{message}: {str(e)}")
            error = BulkUpdateFailed(
                message="Dataset create/update failed.",
                data=dataset_pair.model_dump(),
            )
            return None, error

    def bulk_create_or_update_datasets(
        self,
        connection_config: ConnectionConfig,
        dataset_pairs: Union[List[DatasetConfigCtlDataset], List[FideslangDataset]],
    ) -> BulkPutDataset:
        """Create or update multiple datasets"""
        created_or_updated: List[FideslangDataset] = []
        failed: List[BulkUpdateFailed] = []

        logger.info("Starting bulk upsert for {} datasets", len(dataset_pairs))

        for item in dataset_pairs:
            if isinstance(item, FideslangDataset):
                dataset_input = DatasetInput(
                    dataset=item,
                    connection_config_id=connection_config.id,
                    fides_key=item.fides_key,
                )
                dataset_result, error = self.create_or_update_dataset(
                    connection_config=connection_config,
                    dataset_pair=dataset_input,
                )
            else:  # DatasetConfigCtlDataset
                dataset_result, error = self.create_or_update_dataset(
                    connection_config=connection_config,
                    dataset_pair=item,
                )

            if dataset_result:
                created_or_updated.append(dataset_result)
            if error:
                failed.append(error)

        return BulkPutDataset(
            succeeded=created_or_updated,
            failed=failed,
        )

    def clean_datasets(self) -> Tuple[List[str], List[str]]:
        datasets = self.db.execute(select([CtlDataset])).scalars().all()
        return _run_clean_datasets(self.db, datasets)

    def validate_dataset(
        self, connection_config: ConnectionConfig, dataset: FideslangDataset
    ) -> ValidateDatasetResponse:
        validate_data_categories(dataset, self.db)

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
                "Traversal validation failed for dataset '{}': {}",
                dataset.fides_key,
                err,
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

    def get_dataset_reachability(
        self, dataset_config: DatasetConfig, policy: Optional[Policy] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Determines if the given dataset is reachable along with an error message
        """

        # Get all the dataset configs that are not associated with a disabled connection
        datasets = DatasetConfig.all(db=self.db)
        dataset_graphs = [
            dataset_config.get_graph()
            for dataset_config in datasets
            if not dataset_config.connection_config.disabled
        ]

        # We still want to check reachability even if our dataset config's connection is disabled.
        # We also consider the siblings, because if the connection is enabled, then all the
        # datasets will be enabled with it.
        sibling_dataset_graphs = []
        if dataset_config.connection_config.disabled:
            sibling_datasets = dataset_config.connection_config.datasets
            sibling_dataset_graphs = [
                dataset_config.get_graph() for dataset_config in sibling_datasets
            ]

        try:
            dataset_graph = DatasetGraph(*dataset_graphs, *sibling_dataset_graphs)
        except ValidationError as exc:
            return (
                False,
                f'The following dataset references do not exist "{", ".join(exc.errors)}"',
            )

        # dummy data is enough to determine traversability
        identity_seed: Dict[str, str] = {
            k: "something" for k in dataset_graph.identity_keys.values()
        }

        try:
            Traversal(dataset_graph, identity_seed, policy)
        except UnreachableNodesError as exc:
            return (
                False,
                f'The following collections are not reachable "{", ".join(exc.errors)}"',
            )

        return True, None

    def run_test_access_request(
        self,
        policy: Policy,
        dataset_config: DatasetConfig,
        input_data: Dict[str, Any],
    ) -> PrivacyRequest:
        """
        Creates a privacy request with a source of "Dataset test" that runs an access request for a single dataset.
        The input data is used to mock any external dataset values referenced by our dataset so that it can run in
        complete isolation.
        """

        # Create a privacy request with a source of "Dataset test"
        # so it's not shown to the user.
        privacy_request = PrivacyRequest.create(
            db=self.db,
            data={
                "policy_id": policy.id,
                "source": PrivacyRequestSource.dataset_test,
                "status": PrivacyRequestStatus.in_processing,
            },
        )

        # Remove periods and colons to avoid them being parsed as path delimiters downstream.
        escaped_input_data = {
            key.replace(".", "_").replace(":", "_"): value
            for key, value in input_data.items()
        }

        # Manually cache the input data as identity data.
        # We're doing a bit of trickery here to avoid asking for labels for custom identities.
        predefined_fields = Identity.model_fields.keys()
        input_identity = {
            key: (
                value
                if key in predefined_fields
                else LabeledIdentity(label=key, value=value)
            )
            for key, value in escaped_input_data.items()
        }
        privacy_request.cache_identity(input_identity)

        graph_dataset = dataset_config.get_graph()
        modified_graph_dataset = replace_references_with_identities(
            dataset_config.fides_key, graph_dataset
        )

        dataset_graph = DatasetGraph(modified_graph_dataset)
        connection_config = dataset_config.connection_config

        from fides.api.task.create_request_tasks import run_access_request

        # Finally invoke the existing DSR 3.0 access request task
        run_access_request(
            privacy_request,
            policy,
            dataset_graph,
            [connection_config],
            escaped_input_data,
            self.db,
            privacy_request_proceed=False,
        )
        return privacy_request


def get_identities_and_references(
    dataset_config: DatasetConfig,
) -> Set[str]:
    """
    Returns all identity and dataset references in the dataset.
    If a field has multiple references only the first reference will be considered.
    """

    result: Set[str] = set()
    dataset: GraphDataset = dataset_config.get_graph()
    for collection in dataset.collections:
        # Process the identities in the collection
        result.update(collection.identities().values())
        for _, field_refs in collection.references().items():
            # Take first reference only, we only care that this collection is reachable,
            # how we get there doesn't matter for our current use case
            ref, edge_direction = field_refs[0]
            if edge_direction == "from" and ref.dataset != dataset_config.fides_key:
                result.add(ref.value)
    return result


def replace_references_with_identities(
    dataset_key: str, graph_dataset: GraphDataset
) -> GraphDataset:
    """
    Replace external field references with identity values for testing.

    Creates a copy of the graph dataset and replaces dataset references with
    equivalent identity references that can be seeded directly. This allows
    testing a single dataset in isolation without needing to load data from
    referenced external datasets.
    """

    modified_graph_dataset = deepcopy(graph_dataset)

    for collection in modified_graph_dataset.collections:
        for field in collection.fields:
            for ref, edge_direction in field.references[:]:
                if edge_direction == "from" and ref.dataset != dataset_key:
                    field.identity = f"{ref.dataset}_{ref.collection}_{'_'.join(ref.field_path.levels)}"
                    field.references.remove((ref, "from"))

    return modified_graph_dataset


def validate_data_categories(dataset: FideslangDataset, db: Session) -> None:
    """Validate data categories on a given Dataset

    As a separate method because we want to be able to match against data_categories in the
    database instead of a static list.
    """
    defined_data_categories: List[FidesKey] = get_data_categories_from_db(db)
    validate_data_categories_against_db(dataset, defined_data_categories)


def validate_data_categories_against_db(
    dataset: FideslangDataset, defined_data_categories: List[FidesKey]
) -> None:
    """
    Validate that data_categories defined on the Dataset, Collection, and Field levels exist
    in the database.  Doing this instead of a traditional validator function to have
    access to a database session.

    If no data categories in the database, default to using data categories from the default taxonomy.
    """
    if not defined_data_categories:
        logger.info(
            "No data categories in the database: reverting to default data categories."
        )
        defined_data_categories = [
            FidesKey(key) for key in DefaultTaxonomyDataCategories.__members__.keys()
        ]

    class DataCategoryValidationMixin(BaseModel):
        @field_validator("data_categories", check_fields=False)
        @classmethod
        def valid_data_categories(
            cls: Type["DataCategoryValidationMixin"], v: Optional[List[FidesKey]]
        ) -> Optional[List[FidesKey]]:
            """Validate that all annotated data categories exist in the taxonomy"""
            return _valid_data_categories(v, defined_data_categories)

    class FieldDataCategoryValidation(DatasetField, DataCategoryValidationMixin):
        fields: Optional[List["FieldDataCategoryValidation"]] = None  # type: ignore[assignment]

    FieldDataCategoryValidation.model_rebuild()

    class CollectionDataCategoryValidation(
        DatasetCollection, DataCategoryValidationMixin
    ):
        fields: Sequence[FieldDataCategoryValidation] = []  # type: ignore[assignment]

    class DatasetDataCategoryValidation(FideslangDataset, DataCategoryValidationMixin):
        collections: Sequence[CollectionDataCategoryValidation]  # type: ignore[assignment]

    DatasetDataCategoryValidation(**dataset.model_dump(mode="json"))


def _valid_data_categories(
    proposed_data_categories: Optional[List[FidesKey]],
    defined_data_categories: List[FidesKey],
) -> Optional[List[FidesKey]]:
    """
    Ensure that every data category provided matches a valid defined data category.
    Throws an error if any of the categories are invalid,
    or otherwise returns the list of categories unchanged.
    """

    def validate_category(data_category: FidesKey) -> FidesKey:
        if data_category not in defined_data_categories:
            raise common_exceptions.DataCategoryNotSupported(
                f"The data category {data_category} is not supported."
            )
        return data_category

    if proposed_data_categories:
        return [dc for dc in proposed_data_categories if validate_category(dc)]
    return proposed_data_categories


def _run_clean_datasets(
    db: Session, datasets: List[FideslangDataset]
) -> tuple[List[str], List[str]]:
    """
    Clean the dataset name and structure to remove any malformed data possibly present from nested field regressions.
    Changes dot separated positional names to source names (ie. `user.address.street` -> `street`).
    """

    for dataset in datasets:
        logger.info(f"Cleaning field names for dataset: {dataset.fides_key}")
        for collection in dataset.collections:
            collection["fields"] = _recursive_clean_fields(collection["fields"])  # type: ignore # pylint: disable=unsupported-assignment-operation

        # manually upsert the dataset

        logger.info(f"Upserting dataset: {dataset.fides_key}")
        failed = []
        try:
            dataset_ctl_obj = (
                db.query(CtlDataset)
                .filter(CtlDataset.fides_key == dataset.fides_key)
                .first()
            )
            if dataset_ctl_obj:
                db.query(CtlDataset).filter(
                    CtlDataset.fides_key == dataset.fides_key
                ).update(
                    {
                        "collections": dataset.collections,
                        "updated_at": datetime.now(timezone.utc),
                    },
                    synchronize_session=False,
                )
                db.commit()
            else:
                logger.error(f"Dataset with fides_key {dataset.fides_key} not found.")
        except Exception as e:
            logger.error(f"Error upserting dataset: {dataset.fides_key} {e}")
            db.rollback()
            failed.append(dataset.fides_key)

    succeeded = [dataset.fides_key for dataset in datasets]
    return succeeded, failed


def _recursive_clean_fields(fields: List[dict]) -> List[dict]:
    """
    Recursively clean the fields of a dataset.
    """
    cleaned_fields = []
    for field in fields:
        field["name"] = field["name"].split(".")[-1]
        if field["fields"]:
            field["fields"] = _recursive_clean_fields(field["fields"])
        cleaned_fields.append(field)
    return cleaned_fields


def _get_and_validate_ctl_dataset(
    db: Session, ctl_dataset_fides_key: str
) -> Tuple[CtlDataset, FideslangDataset]:
    """Get and validate a CTL dataset"""
    ctl_dataset: CtlDataset = (
        db.query(CtlDataset).filter_by(fides_key=ctl_dataset_fides_key).first()
    )
    if not ctl_dataset:
        raise DatasetNotFoundException(
            f"No ctl dataset with key '{ctl_dataset_fides_key}'"
        )

    fetched_dataset: FideslangDataset = FideslangDataset.model_validate(ctl_dataset)
    validate_data_categories(fetched_dataset, db)

    return ctl_dataset, fetched_dataset


def _validate_saas_dataset(
    connection_config: ConnectionConfig, dataset: FideslangDataset
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


def _create_or_update_dataset_config(
    db: Session,
    data: DatasetCreateOrUpdateData,
    ctl_dataset_id: Optional[str] = None,
) -> DatasetConfig:
    """Create or update a dataset config"""
    if ctl_dataset_id:
        data_dict: Dict[str, Any] = {
            "connection_config_id": data.connection_config_id,
            "fides_key": data.fides_key,
            "ctl_dataset_id": ctl_dataset_id,
        }
        return DatasetConfig.create_or_update(db, data=data_dict)

    data_dict: Dict[str, Any] = {
        "connection_config_id": data.connection_config_id,
        "fides_key": data.fides_key,
        "dataset": data.dataset.model_dump(mode="json") if data.dataset else None,
    }
    return DatasetConfig.upsert_with_ctl_dataset(db, data=data_dict)
