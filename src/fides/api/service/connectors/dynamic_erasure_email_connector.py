import json
from typing import Any, Dict, List, NamedTuple, Optional, Tuple

from fideslang.models import FidesDatasetReference
from loguru import logger
from sqlalchemy.orm import Query, Session

from fides.api.common_exceptions import MessageDispatchException
from fides.api.graph.config import CollectionAddress, GraphDataset
from fides.api.graph.execution import ExecutionNode
from fides.api.models.connectionconfig import ConnectionConfig, ConnectionTestStatus
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.privacy_request import (
    ExecutionLog,
    ExecutionLogStatus,
    PrivacyRequest,
    PrivacyRequestStatus,
    RequestTask,
    TraversalDetails,
)
from fides.api.schemas.connection_configuration.connection_secrets_dynamic_erasure_email import (
    DynamicErasureEmailSchema,
)
from fides.api.schemas.policy import ActionType
from fides.api.service.connectors.base_connector import BaseConnector
from fides.api.service.connectors.base_erasure_email_connector import (
    BaseErasureEmailConnector,
    filter_user_identities_for_connector,
    send_single_erasure_email,
)
from fides.config import get_config

CONFIG = get_config()


class DynamicErasureEmailConnectorException(Exception):
    pass


class ProcessedConfig(NamedTuple):
    graph_dataset: GraphDataset
    connector: BaseConnector
    collection_address: CollectionAddress
    email_field: str
    vendor_field: str


