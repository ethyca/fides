from typing import Any, Dict, Optional, Set

from loguru import logger
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Session, relationship

from fides.api.ops.common_exceptions import ValidationError
from fides.api.ops.graph.config import (
    Collection,
    CollectionAddress,
    Dataset,
    Field,
    FieldAddress,
    FieldPath,
    generate_field,
)
from fides.api.ops.graph.data_type import parse_data_type_string
from fides.api.ops.models.connectionconfig import ConnectionConfig, ConnectionType
from fides.api.ops.schemas.dataset import (
    FidesopsDataset,
    FidesopsDatasetField,
    FidesopsDatasetReference,
)
from fides.api.ops.schemas.shared_schemas import FidesOpsKey
from fides.api.ops.util.saas_util import merge_datasets
from fides.lib.db.base_class import Base


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
    dataset = Column(
        MutableDict.as_mutable(JSONB), index=False, unique=False, nullable=False
    )

    connection_config = relationship(
        ConnectionConfig,
        backref="datasets",
    )

    @classmethod
    def create_or_update(cls, db: Session, *, data: Dict[str, Any]) -> "DatasetConfig":
        """
        Look up dataset by config and fides_key. If found, update this dataset, otherwise
        create a new one.
        """
        dataset = DatasetConfig.filter(
            db=db,
            conditions=(
                (DatasetConfig.connection_config_id == data["connection_config_id"])
                & (DatasetConfig.fides_key == data["fides_key"])
            ),
        ).first()

        if dataset:
            dataset.update(db=db, data=data)
        else:
            dataset = cls.create(db=db, data=data)

        return dataset

    def get_graph(self) -> Dataset:
        """
        Return the saved dataset JSON as a dataset graph for query execution.

        For dataset configs associated to a ConnectionConfig of type saas,
        the corresponding SaaS config is merged in as well
        """
        dataset_graph = convert_dataset_to_graph(
            FidesopsDataset(**self.dataset), self.connection_config.key  # type: ignore
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


def to_graph_field(
    field: FidesopsDatasetField, return_all_elements: Optional[bool] = None
) -> Field:
    """Flattens the dataset field type into its graph representation"""

    # NOTE: on the dataset field, annotations like identity & references are
    # declared on the meta object, whereas in our graph representation these are
    # top-level attributes for convenience

    identity = None
    is_pk = False
    is_array = False
    references = []
    meta_section = field.fidesops_meta
    sub_fields = []
    length = None
    data_type_name = None
    read_only = None
    if meta_section:
        identity = meta_section.identity
        if meta_section.primary_key:
            is_pk = meta_section.primary_key
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
                references.append((address, reference.direction))
        if meta_section.length is not None:
            # 'if meta_section.length' will not suffice here, we will want to pass through
            # length for any valid integer if it has been set in the config, including 0.
            #
            # Currently 0 is filtered out by validations but better not to filter out 0's
            # here in case we decide to allow it in the future.
            length = meta_section.length

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
        references=references,
        is_pk=is_pk,
        length=length,
        is_array=is_array,
        sub_fields=sub_fields,
        return_all_elements=return_all_elements,
        read_only=read_only,
    )


def convert_dataset_to_graph(
    dataset: FidesopsDataset, connection_key: FidesOpsKey
) -> Dataset:
    """
    Converts the given Fides dataset dataset into the concrete graph
    representation needed for query execution
    """

    dataset_name = dataset.fides_key
    after = set()
    if dataset.fidesops_meta and dataset.fidesops_meta.after:
        after = set(dataset.fidesops_meta.after)
    logger.debug("Parsing dataset '{}' into graph representation", dataset_name)
    graph_collections = []
    for collection in dataset.collections:
        graph_fields = [to_graph_field(field) for field in collection.fields]
        logger.debug(
            "Parsing dataset {}: parsed collection {} with {} fields",
            dataset_name,
            collection.name,
            len(graph_fields),
        )
        collection_after: Set[CollectionAddress] = set()
        if collection.fidesops_meta and collection.fidesops_meta.after:
            collection_after = {
                CollectionAddress(*s.split(".")) for s in collection.fidesops_meta.after
            }

        graph_collection = Collection(
            name=collection.name, fields=graph_fields, after=collection_after
        )
        graph_collections.append(graph_collection)
    logger.debug(
        "Finished parsing dataset {} with {} collections",
        dataset_name,
        len(graph_collections),
    )

    return Dataset(
        name=dataset_name,
        collections=graph_collections,
        connection_key=connection_key,
        after=after,
    )


def validate_dataset_reference(
    db: Session, dataset_reference: FidesopsDatasetReference
) -> None:
    """
    Validates that the provided FidesopsDatasetReference refers
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
    dataset: Dataset = convert_dataset_to_graph(
        FidesopsDataset(**dataset_config.dataset), dataset_config.fides_key  # type: ignore[arg-type]
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
