from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy.orm import Query, Session

from fides.api.common_exceptions import MessageDispatchException
from fides.api.models.connectionconfig import (
    ConnectionConfig,
    ConnectionTestStatus,
    ConnectionType,
)
from fides.api.models.privacy_request import ExecutionLog, PrivacyRequest
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.connection_configuration import EmailSchema
from fides.api.schemas.policy import ActionType
from fides.api.service.connectors.base_erasure_email_connector import (
    BaseErasureEmailConnector,
    filter_user_identities_for_connector,
    send_single_erasure_email,
)
from fides.config import get_config

CONFIG = get_config()

ERASURE_EMAIL_CONNECTOR_TYPES = [
    ConnectionType.generic_erasure_email,
    ConnectionType.attentive_email,
    ConnectionType.dynamic_erasure_email,
]


class GenericErasureEmailConnector(BaseErasureEmailConnector):
    """Generic Email Erasure Connector that can be overridden for specific vendors"""

    config: EmailSchema

    def get_config(self, configuration: ConnectionConfig) -> EmailSchema:
        return EmailSchema(**configuration.secrets or {})

    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """
        Sends an email to the "test_email" configured, just to establish that the email workflow is working.
        """
        logger.info("Starting test connection to {}", self.configuration.key)

        db = Session.object_session(self.configuration)

        try:
            if not self.config.test_email_address:
                raise MessageDispatchException(
                    f"Cannot test connection. No test email defined for {self.configuration.key}"
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
            logger.info(
                "Email connector test for {} failed with exception {}",
                self.configuration.key,
                exc,
            )
            return ConnectionTestStatus.failed
        return ConnectionTestStatus.succeeded

    def batch_email_send(self, privacy_requests: Query, batch_id: str) -> None:
        skipped_privacy_requests: List[str] = []
        batched_identities: List[str] = []
        db = Session.object_session(self.configuration)

        for privacy_request in privacy_requests:
            user_identities: Dict[str, Any] = privacy_request.get_cached_identity_data()
            filtered_user_identities: Dict[str, Any] = (
                filter_user_identities_for_connector(self.config, user_identities)
            )
            if filtered_user_identities:
                batched_identities.extend(filtered_user_identities.values())
            else:
                skipped_privacy_requests.append(privacy_request.id)
                self.add_skipped_log(db, privacy_request)

        if not batched_identities:
            logger.info(
                "Skipping erasure email send for connector '{}' and batch '{}'. "
                "No corresponding user identities found for pending privacy requests.",
                self.configuration.key,
                batch_id,
            )
            return

        logger.info(
            "Sending batch erasure email {} for connector {}...",
            batch_id,
            self.configuration.key,
        )

        try:
            send_single_erasure_email(
                db=db,
                subject_email=self.config.recipient_email_address,
                subject_name=self.config.third_party_vendor_name,
                batch_identities=batched_identities,
                test_mode=False,
            )
        except MessageDispatchException as exc:
            message = f"Batch erasure email {batch_id} for connector {self.configuration.key} failed with exception {exc}"
            logger.error(message)
            self.error_all_privacy_requests(
                db,
                privacy_requests.filter(
                    PrivacyRequest.id.notin_(skipped_privacy_requests)
                ),
                message,
            )
            raise

        # create an audit event for each privacy request ID
        for privacy_request in privacy_requests:
            if privacy_request.id not in skipped_privacy_requests:
                ExecutionLog.create(
                    db=db,
                    data={
                        "connection_key": self.configuration.key,
                        "dataset_name": self.configuration.name_or_key,
                        "collection_name": self.configuration.name_or_key,
                        "privacy_request_id": privacy_request.id,
                        "action_type": ActionType.erasure,
                        "status": ExecutionLogStatus.complete,
                        "message": f"Erasure email instructions dispatched for '{self.configuration.name_or_key}'",
                    },
                )