class DynamicErasureEmailConnector(BaseErasureEmailConnector):
    """Email Erasure Connector that performs a lookup for the email to use."""

    config: DynamicErasureEmailSchema

    def get_config(self, configuration: ConnectionConfig) -> DynamicErasureEmailSchema:
        return DynamicErasureEmailSchema(**configuration.secrets or {})

    def get_email_and_vendor_from_custom_request_fields(
        self,
        db: Session,
        processed_config: ProcessedConfig,
        privacy_request: PrivacyRequest,
    ) -> Optional[Tuple[str, str]]:
        """
        Gets the custom request fields from the privacy request and uses them to perform a
        standalone query on the connector, in order to retrieve the value of the email address
        we need to send the erasure email to (specified in field_name).

        Returns a tuple of the form (email, vendor_name), or None if an error occurred or
        some data was not valid.
        """
        # The following code is a bit hacky, but we need to instantiate a RequestTask
        # and an Execution node in order to execute a standalone retrieval query on the connector.
        # The only fields we really care about in the RequestTask are those related to the collection
        # and to the dataset itself.
        # TODO: Once custom request fields can be processed as part of the DSR graph, this logic
        # will be simplified a lot, since the query for the email address will be performed at the
        # Node level as part of the graph traversal and execution. Here we will just need to retrieve
        # it from its corresponding (real) RequestTask and use it to send the email.

        collection_address = processed_config.collection_address
        graph_dataset = processed_config.graph_dataset

        # Search for the collection in the dataset that contains the email recipient field
        collections = [
            c
            for c in graph_dataset.collections
            if c.name == collection_address.collection
        ]

        if not collections:
            logger.error(
                "Collection with name '{}' not found in dataset '{}'. Skipping email send for privacy request with id {}.",
                collection_address.collection,
                graph_dataset.name,
                privacy_request.id,
            )
            self.error_privacy_request(
                db,
                privacy_request,
                f"Connector configuration references invalid collection {collection_address.collection} for dataset {graph_dataset.name}",
            )
            return None

        collection = collections[0]
        collection_data = json.loads(
            # Serializes with duck-typing behavior, no longer the default in Pydantic v2
            # Needed for serializing nested collection fields
            collection.model_dump_json(serialize_as_any=True)
        )

        # Create an in-memory request task, needed for the execution node
        request_task = RequestTask(
            privacy_request_id=privacy_request.id,
            collection_address=collection_address.value,
            dataset_name=collection_address.dataset,
            collection=collection_data,
            traversal_details=TraversalDetails.create_empty_traversal(
                graph_dataset.connection_key
            ).model_dump(mode="json"),
        )
        execution_node = ExecutionNode(request_task)

        # Get the custom request fields from the privacy request.
        # Returns something like {"site_id": {"value": "1234", "label": "Site Id"}}
        custom_request_fields = (
            privacy_request.get_persisted_custom_privacy_request_fields()
        )

        # We execute a standalone retrieval query on the connector to get the email address
        # based on the custom request fields on the privacy request and the field_name
        # provided as part of the connection config.
        # Following the previous example, this query would be something like
        # SELECT email_address FROM site_info WHERE site_id = '1234'
        retrieved_data = processed_config.connector.execute_standalone_retrieval_query(
            node=execution_node,
            fields=[processed_config.email_field, processed_config.vendor_field],
            filters={
                custom_field_name: [custom_field_data["value"]]
                for custom_field_name, custom_field_data in custom_request_fields.items()
            },
        )
        if not retrieved_data:
            logger.error(
                "Custom request field lookup yielded no results. Skipping email send for privacy request with id {}.",
                privacy_request.id,
            )
            self.error_privacy_request(
                db,
                privacy_request,
                "Custom request field lookup produced no results: no email address matching custom request fields was found.",
            )
            return None

        if len(retrieved_data) > 1:
            logger.error(
                "Custom request field lookup yielded multiple results. Skipping email send for privacy request with id {}.",
                privacy_request.id,
            )
            self.error_privacy_request(
                db,
                privacy_request,
                "Custom request field lookup produced multiple results: multiple email addresses returned for provided custom fields.",
            )
            return None

        email = retrieved_data[0][processed_config.email_field]
        vendor = retrieved_data[0][processed_config.vendor_field]

        return email, vendor

    def get_collection_and_field_from_reference(
        self,
        db: Session,
        privacy_requests: Query,
        dataset_reference: FidesDatasetReference,
    ) -> Tuple[str, str]:
        dataset_key = dataset_reference.dataset  # pylint: disable=no-member

        # Field should be of the form collection_name.field_name, potentially with nested fields
        # e.g collection_name.field_name.nested_field_name, so splitting by "." should give
        # a list of length greater than or equal to 2.
        split_field = dataset_reference.field.split(".")  # pylint: disable=no-member

        if len(split_field) < 2:
            field = dataset_reference.field  # pylint: disable=no-member
            error_log = f"Invalid dataset reference field {field} for dataset {dataset_key}. Skipping erasure email send for connector: {self.configuration.key}."
            logger.error(error_log)
            self.error_all_privacy_requests(
                db,
                privacy_requests,
                f"Connector configuration references invalid dataset field {field} for dataset {dataset_key}.",
            )
            raise DynamicErasureEmailConnectorException(error_log)

        # Get collection name and field name
        collection_name = split_field[0]
        field_name = ".".join(split_field[1:])

        return collection_name, field_name

    def process_connector_config(
        self, db: Session, privacy_requests: Query
    ) -> ProcessedConfig:
        """
        Validates and processes the connector config. Returns a ProcessedConfig that has the graph_dataset
        corresponding to the referenced dataset config, the associated connector instance (different from the
        DynamicErasureEmailConnector), and the collection address and fields of the dataset where we need to
        lookup the recipient email address and vendor name.

        Raises a DynamicErasureEmailConnectorException if the connector configuration is invalid.
        """
        # Import here to avoid circular import error
        # TODO: once we incorporate custom request fields into the DSR graph logic  we won't need this import here,
        # so ignorning cyclic import warning for now
        from fides.api.service.connectors import (  # pylint: disable=cyclic-import
            get_connector,
        )

        email_dataset_reference = self.config.recipient_email_address
        email_dataset_key = email_dataset_reference.dataset  # pylint: disable=no-member

        vendor_dataset_reference = self.config.third_party_vendor_name
        vendor_datset_key = (
            vendor_dataset_reference.dataset  # pylint: disable=no-member
        )

        if email_dataset_key != vendor_datset_key:
            error_log = f"Dynamic Erasure Email Connector with key {self.configuration.key} references different datasets for email and vendor fields. Skipping erasure email send."
            logger.error(error_log)
            self.error_all_privacy_requests(
                db,
                privacy_requests,
                "Connector configuration references different datasets for email and vendor fields.",
            )
            raise DynamicErasureEmailConnectorException(error_log)

        collection_name, email_field_name = (
            self.get_collection_and_field_from_reference(
                db, privacy_requests, self.config.recipient_email_address
            )
        )

        vendor_collection_name, vendor_field_name = (
            self.get_collection_and_field_from_reference(
                db, privacy_requests, self.config.third_party_vendor_name
            )
        )

        if collection_name != vendor_collection_name:
            error_log = f"Dynamic Erasure Email Connector with key {self.configuration.key} references different collections for email and vendor fields. Skipping erasure email send."
            logger.error(error_log)
            self.error_all_privacy_requests(
                db,
                privacy_requests,
                "Connector configuration references different collections for email and vendor fields.",
            )
            raise DynamicErasureEmailConnectorException(error_log)

        # We get the DatasetConfig instance using the dataset key provided in the configuration
        dataset_config: Optional[DatasetConfig] = DatasetConfig.get_by(
            db, field="fides_key", value=email_dataset_key
        )

        if not dataset_config:
            error_log = f"DatasetConfig with key {email_dataset_key} not found. Skipping erasure email send for connector: {self.configuration.key}."
            logger.error(error_log)
            self.error_all_privacy_requests(
                db,
                privacy_requests,
                f"Connector configuration references DatasetConfig with key {email_dataset_key}, but such DatasetConfig was not found.",
            )

            raise DynamicErasureEmailConnectorException(error_log)

        # Get the graph dataset from the dataset config
        graph_dataset: GraphDataset = dataset_config.get_graph()

        # Build the CollectionAddress using the dataset name and the collection name
        collection_address = CollectionAddress(graph_dataset.name, collection_name)

        # Get the corresponding ConnectionConfig instance
        connection_config: ConnectionConfig = (
            db.execute(
                db.query(ConnectionConfig).filter(
                    ConnectionConfig.id == dataset_config.connection_config_id
                )
            )
            .scalars()
            .first()
        )

        # Instatiate the ConnectionConfig's connector so that we can execute the query
        # to retrieve the email addresses based on the custom request fields
        connector = get_connector(connection_config)

        return ProcessedConfig(
            graph_dataset,
            connector,
            collection_address,
            email_field_name,
            vendor_field_name,
        )

    def batch_email_send(self, privacy_requests: Query) -> None:
        logger.debug(
            "Starting batch_email_send for connector: {} ...", self.configuration.name
        )

        db: Session = Session.object_session(self.configuration)
        proccessed_config = self.process_connector_config(db, privacy_requests)

        skipped_privacy_requests: List[str] = []
        # We'll batch identities for each email address
        # so we'll only send 1 email to each email address
        batched_identities: Dict[str, List[str]] = {}
        vendor_names: Dict[str, str] = {}

        for privacy_request in privacy_requests:
            try:
                custom_field_data = (
                    self.get_email_and_vendor_from_custom_request_fields(
                        db,
                        proccessed_config,
                        privacy_request,
                    )
                )

                # if we couldn't retrieve the email address / vendor, we skip the privacy request
                # (error was already logged within the function, so we just continue to the
                # next privacy request)
                if not custom_field_data:
                    continue

                email, vendor_name = custom_field_data

                user_identities: Dict[str, Any] = (
                    privacy_request.get_cached_identity_data()
                )
                filtered_user_identities: Dict[str, Any] = (
                    filter_user_identities_for_connector(self.config, user_identities)
                )

                # If there are no user identities, we just skip the privacy request
                if not filtered_user_identities:
                    skipped_privacy_requests.append(privacy_request.id)
                    self.add_skipped_log(db, privacy_request)
                    continue

                if email not in batched_identities:
                    batched_identities[email] = []

                batched_identities[email].extend(filtered_user_identities.values())
                vendor_names[email] = vendor_name

            except Exception as exc:
                logger.error(
                    "An error occurred when retrieving email from custom request fields for connector {}. Skipping email send for privacy request with id {}. Error: {}",
                    self.configuration.key,
                    privacy_request.id,
                    exc,
                )
                self.error_privacy_request(db, privacy_request, str(exc))

        if not batched_identities:
            logger.info(
                "Skipping erasure email send for connector: '{}'. "
                "No corresponding user identities or email addresses found for pending privacy requests.",
                self.configuration.key,
            )
            return

        logger.info(
            "Sending batched erasure email for connector {}...",
            self.configuration.key,
        )

        for email_address, identities in batched_identities.items():
            try:
                send_single_erasure_email(
                    db=db,
                    subject_email=email_address,
                    subject_name=vendor_names[email_address],
                    batch_identities=identities,
                    test_mode=False,
                )
            except MessageDispatchException as exc:
                logger.info("Erasure email failed with exception {}", exc)
                raise

        # create an audit event for each privacy request ID
        for privacy_request in privacy_requests:
            if privacy_request.id not in skipped_privacy_requests:
                ExecutionLog.create(
                    db=db,
                    data={
                        "connection_key": self.configuration.key,
                        "dataset_name": self.configuration.name
                        or self.configuration.key,
                        "collection_name": self.configuration.name
                        or self.configuration.key,
                        "privacy_request_id": privacy_request.id,
                        "action_type": ActionType.erasure,
                        "status": ExecutionLogStatus.complete,
                        "message": f"Erasure email instructions dispatched for '{self.configuration.name}'",
                    },
                )

    def error_all_privacy_requests(
        self, db: Session, privacy_requests: Query, failure_reason: str
    ) -> None:
        """
        Creates an ExecutionLog with status error for each privacy request in the batch, and sets the
        privacy request status to error.
        """
        for privacy_request in privacy_requests:
            self.error_privacy_request(db, privacy_request, failure_reason)

    def error_privacy_request(
        self,
        db: Session,
        privacy_request: PrivacyRequest,
        failure_reason: Optional[str],
    ) -> None:
        """
        Creates an ExecutionLog with status error for the privacy request, using the failure_reason
        as the message, and sets the privacy request status to error.
        """
        ExecutionLog.create(
            db=db,
            data={
                "connection_key": self.configuration.key,
                "dataset_name": self.configuration.name or self.configuration.key,
                "collection_name": self.configuration.name or self.configuration.key,
                "privacy_request_id": privacy_request.id,
                "action_type": ActionType.erasure,
                "status": ExecutionLogStatus.error,
                "message": failure_reason
                or "An error occurred when trying to send the erasure email",
            },
        )
        privacy_request.status = PrivacyRequestStatus.error
        privacy_request.save(db)

    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """
        Sends an email to the "test_email" configured, just to establish that the email workflow is working.
        """
        logger.info("Starting test connection to {}", self.configuration.key)

        db = Session.object_session(self.configuration)

        try:
            if not self.config.test_email_address:
                raise MessageDispatchException(
                    f"Cannot test connection. No test email defined for {self.configuration.name}"
                )
            # synchronous for now since failure to send is considered a connection test failure
            send_single_erasure_email(
                db=db,
                subject_email=self.config.test_email_address,
                subject_name="Test Vendor",  # Needs to be a string since vendor depends con custom request field values
                batch_identities=list(self.identities_for_test_email.values()),
                test_mode=True,
            )
        except MessageDispatchException as exc:
            logger.info("Email connector test failed with exception {}", exc)
            return ConnectionTestStatus.failed
        return ConnectionTestStatus.succeeded
