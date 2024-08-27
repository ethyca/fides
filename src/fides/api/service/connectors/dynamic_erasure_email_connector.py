import json
from typing import Any, Dict, List, Optional

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


class DynamicErasureEmailConnector(BaseErasureEmailConnector):
    """Email Erasure Connector that performs a lookup for the email to use."""

    config: DynamicErasureEmailSchema

    def get_config(self, configuration: ConnectionConfig) -> DynamicErasureEmailSchema:
        return DynamicErasureEmailSchema(**configuration.secrets or {})

    def get_email_address_from_custom_request_fields(
        self,
        connector: BaseConnector,
        graph_dataset: GraphDataset,
        privacy_request: PrivacyRequest,
        collection_address: CollectionAddress,
        field_name: str,
    ) -> Optional[str]:
        """
        Gets the custom request fields from the privacy request and uses them to perform a
        standalone query on the connector, in order to retrieve the value of the email address
        we need to send the erasure email to (specified in field_name).

        Returns the found email address, or None if none were found. Expects that the query using
        the provided custom request fields returns 1 single row, otherwise an error is logged and
        None is returned.
        """
        # The following code is a bit hacky, but we need to instantiate a RequestTask
        # and an Execution node in order to execute a standalone retrieval query on the connector.
        # The only fields we really care about in the RequestTask are those related to the collection
        # and to the dataset itself.
        # TODO: Once custom request fields can be processed as part of the DSR graph, this logic
        # will be simplified a lot, since the query for the email address will be performed at the
        # Node level as part of the graph traversal and execution. Here we will just need to retrieve
        # it from its corresponding (real) RequestTask and use it to send the email.

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
        email_recipient_data = connector.execute_standalone_retrieval_query(
            node=execution_node,
            fields=[field_name],
            filters={
                custom_field_name: [custom_field_data["value"]]
                for custom_field_name, custom_field_data in custom_request_fields.items()
            },
        )
        if not email_recipient_data:
            logger.error(
                "Custom request field lookup yielded no results. Skipping email send for privacy request with id {}.",
                privacy_request.id,
            )
            return None

        if len(email_recipient_data) > 1:
            logger.error(
                "Custom request field lookup yielded multiple results. Skipping email send for privacy request with id {}.",
                privacy_request.id,
            )
            return None

        return email_recipient_data[0][field_name]

    def batch_email_send(self, privacy_requests: Query) -> None:
        # Import here to avoid circular import error
        # TODO: once we incorporate custom request fields into the DSR graph logic
        # we won't need this import here, so ignorning cyclic import warning for now
        from fides.api.service.connectors import (  # pylint: disable=cyclic-import
            get_connector,
        )

        logger.debug(
            "Starting batch_email_send for connector: {} ...", self.configuration.name
        )

        db: Session = Session.object_session(self.configuration)

        dataset_reference = self.config.recipient_email_address
        dataset_key = dataset_reference.dataset  # pylint: disable=no-member

        # We get the DatasetConfig instance using the dataset key provided in the configuration
        dataset_config: Optional[DatasetConfig] = DatasetConfig.get_by(
            db, field="fides_key", value=dataset_key
        )

        if not dataset_config:
            logger.error(
                "DatasetConfig with key '{}' not found. Skipping erasure email send for connector: '{}'.",
                dataset_key,
                self.configuration.name,
            )
            return

        # Get the graph dataset from the dataset config
        graph_dataset: GraphDataset = dataset_config.get_graph()

        # Field should be of the form collection_name.field_name, potentially with nested fields
        # i.e collection_name.field_name.nested_field_name
        # so splitting by "." should give a list of length greater than or equal to 2.
        split_field = dataset_reference.field.split(".")  # pylint: disable=no-member

        if len(split_field) < 2:
            logger.error(
                "Invalid dataset reference field '{}' for dataset {}. Skipping erasure email send for connector: '{}'.",
                dataset_reference.field,
                dataset_key,
                self.configuration.name,
            )
            return

        # Build the CollectionAddress using the dataset name and the collection name
        collection_name = split_field[0]
        collection_address = CollectionAddress(graph_dataset.name, collection_name)
        # And get the field name from the datasetreference
        field_name = ".".join(split_field[1:])

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

        skipped_privacy_requests: List[str] = []
        # We'll batch identities for each email address
        # so we'll only send 1 email to each email address
        batched_identities: Dict[str, List[str]] = {}

        for privacy_request in privacy_requests:
            try:
                email = self.get_email_address_from_custom_request_fields(
                    connector,
                    graph_dataset,
                    privacy_request,
                    collection_address,
                    field_name,
                )

                user_identities: Dict[str, Any] = (
                    privacy_request.get_cached_identity_data()
                )
                filtered_user_identities: Dict[str, Any] = (
                    filter_user_identities_for_connector(self.config, user_identities)
                )

                # If we couldn't get the email or the user identities, we skip the privacy request
                if not email or not filtered_user_identities:
                    skipped_privacy_requests.append(privacy_request.id)
                    self.add_skipped_log(db, privacy_request)
                    continue

                if email not in batched_identities:
                    batched_identities[email] = []

                batched_identities[email].extend(filtered_user_identities.values())

            # TODO: try not to catch all exceptions, but rather specific ones
            except Exception as exc:
                logger.error(
                    "An error occurred when retrieving email from custom request fields for connector {}. Skipping email send for privacy request with id {}. Error: {}",
                    self.configuration.name,
                    privacy_request.id,
                    exc,
                )
                ExecutionLog.create(
                    db=db,
                    data={
                        "connection_key": self.configuration.key,
                        "dataset_name": self.configuration.name,
                        "collection_name": self.configuration.name,
                        "privacy_request_id": privacy_request.id,
                        "action_type": ActionType.erasure,
                        "status": ExecutionLogStatus.error,
                        "message": "An error occurred when retrieving email from custom request fields. Email not sent.",
                    },
                )

        if not batched_identities:
            logger.info(
                "Skipping erasure email send for connector: '{}'. "
                "No corresponding user identities or email addresses found for pending privacy requests.",
                self.configuration.name,
            )
            return

        logger.info(
            "Sending batched erasure email for connector {}...",
            self.configuration.name,
        )

        for email_address, identities in batched_identities.items():
            try:
                send_single_erasure_email(
                    db=db,
                    subject_email=email_address,
                    subject_name=self.config.third_party_vendor_name,
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
                        "dataset_name": self.configuration.name,
                        "collection_name": self.configuration.name,
                        "privacy_request_id": privacy_request.id,
                        "action_type": ActionType.erasure,
                        "status": ExecutionLogStatus.complete,
                        "message": f"Erasure email instructions dispatched for '{self.configuration.name}'",
                    },
                )

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
                subject_name=self.config.third_party_vendor_name,
                batch_identities=list(self.identities_for_test_email.values()),
                test_mode=True,
            )
        except MessageDispatchException as exc:
            logger.info("Email connector test failed with exception {}", exc)
            return ConnectionTestStatus.failed
        return ConnectionTestStatus.succeeded
