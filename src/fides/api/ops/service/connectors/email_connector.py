from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.ops.common_exceptions import (
    MessageDispatchException,
    PrivacyRequestErasureEmailSendRequired,
)
from fides.api.ops.graph.config import CollectionAddress, FieldPath
from fides.api.ops.graph.traversal import TraversalNode
from fides.api.ops.models.connectionconfig import (
    ConnectionConfig,
    ConnectionTestStatus,
    ConnectionType,
)
from fides.api.ops.models.datasetconfig import DatasetConfig
from fides.api.ops.models.messaging import MessagingConfig
from fides.api.ops.models.policy import CurrentStep, Policy, Rule
from fides.api.ops.models.privacy_request import (
    CheckpointActionRequired,
    ManualAction,
    PrivacyRequest,
)
from fides.api.ops.schemas.connection_configuration import EmailSchema
from fides.api.ops.schemas.messaging.messaging import (
    MessagingActionType,
    MessagingServiceType,
)
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.connectors.base_connector import BaseConnector
from fides.api.ops.service.connectors.query_config import ManualQueryConfig
from fides.api.ops.service.messaging.message_dispatch_service import dispatch_message
from fides.api.ops.util.collection_util import Row, append
from fides.lib.models.audit_log import AuditLog, AuditLogAction


class EmailConnector(BaseConnector[None]):
    def query_config(self, node: TraversalNode) -> ManualQueryConfig:
        """Intentionally reusing the ManualQueryConfig here. We're only using methods off of the base
        QueryConfig class here.
        """
        return ManualQueryConfig(node)

    def create_client(self) -> None:
        """Stub"""

    def close(self) -> None:
        """N/A for the EmailConnector"""

    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """
        Sends an email to the "test_email" configured, just to establish that the email workflow is working.
        """
        config = EmailSchema(**self.configuration.secrets or {})
        logger.info("Starting test connection to {}", self.configuration.key)

        db = Session.object_session(self.configuration)

        email_service: Optional[str] = _get_email_messaging_config_service_type(db=db)

        try:
            # synchronous for now since failure to send is considered a connection test failure
            dispatch_message(
                db=db,
                action_type=MessagingActionType.MESSAGE_ERASURE_REQUEST_FULFILLMENT,
                to_identity=Identity(email=config.test_email),
                service_type=email_service,
                message_body_params=[
                    CheckpointActionRequired(
                        step=CurrentStep.erasure,
                        collection=CollectionAddress("test_dataset", "test_collection"),
                        action_needed=[
                            ManualAction(
                                locators={"id": ["example_id"]},
                                get=None,
                                update={
                                    "test_field": "null_rewrite",
                                },
                            )
                        ],
                    )
                ],
            )
        except MessageDispatchException as exc:
            logger.info("Email connector test failed with exception {}", exc)
            return ConnectionTestStatus.failed
        return ConnectionTestStatus.succeeded

    def retrieve_data(  # type: ignore
        self,
        node: TraversalNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        input_data: Dict[str, List[Any]],
    ) -> Optional[List[Row]]:
        """Access requests are not supported at this time."""
        logger.info(
            "Access requests not supported for email connector '{}' at this time.",
            node.address.value,
        )
        return []

    def mask_data(  # type: ignore
        self,
        node: TraversalNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        rows: List[Row],
        input_data: Dict[str, List[Any]],
    ) -> None:
        """Cache instructions for how to mask data in this collection.
        One email will be sent for all collections in this dataset at the end of the privacy request execution.
        """

        manual_action: ManualAction = self.build_masking_instructions(
            node, policy, input_data
        )

        logger.info("Caching action needed for collection: '{}", node.address.value)
        privacy_request.cache_email_connector_template_contents(
            step=CurrentStep.erasure,
            collection=node.address,
            action_needed=[manual_action],
        )

        # Raises a special exception just to update the ExecutionLog message.  The email send itself
        # is postponed until all collections have been visited.
        raise PrivacyRequestErasureEmailSendRequired("email prepared")

    def build_masking_instructions(
        self, node: TraversalNode, policy: Policy, input_data: Dict[str, List[Any]]
    ) -> ManualAction:
        """
        Generate information on how to find and mask relevant records on this collection.

        Because we don't have any rows from a completed "access request" for this source, we pass on both "access"
        and "erasure" instructions to the source.
        """

        # Values for locating relevant records on the current collection.
        locators: Dict[str, Any] = node.typed_filtered_values(input_data)
        # Add additional locators from the same dataset for which we don't have data
        for edge in node.incoming_edges_from_same_dataset():
            append(locators, edge.f2.field_path.string_path, str(edge.f1))

        # Build which fields to mask and how to mask
        fields_to_mask_by_rule: Dict[Rule, List[FieldPath]] = self.query_config(
            node
        ).build_rule_target_field_paths(policy)
        mask_map: Dict[str, Any] = {}
        for rule, field_paths in fields_to_mask_by_rule.items():
            for rule_field_path in field_paths:
                # Map field paths to the specified masking strategy.  If multiple rules target
                # the same field path, the last one will win
                mask_map[rule_field_path.string_path] = (
                    rule.masking_strategy.get("strategy")
                    if rule.masking_strategy
                    else None
                )

        # Returns a ManualAction even if there are no fields to mask on this collection,
        # because the locators still may be needed to find data to mask on dependent collections
        return ManualAction(locators=locators, update=mask_map if mask_map else None)


