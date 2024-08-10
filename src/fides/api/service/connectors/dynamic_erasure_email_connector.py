from typing import Any, Dict, List

from loguru import logger
from sqlalchemy.orm import Query, Session

from fides.api.common_exceptions import MessageDispatchException
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.privacy_request import ExecutionLog, ExecutionLogStatus
from fides.api.schemas.connection_configuration.connection_secrets_dynamic_erasure_email import (
    DynamicErasureEmailSchema,
)
from fides.api.schemas.policy import ActionType
from fides.api.service.connectors.erasure_email_connector import (
    GenericErasureEmailConnector,
    filter_user_identities_for_connector,
    send_single_erasure_email,
)
from fides.config import get_config

CONFIG = get_config()


class DynamicErasureEmailConnector(GenericErasureEmailConnector):
    """Email Erasure Connector that performs a lookup for the email to use."""

    def __init__(self, configuration: ConnectionConfig):
        super().__init__(configuration)
        self.config = DynamicErasureEmailSchema(**configuration.secrets or {})

    def batch_email_send(self, privacy_requests: Query) -> None:
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
                "Skipping erasure email send for connector: '{}'. "
                "No corresponding user identities found for pending privacy requests.",
                self.configuration.name,
            )
            return

        logger.info(
            "Sending batched erasure email for connector {}...",
            self.configuration.name,
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
