import logging
from typing import Dict, Any, Set

from boto3 import Session
from sqlalchemy import (
    Column,
    ForeignKey,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship

from fidesops.db.base_class import Base
from fidesops.graph.config import (
    Collection,
    Field,
    FieldAddress,
    Dataset,
    CollectionAddress,
    generate_field,
)
from fidesops.graph.data_type import parse_data_type_string
from fidesops.models.connectionconfig import ConnectionConfig
from fidesops.schemas.dataset import FidesopsDataset, FidesopsDatasetField
from fidesops.schemas.shared_schemas import FidesOpsKey
from fidesops.util.logger import NotPii

logger = logging.getLogger(__name__)


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
        Return the saved dataset JSON as a dataset graph for query execution
        """
        return convert_dataset_to_graph(
            FidesopsDataset(**self.dataset), self.connection_config.key
        )


def to_graph_field(field: FidesopsDatasetField) -> Field:
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
                address = FieldAddress(
                    reference.dataset, ref_collection, ".".join(ref_fields)
                )
                references.append((address, reference.direction))
        if meta_section.length is not None:
            # 'if meta_section.length' will not suffice here, we will want to pass through
            # length for any valid integer if it has been set in the config, including 0.
            #
            # Currently 0 is filtered out by validations but better not to filter out 0's
            # here in case we decide to allow it in the future.
            length = meta_section.length

        (data_type_name, is_array) = parse_data_type_string(meta_section.data_type)

    if field.fields:
        sub_fields = [to_graph_field(fld) for fld in field.fields]

    return generate_field(
        name=field.name,
        data_categories=field.data_categories,
        identity=identity,
        data_type_name=data_type_name,
        references=references,
        is_pk=is_pk,
        length=length,
        is_array=is_array,
        sub_fields=sub_fields,
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
    logger.debug(f"Parsing dataset '{dataset_name}' into graph representation")
    graph_collections = []
    for collection in dataset.collections:
        graph_fields = [to_graph_field(field) for field in collection.fields]
        logger.debug(
            "Parsing dataset %s: parsed collection %s with %s fields",
            NotPii(dataset_name),
            NotPii(collection.name),
            NotPii(len(graph_fields)),
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
        "Finished parsing dataset %s with %s collections",
        NotPii(dataset_name),
        NotPii(len(graph_collections)),
    )

    return Dataset(
        name=dataset_name,
        collections=graph_collections,
        connection_key=connection_key,
        after=after,
    )
