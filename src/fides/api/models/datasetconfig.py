from typing import Any, Dict, Optional, Set

from fideslang.models import Dataset, DatasetField, FidesDatasetReference
from fideslang.validation import FidesKey
from loguru import logger
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.orm import Session, relationship

from fides.api.common_exceptions import ValidationError
from fides.api.db.base_class import Base
from fides.api.graph.config import (
    Collection,
    CollectionAddress,
    Field,
    FieldAddress,
    FieldPath,
    GraphDataset,
    generate_field,
)
from fides.api.graph.data_type import parse_data_type_string
from fides.api.models.connectionconfig import ConnectionConfig, ConnectionType
from fides.api.service.masking.strategy.masking_strategy import MaskingStrategy
from fides.api.util.saas_util import merge_datasets

from fides.api.models.sql_models import (  # type: ignore[attr-defined] # isort: skip
    Dataset as CtlDataset,
)


class DatasetConfig(Base):
    """
    Stores a Fides-annotated dataset that belongs to a ConnectionConfig.

    NOTE: For simplicity, this only stores the dataset's fides_key for indexing,
    and the rest of the dataset is stored as JSON. See fideslang.models.Collection
    for details
    """

    connection_config_id = Column(
        String, ForeignKey(ConnectionConfig.id_field_path), nullable=False
    )
    fides_key = Column(String, index=True, unique=True, nullable=False)
    ctl_dataset_id = Column(
        String, ForeignKey(CtlDataset.id), index=True, nullable=False
    )

    connection_config = relationship(
        "ConnectionConfig",
        back_populates="datasets",
    )

    ctl_dataset = relationship(
        CtlDataset,
        backref="dataset_configs",
    )

    @classmethod
    def create_or_update(cls, db: Session, *, data: Dict[str, Any]) -> "DatasetConfig":  # type: ignore[override]
        """
        Create or update both DatasetConfig and CTL Dataset.
        Updates existing CTL Dataset if found by ID or fides_key, otherwise creates new one.
        """

        def upsert_ctl_dataset(
            dataset_contents: Dict[str, Any],
            existing_ctl_dataset_id: Optional[str] = None,
        ) -> CtlDataset:
            """Create new or update existing CTL dataset."""
            validated_data = Dataset(**dataset_contents).model_dump(mode="json")

            if existing_ctl_dataset_id:
                ctl_dataset = (
                    db.query(CtlDataset)
                    .filter(CtlDataset.id == existing_ctl_dataset_id)
                    .first()
                )
            else:
                ctl_dataset = (
                    db.query(CtlDataset)
                    .filter(CtlDataset.fides_key == dataset_contents.get("fides_key"))
                    .first()
                )

            if ctl_dataset:
                for key, val in validated_data.items():
                    setattr(ctl_dataset, key, val)
            else:
                ctl_dataset = CtlDataset(**validated_data)

            db.add(ctl_dataset)
            db.commit()
            db.refresh(ctl_dataset)
            return ctl_dataset

        # Make a copy of data to avoid modifications
        data_copy = data.copy()
        dataset_contents = data_copy.pop("dataset", None)

        # Check for existing dataset config
        dataset_config = cls.filter(
            db=db,
            conditions=(
                (cls.connection_config_id == data_copy["connection_config_id"])
                & (cls.fides_key == data_copy["fides_key"])
            ),
        ).first()
        existing_ctl_dataset_id = (
            dataset_config.ctl_dataset_id if dataset_config else None
        )

        # Handle CTL dataset if dataset data is provided
        if dataset_contents:
            ctl_dataset = upsert_ctl_dataset(dataset_contents, existing_ctl_dataset_id)
            data_copy["ctl_dataset_id"] = ctl_dataset.id

        # Create or update DatasetConfig
        if dataset_config:
            dataset_config.update(db=db, data=data_copy)
        else:
            dataset_config = cls.create(db=db, data=data_copy)

        return dataset_config

    def get_graph(self) -> GraphDataset:
        """
        Return the saved dataset JSON as a dataset graph for query execution.

        For dataset configs associated to a ConnectionConfig of type saas,
        the corresponding SaaS config is merged in as well
        """
        dataset_graph = convert_dataset_to_graph(
            Dataset.model_validate(self.ctl_dataset), self.connection_config.key  # type: ignore
        )
        if (
            self.connection_config.connection_type == ConnectionType.saas
            and self.connection_config.saas_config is not None
            and self.connection_config.saas_config["fides_key"] == self.fides_key
        ):
            dataset_graph = merge_datasets(
                dataset_graph,
                self.connection_config.get_saas_config().get_graph(self.connection_config.secrets),  # type: ignore
            )
        else:
            logger.debug(
                "Connection config with key {} is not a saas config, skipping merge dataset",
                self.connection_config.key,
            )

        return dataset_graph

    def get_dataset_with_stubbed_collection(self) -> GraphDataset:
        """
        Return a Dataset with a single mock Collection for use in building a graph
        where we only want one node per dataset, instead of one node per collection.  Note that
        the expectation is that there would be no dependencies between nodes on the eventual graph, and the graph
        doesn't require information stored at the collection-level.

        The single Collection will be the resource that gets practically added to the graph, but the intent
        is that this single node represents the overall Dataset, and will execute Dataset-level requests,
        not Collection-level requests.
        """
        dataset_graph = self.get_graph()
        stubbed_collection = Collection(name=dataset_graph.name, fields=[], after=set())

        dataset_graph.collections = [stubbed_collection]
        return dataset_graph

    def get_identities_and_references(self) -> Set[str]:
        """
        Returns all identity and dataset references in the dataset.
        If a field has multiple references only the first reference will be considered.
        """
        result: Set[str] = set()
        dataset: GraphDataset = self.get_graph()
        for collection in dataset.collections:
            # Process the identities in the collection
            result.update(collection.identities().values())
            for _, field_refs in collection.references().items():
                # Take first reference only, we only care that this collection is reachable,
                # how we get there doesn't matter for our current use case
                ref, edge_direction = field_refs[0]
                if edge_direction == "from" and ref.dataset != self.fides_key:
                    result.add(ref.value)
        return result


