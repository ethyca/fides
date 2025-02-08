from abc import ABC, abstractmethod
from typing import List, Optional, Sequence, Type, TypeVar

from fideslang.models import Dataset as FideslangDataset
from fideslang.models import DatasetCollection, DatasetField
from fideslang.validation import FidesKey
from loguru import logger
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from fides.api import common_exceptions
from fides.api.common_exceptions import (
    SaaSConfigNotFoundException,
    TraversalError,
    ValidationError,
)
from fides.api.graph.graph import DatasetGraph
from fides.api.graph.traversal import Traversal
from fides.api.models.connectionconfig import ConnectionConfig, ConnectionType
from fides.api.models.datasetconfig import convert_dataset_to_graph, to_graph_field
from fides.api.schemas.dataset import DatasetTraversalDetails, ValidateDatasetResponse
from fides.api.service.masking.strategy.masking_strategy import MaskingStrategy
from fides.api.util.data_category import DataCategory as DefaultTaxonomyDataCategories
from fides.api.util.data_category import get_data_categories_from_db
from fides.api.util.saas_util import merge_datasets

T = TypeVar("T", bound="DatasetValidationStep")


class DatasetValidationStep(ABC):
    """Abstract base class for dataset validation steps"""

    @classmethod
    def _find_all_validation_steps(cls: Type[T]) -> List[Type[T]]:
        """Find all subclasses of DatasetValidationStep"""
        return cls.__subclasses__()

    @abstractmethod
    def validate(self, context: "DatasetValidationContext") -> None:
        """Perform validation step"""


class DatasetValidationContext:
    """Context object holding state for validation"""

    def __init__(
        self,
        db: Session,
        dataset: FideslangDataset,
        connection_config: Optional[ConnectionConfig] = None,
    ):
        self.db = db
        self.dataset = dataset
        self.connection_config = connection_config
        self.traversal_details: Optional[DatasetTraversalDetails] = None


class MaskingStrategyValidationStep(DatasetValidationStep):
    """Validates masking strategy overrides"""

    def validate(self, context: DatasetValidationContext) -> None:
        """
        Validates that field-level masking overrides do not require secret keys.
        When handling a privacy request, we use the `cache_data` function to review the policies and identify which masking strategies need secret keys generated and cached.
        Currently, we are avoiding the additional complexity of scanning datasets for masking overrides.
        """

        def validate_field(dataset_field: DatasetField) -> None:
            if dataset_field.fields:
                for subfield in dataset_field.fields:
                    validate_field(subfield)
            else:
                if (
                    dataset_field.fides_meta
                    and dataset_field.fides_meta.masking_strategy_override
                ):
                    strategy: MaskingStrategy = MaskingStrategy.get_strategy(
                        dataset_field.fides_meta.masking_strategy_override.strategy,
                        dataset_field.fides_meta.masking_strategy_override.configuration,  # type: ignore[arg-type]
                    )
                    if strategy.secrets_required():
                        raise ValidationError(
                            f"Masking strategy '{strategy.name}' with required secrets not allowed as an override."
                        )

        for collection in context.dataset.collections:
            for field in collection.fields:
                validate_field(field)


class DataCategoryValidationStep(DatasetValidationStep):
    """Validates data categories against database"""

    def validate(self, context: DatasetValidationContext) -> None:
        defined_data_categories = get_data_categories_from_db(context.db)
        validate_data_categories_against_db(context.dataset, defined_data_categories)


class SaaSValidationStep(DatasetValidationStep):
    """Validates SaaS-specific requirements"""

    def validate(self, context: DatasetValidationContext) -> None:
        if (
            context.connection_config
            and context.connection_config.connection_type == ConnectionType.saas
        ):
            _validate_saas_dataset(context.connection_config, context.dataset)


class TraversalValidationStep(DatasetValidationStep):
    """Validates dataset traversability"""

    def validate(self, context: DatasetValidationContext) -> None:
        if not context.connection_config:
            logger.warning(
                "Skipping traversal validation, no connection config provided"
            )
            return

        try:
            graph = convert_dataset_to_graph(
                context.dataset, context.connection_config.key
            )

            if (
                context.connection_config
                and context.connection_config.connection_type == ConnectionType.saas
            ):
                graph = merge_datasets(
                    graph,
                    context.connection_config.get_saas_config().get_graph(
                        context.connection_config.secrets
                    ),
                )

            complete_graph = DatasetGraph(graph)
            unique_identities = set(complete_graph.identity_keys.values())
            Traversal(complete_graph, {k: None for k in unique_identities})

            context.traversal_details = DatasetTraversalDetails(
                is_traversable=True, msg=None
            )
        except (TraversalError, ValidationError) as err:
            context.traversal_details = DatasetTraversalDetails(
                is_traversable=False, msg=str(err)
            )


class DatasetValidator:
    """Dataset validator that allows selective validation steps"""

    def __init__(
        self,
        db: Session,
        dataset: FideslangDataset,
        connection_config: Optional[ConnectionConfig] = None,
        skip_steps: Optional[List[Type[DatasetValidationStep]]] = None,
    ):
        self.context = DatasetValidationContext(db, dataset, connection_config)
        self.skip_steps = skip_steps or []
        self.validation_steps = [
            step()
            for step in DatasetValidationStep._find_all_validation_steps()
            if step not in self.skip_steps
        ]

    def validate(self) -> ValidateDatasetResponse:
        """Execute selected validation steps and return response"""
        for step in self.validation_steps:
            step.validate(self.context)

        return ValidateDatasetResponse(
            dataset=self.context.dataset,
            traversal_details=self.context.traversal_details,
        )


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
