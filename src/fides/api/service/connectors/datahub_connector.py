from typing import Generic, Optional, Dict, Any, Tuple, List

import datahub.emitter.mce_builder as datahub_urn_builder
from datahub.ingestion.graph.client import DataHubGraph, DataHubGraphConfig

from fideslang.models import DatasetCollection, DatasetField
from loguru import logger

from fides.api.models.connectionconfig import (
    ConnectionConfig,
    ConnectionTestStatus,
    ConnectionType,
)
from fides.api.models.sql_models import Dataset
from fides.api.schemas.connection_configuration.connection_secrets_datahub import (
    DatahubSchema,
)
from fides.api.schemas.namespace_meta import BigQueryNamespaceMeta
from fides.api.service.connectors.base_connector import DB_CONNECTOR_TYPE
from fides.api.service.connectors.datahub_query_runner import DatahubQueryRunner


# TODO: make this a configurable variable?
FIDES_CATEGORIES_GLOSSARY_NODE = "FidesDataCategories"


class DatahubConnector:

    def __init__(self, configuration: ConnectionConfig):
        self.configuration = configuration
        self.config = DatahubSchema(**configuration.secrets or {})
        # TODO: use token for authentication
        self.datahub_client = DataHubGraph(
            DataHubGraphConfig(server=str(self.config.datahub_server_url))
        )
        self.datahub_query_runner = DatahubQueryRunner(
            self.datahub_client, FIDES_CATEGORIES_GLOSSARY_NODE
        )

    def test_connection(self) -> Optional[ConnectionTestStatus]:
        logger.info(f"Testing DataHub connection for {self.configuration.key}...")
        try:
            self.datahub_client.test_connection()
            logger.info(
                f"DataHub connection test for {self.configuration.key} succeeded."
            )
            return ConnectionTestStatus.succeeded
        except Exception as e:
            logger.error(
                f"DataHub connection test for {self.configuration.key} failed: {e}"
            )
            return ConnectionTestStatus.failed

    @classmethod
    def build_nested_field_path(
        cls, field: DatasetField, parent_field_path: Optional[str] = None
    ):
        """
        Builds the Datahub field path for a given Fides field, taking as input its
        Datahub parent field path. If no parent_field_path is provided, then it builds
        the initial parent field path for the field.

        Some examples of field paths for an address field with two children are:
        [version=2.0].[type=struct].[type=struct].address (initial parent field path)
        [version=2.0].[type=struct].[type=struct].address.[type=long].zip_code
        [version=2.0].[type=struct].[type=struct].address.[type=string].street_name
        """
        # If the field has no parent, then we build the initial parent field path
        if not parent_field_path:
            return f"[version=2.0].[type=struct].[type=struct].{field.name}"

        # If the field has children, then its type is a struct
        if field.fields:
            return f"{parent_field_path}.[type=struct].{field.name}"

        # If the field has no children, then its type is a primitive type,
        # and we transform its Fides data type into a Datahub data type
        data_type = cls.get_datahub_type(field.fides_meta.data_type)

        return f"{parent_field_path}.[type={data_type}].{field.name}"

    @classmethod
    def get_datahub_type(cls, fides_type):
        # TODO: add more data types?
        fides_type_to_datahub_type = {
            "string": "string",
            "integer": "long",
        }

        if fides_type not in fides_type_to_datahub_type:
            logger.error(f"Unsupported Fides type: {fides_type}")
            raise ValueError(f"Unsupported Fides type: {fides_type}")

        return fides_type_to_datahub_type[fides_type]

    def get_fides_dataset_urn_and_platform(
        self, dataset_namespace: Dict[str, Any], fides_key: str
    ) -> Tuple[str, ConnectionType]:
        """
        Builds the URN for a Fides dataset based on its namespace information.
        """
        platform = dataset_namespace.get("connection_type")

        # For now we only have reliable namespace information for BigQuery datasets
        if platform == ConnectionType.bigquery:
            namespace = BigQueryNamespaceMeta(**dataset_namespace)
            fides_dataset_urn = f"{namespace.project_id}.{namespace.dataset_id}"

        # If the platform attribute has been set, we assume the dataset was generated
        # through Detection and Discovery, so we know the format of the dataset fides key.
        elif platform:
            fides_key_parts = fides_key.split(".")
            if len(fides_key_parts) < 2:
                raise ValueError(
                    f"Cannot build Fides dataset URN for key {fides_key} and platform {platform}: unexpected format."
                )

            # Datasets generated with D & D have the monitor name as the first part of their
            # fides key, so we need to remove it to get the "real" dataset URN.
            fides_dataset_urn = ".".join(fides_key_parts[1:])

        else:
            raise ValueError(
                f"Cannot build Fides dataset URN for key {fides_key}: no platform information."
            )

        return fides_dataset_urn, platform

    def sync_dataset(self, dataset: Dataset):

        dataset_namespace = dataset.fides_meta.get("namespace")

        if not dataset_namespace:
            logger.error(f"Cannot sync dataset without namespace: {dataset.fides_key}")

        try:
            fides_dataset_urn, platform = self.get_fides_dataset_urn_and_platform(
                dataset_namespace, dataset.fides_key
            )

        except Exception as e:
            logger.error(
                f"Failed to sync dataset {dataset.fides_key} with DataHub: {e}"
            )
            return

        # A Datahub Dataset corresponds to a Fides DatasetCollection
        # so we iterate over all collections and sync each one
        for collection_dict in dataset.collections:
            collection = DatasetCollection(**collection_dict)
            collection_urn = f"{fides_dataset_urn}.{collection.name}"
            datahub_urn = datahub_urn_builder.make_dataset_urn(platform, collection_urn)
            self.sync_collection(collection, datahub_urn)

    def sync_collection(self, collection: DatasetCollection, collection_urn: str):
        print("Syncing collection: ", collection_urn)
        if collection.data_categories:
            # TODO: add top-level categories to datahub dataset
            pass

        for field in collection.fields:
            print("field: ", field.name, field.data_categories)
            self.sync_collection_field_and_subfields(collection_urn, field)

    def sync_collection_field_and_subfields(
        self,
        collection_urn: str,
        field: DatasetField,
        parent_field_path: Optional[str] = None,
    ):
        """
        Syncs a Fides field with Datahub, adding all Fides data categories assigned to the field
        as Terms to the Datahub field. If the field has subfields, it recursively syncs them as well.

        Field paths explanation:
            - For a field with no children, its field path is just its name, e.g "email"
            - For a field with children and no parent (a root field), its field path is also its name, e.g "address".
              However we call the string that will be used to build the field path of its children its "nested
              field path", e.g "[version=2.0].[type=struct].[type=struct].address"
            - For a field with a parent, its field path is its parent's nested field path followed by the field's type
              and name, e.g for address.zip_code "[version=2.0].[type=struct].[type=struct].address.[type=long].zip_code"
        """

        # Build the nested field path for the current field, given its parent.
        # This will be used to recursively sync all subfields for the current field.
        nested_field_path = DatahubConnector.build_nested_field_path(
            field, parent_field_path
        )

        # If there is no parent, then the current field path is just the field name.
        # Otherwise, the current field path is the nested field path.
        field_path = field.name if not parent_field_path else nested_field_path

        data_categories = [
            self.datahub_query_runner.get_or_create_term(data_category, "")
            for data_category in field.data_categories
        ]
        self.datahub_query_runner.add_terms_to_dataset_field(
            data_categories,
            collection_urn,
            field_path,
        )

        if field.fields:
            # The parent_field_path for the child fields is the current field's nested_field_path
            new_parent_field_path = nested_field_path

            # Recursively sync all subfields of the current field
            for subfield in field.fields:
                self.sync_collection_field_and_subfields(
                    collection_urn, subfield, new_parent_field_path
                )