def to_graph_field(
    field: DatasetField, return_all_elements: Optional[bool] = None
) -> Field:
    """Flattens the dataset field type into its graph representation"""

    # NOTE: on the dataset field, annotations like identity & references are
    # declared on the meta object, whereas in our graph representation these are
    # top-level attributes for convenience

    identity = None
    is_pk = False
    is_array = False
    references = []
    meta_section = field.fides_meta
    sub_fields = []
    length = None
    data_type_name = None
    read_only = None
    custom_request_field = None
    masking_strategy_override = None

    if meta_section:
        identity = meta_section.identity
        if meta_section.primary_key:
            is_pk = meta_section.primary_key
        if meta_section.custom_request_field:
            custom_request_field = meta_section.custom_request_field
        if meta_section.references:
            for reference in meta_section.references:
                # Split the "field" address (e.g. "customers.id") into its component
                # parts: (collection, field). If there are multiple levels of nesting,
                # force these all into the field address.
                #
                # For example, the following dataset field reference:
                # ```
                # references:
                #   - dataset: postgres_example_test_dataset
                #     field: address.id
                # ```
                # becomes: (postgres_example_test_dataset, address, id)
                #
                # Whereas a deeply nested field:
                # references:
                #   - dataset: mongo_example_test_dataset
                #     field: customer_details.extra.meta.created
                # ```
                # becomes: (mongo_example_test_dataset, customer_details, extra.meta.created)
                (ref_collection, *ref_fields) = reference.field.split(".")
                address = FieldAddress(reference.dataset, ref_collection, *ref_fields)
                references.append(
                    (
                        address,
                        (
                            reference.direction.value  # Transforming reference back to a literal first for Pydantic v2
                            if reference.direction
                            else reference.direction
                        ),
                    )
                )
        if meta_section.length is not None:
            # 'if meta_section.length' will not suffice here, we will want to pass through
            # length for any valid integer if it has been set in the config, including 0.
            #
            # Currently 0 is filtered out by validations but better not to filter out 0's
            # here in case we decide to allow it in the future.
            length = meta_section.length

        if meta_section.masking_strategy_override:
            masking_strategy_override = meta_section.masking_strategy_override

        (data_type_name, is_array) = parse_data_type_string(meta_section.data_type)

        if meta_section.return_all_elements:
            # If specified on array field, lifts and passes into sub-fields, for example,
            # arrays of objects
            return_all_elements = True

        if meta_section.read_only:
            read_only = True

    if field.fields:
        sub_fields = [to_graph_field(fld, return_all_elements) for fld in field.fields]
    return generate_field(
        name=field.name,
        data_categories=field.data_categories,
        identity=identity,
        data_type_name=data_type_name,  # type: ignore
        references=references,  # type: ignore
        is_pk=is_pk,
        length=length,
        is_array=is_array,
        sub_fields=sub_fields,
        return_all_elements=return_all_elements,
        read_only=read_only,
        custom_request_field=custom_request_field,
        masking_strategy_override=masking_strategy_override,
    )