def email_connector_erasure_send(db: Session, privacy_request: PrivacyRequest) -> None:
    """
    Send emails to configured third-parties with instructions on how to erase remaining data.
    Combined all the collections on each email-based dataset into one email.
    """
    email_dataset_configs = db.query(DatasetConfig, ConnectionConfig).filter(
        DatasetConfig.connection_config_id == ConnectionConfig.id,
        ConnectionConfig.connection_type == ConnectionType.email,
    )
    for ds, cc in email_dataset_configs:
        template_values: List[
            CheckpointActionRequired
        ] = privacy_request.get_email_connector_template_contents_by_dataset(
            CurrentStep.erasure, ds.dataset.get("fides_key")
        )

        if not template_values:
            logger.info(
                "No email sent: no template values saved for '{}'",
                ds.dataset.get("fides_key"),
            )
            return

        if not any(
            (
                action_required.action_needed[0].update
                if action_required and action_required.action_needed
                else False
                for action_required in template_values
            )
        ):
            logger.info(
                "No email sent: no masking needed on '{}'", ds.dataset.get("fides_key")
            )
            return

        email_service: Optional[str] = _get_email_messaging_config_service_type(db=db)

        dispatch_message(
            db,
            action_type=MessagingActionType.MESSAGE_ERASURE_REQUEST_FULFILLMENT,
            to_identity=Identity(email=cc.secrets.get("to_email")),
            service_type=email_service,
            message_body_params=template_values,
        )

        logger.info(
            "Email send succeeded for request '{}' for dataset: '{}'",
            privacy_request.id,
            ds.dataset.get("fides_key"),
        )
        AuditLog.create(
            db=db,
            data={
                "user_id": "system",
                "privacy_request_id": privacy_request.id,
                "action": AuditLogAction.email_sent,
                "message": f"Erasure email instructions dispatched for '{ds.dataset.get('fides_key')}'",
            },
        )


def _get_email_messaging_config_service_type(db: Session) -> Optional[str]:
    """
    Email connectors require that an email messaging service has been configured.
    Prefers Twilio if both Twilio email AND Mailgun has been configured.
    """
    messaging_configs: Optional[List[MessagingConfig]] = MessagingConfig.query(
        db=db
    ).all()
    if not messaging_configs:
        # let messaging dispatch service handle non-existent service
        return None
    twilio_email_config = next(
        (
            config
            for config in messaging_configs
            if config.service_type == MessagingServiceType.TWILIO_EMAIL
        ),
        None,
    )
    mailgun_config = next(
        (
            config
            for config in messaging_configs
            if config.service_type == MessagingServiceType.MAILGUN
        ),
        None,
    )
    if twilio_email_config:
        # we prefer twilio over mailgun
        return MessagingServiceType.TWILIO_EMAIL.value
    if mailgun_config:
        return MessagingServiceType.MAILGUN.value
    return None
