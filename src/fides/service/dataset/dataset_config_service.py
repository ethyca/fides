from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple, Union

from fastapi.encoders import jsonable_encoder
from fideslang.models import Dataset as FideslangDataset
from loguru import logger
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.orm import Session

from fides.api.common_exceptions import (
    SaaSConfigNotFoundException,
    UnreachableNodesError,
    ValidationError,
)
from fides.api.graph.config import GraphDataset
from fides.api.graph.graph import DatasetGraph
from fides.api.graph.node_filters import NodeFilter
from fides.api.graph.traversal import Traversal, TraversalNode
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.api import BulkUpdateFailed
from fides.api.schemas.dataset import (
    BulkPutDataset,
    DatasetConfigCtlDataset,
    ValidateDatasetResponse,
)
from fides.api.schemas.privacy_request import PrivacyRequestSource, PrivacyRequestStatus
from fides.api.schemas.redis_cache import Identity, LabeledIdentity
from fides.service.dataset.dataset_service import (
    DatasetNotFoundException,
    _get_ctl_dataset,
)
from fides.service.dataset.dataset_validator import DatasetValidator
from fides.service.dataset.validation_steps.traversal import TraversalValidationStep


class DatasetFilter(NodeFilter):
    """
    Filter that excludes nodes that are not part of the specified dataset.
    This ensures that unreachable nodes from other datasets are not treated as errors.
    """

    def __init__(self, dataset_name: str):
        super().__init__()
        self.dataset_name = dataset_name

    def exclude_node(self, node: TraversalNode) -> bool:
        """Returns True if the node is not part of the dataset"""
        return node.address.dataset != self.dataset_name


class DatasetConfigService:
    def __init__(self, db: Session):
        self.db = db

    def create_or_update_dataset_config(
        self,
        connection_config: ConnectionConfig,
        dataset: Union[DatasetConfigCtlDataset, FideslangDataset],
    ) -> Tuple[Optional[FideslangDataset], Optional[BulkUpdateFailed]]:
        """Create or update a single dataset"""
        try:
            if isinstance(dataset, DatasetConfigCtlDataset):
                ctl_dataset = _get_ctl_dataset(self.db, dataset.ctl_dataset_fides_key)
                dataset_to_validate = FideslangDataset.model_validate(ctl_dataset)
                data_dict = {
                    "connection_config_id": connection_config.id,
                    "fides_key": dataset.fides_key,
                    "ctl_dataset_id": ctl_dataset.id,
                }
            else:
                dataset_to_validate = dataset
                data_dict = {
                    "connection_config_id": connection_config.id,
                    "fides_key": dataset.fides_key,
                    "dataset": dataset.model_dump(mode="json"),
                }

            # Validate dataset
            DatasetValidator(
                self.db,
                dataset_to_validate,
                connection_config,
                skip_steps=[TraversalValidationStep],
            ).validate()

            # Create or update using unified method
            dataset_config = DatasetConfig.create_or_update(self.db, data=data_dict)

            return dataset_config.ctl_dataset, None

        except (SaaSConfigNotFoundException, ValidationError) as exception:
            error = BulkUpdateFailed(
                message=str(exception),
                data=dataset.model_dump(),
            )
            logger.warning(f"Dataset validation failed: {str(exception)}")
            return None, error

        except (PydanticValidationError, DatasetNotFoundException):
            # Raising errors for now to stay consistent with existing behavior.
            # TODO: Include these errors in the bulk update response and update the test assertions.
            raise

        except Exception as e:
            message = f"Create/update failed for dataset '{dataset.fides_key}'"
            logger.warning(f"{message}: {str(e)}")
            error = BulkUpdateFailed(
                message="Dataset create/update failed.",
                data=dataset.model_dump(),
            )
            return None, error

    def bulk_create_or_update_dataset_configs(
        self,
        connection_config: ConnectionConfig,
        datasets: Union[List[DatasetConfigCtlDataset], List[FideslangDataset]],
    ) -> BulkPutDataset:
        """Create or update multiple datasets"""
        created_or_updated: List[FideslangDataset] = []
        failed: List[BulkUpdateFailed] = []

        logger.info("Starting bulk upsert for {} datasets", len(datasets))

        for item in datasets:
            dataset_result, error = self.create_or_update_dataset_config(
                connection_config=connection_config,
                dataset=item,
            )

            if dataset_result:
                created_or_updated.append(dataset_result)
            if error:
                failed.append(error)

        return BulkPutDataset(
            succeeded=created_or_updated,
            failed=failed,
        )

    def validate_dataset_config(
        self, connection_config: ConnectionConfig, dataset: FideslangDataset
    ) -> ValidateDatasetResponse:

        return DatasetValidator(self.db, dataset, connection_config).validate()

    def get_dataset_reachability(
        self, dataset_config: DatasetConfig, policy: Optional[Policy] = None
    ) -> Tuple[bool, Optional[Union[str, List[Dict[str, Any]]]]]:
        """
        Determines if the given dataset is reachable along with an error message
        """
        # First check if the target dataset is valid
        try:
            dataset_config.get_graph()
        except PydanticValidationError as exc:
            return False, jsonable_encoder(
                exc.errors(
                    include_url=False, include_input=False, include_context=False
                )
            )

        # Get graphs for all enabled datasets
        dataset_graphs = []
        datasets = DatasetConfig.all(db=self.db)
        for dataset in datasets:
            if not dataset.connection_config.disabled:
                try:
                    dataset_graphs.append(dataset.get_graph())
                except PydanticValidationError:
                    continue

        # We still want to check reachability even if our dataset config's connection is disabled.
        # We also consider the siblings, because if the connection is enabled, then all the
        # datasets will be enabled with it.
        sibling_dataset_graphs = []
        if dataset_config.connection_config.disabled:
            for sibling in dataset_config.connection_config.datasets:
                try:
                    sibling_dataset_graphs.append(sibling.get_graph())
                except PydanticValidationError:
                    continue

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
            Traversal(
                dataset_graph,
                identity_seed,
                policy=policy,
                node_filters=[DatasetFilter(dataset_config.fides_key)],
            )
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

        with logger.contextualize(
            privacy_request_id=privacy_request.id,
            privacy_request_source=PrivacyRequestSource.dataset_test.value,
        ):
            try:
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

                run_access_request(
                    privacy_request,
                    policy,
                    dataset_graph,
                    [connection_config],
                    escaped_input_data,
                    self.db,
                    privacy_request_proceed=False,
                )
            except Exception as exc:
                logger.error(f"Error running test access request: {exc}")

        return privacy_request


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