def convert_dataset_to_graph(
    dataset: Dataset, connection_key: FidesKey
) -> GraphDataset:
    """
    Converts the given Fides dataset into the concrete graph
    representation needed for query execution
    """

    dataset_name = dataset.fides_key
    after = set()
    if dataset.fides_meta and dataset.fides_meta.after:
        after = set(dataset.fides_meta.after)
    logger.debug("Parsing dataset '{}' into graph representation", dataset_name)
    graph_collections = []
    for collection in dataset.collections:
        collection_skip_processing: bool = bool(
            collection.fides_meta and collection.fides_meta.skip_processing
        )
        if collection_skip_processing:
            logger.debug(
                "Skipping collection {} on dataset {} marked with skip_processing",
                collection.name,
                dataset_name,
            )
            continue
        graph_fields = [to_graph_field(field) for field in collection.fields]
        logger.debug(
            "Parsing dataset {}: parsed collection {} with {} fields",
            dataset_name,
            collection.name,
            len(graph_fields),
        )
        collection_after: Set[CollectionAddress] = set()
        if collection.fides_meta and collection.fides_meta.after:
            collection_after = {
                CollectionAddress(*s.split(".")) for s in collection.fides_meta.after
            }

        collection_erase_after: Set[CollectionAddress] = set()
        if collection.fides_meta and collection.fides_meta.erase_after:
            collection_erase_after = {
                CollectionAddress(*s.split("."))
                for s in collection.fides_meta.erase_after
            }

        masking_override = None
        if collection.fides_meta and collection.fides_meta.masking_strategy_override:
            masking_override = collection.fides_meta.masking_strategy_override

        collection_partitioning = None
        if collection.fides_meta and collection.fides_meta.partitioning:
            collection_partitioning = collection.fides_meta.partitioning

        graph_collection = Collection(
            name=collection.name,
            fields=graph_fields,
            after=collection_after,
            erase_after=collection_erase_after,
            masking_strategy_override=masking_override,
            skip_processing=collection_skip_processing,
            data_categories=(
                set(collection.data_categories) if collection.data_categories else set()
            ),
            partitioning=collection_partitioning,
        )
        graph_collections.append(graph_collection)
    logger.debug(
        "Finished parsing dataset {} with {} collections",
        dataset_name,
        len(graph_collections),
    )

    return GraphDataset(
        name=dataset_name,
        collections=graph_collections,
        connection_key=connection_key,
        after=after,
    )


def validate_dataset_reference(
    db: Session, dataset_reference: FidesDatasetReference
) -> None:
    """
    Validates that the provided FidesDatasetReference refers
    to a `Dataset`, `Collection` and `Field` that actually exist in the DB.
    Raises a `ValidationError` if not.
    """
    dataset_config: Optional[DatasetConfig] = (
        db.query(DatasetConfig)
        .filter(DatasetConfig.fides_key == dataset_reference.dataset)
        .first()
    )
    if dataset_config is None:
        raise ValidationError(
            f"Unknown dataset '{dataset_reference.dataset}' referenced by external reference"
        )

    dataset: GraphDataset = convert_dataset_to_graph(
        Dataset.model_validate(dataset_config.ctl_dataset), dataset_config.fides_key  # type: ignore[arg-type]
    )
    collection_name, *field_name = dataset_reference.field.split(".")
    if not field_name or not collection_name or not field_name[0]:
        raise ValidationError(
            "Dataset reference field specifications must include at least two dot-separated components"
        )
    collection = next(
        (
            collection
            for collection in dataset.collections
            if collection.name == collection_name
        ),
        None,
    )
    if collection is None:
        raise ValidationError(
            f"Unknown collection '{collection_name}' in dataset '{dataset_config.fides_key}' referenced by external reference"
        )
    field = collection.field(FieldPath.parse(*field_name))
    if field is None:
        raise ValidationError(
            f"Unknown field '{dataset_reference.field}' in dataset '{dataset_config.fides_key}' referenced by external reference"
        )


def validate_masking_strategy_override(dataset: Dataset) -> None:
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

    for collection in dataset.collections:
        for field in collection.fields:
            validate_field(field)
