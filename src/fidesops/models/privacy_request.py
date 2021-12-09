# pylint: disable=R0401
import logging
from datetime import datetime

import json

from typing import Any, Dict, Optional

from enum import Enum as EnumType
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import (
    Column,
    DateTime,
    Enum as EnumColumn,
    ForeignKey,
    String,
)

from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import relationship, Session

from fidesops.api.v1.scope_registry import PRIVACY_REQUEST_CALLBACK_RESUME
from fidesops.common_exceptions import PrivacyRequestPaused
from fidesops.db.base_class import Base
from fidesops.models.client import ClientDetail
from fidesops.models.policy import (
    Policy,
    ActionType,
    PolicyPreWebhook,
    WebhookDirection,
    WebhookTypes,
)
from fidesops.schemas.external_https import (
    SecondPartyRequestFormat,
    SecondPartyResponseFormat,
    WebhookJWE,
)
from fidesops.schemas.redis_cache import PrivacyRequestIdentity
from fidesops.service.connectors import HTTPSConnector, get_connector
from fidesops.util.cache import (
    get_all_cache_keys_for_privacy_request,
    get_cache,
    get_identity_cache_key,
    FidesopsRedis,
    get_encryption_cache_key,
)
from fidesops.util.oauth_util import generate_jwe

logger = logging.getLogger(__name__)


class PrivacyRequestStatus(EnumType):
    """Enum for privacy request statuses, reflecting where they are in the Privacy Request Lifecycle"""

    in_processing = "in_processing"
    pending = "pending"
    complete = "complete"
    paused = "paused"
    error = "error"


def generate_request_callback_jwe(webhook: PolicyPreWebhook) -> str:
    """Generate a JWE to be used to resume privacy request execution."""
    jwe = WebhookJWE(
        webhook_id=webhook.id,
        scopes=[PRIVACY_REQUEST_CALLBACK_RESUME],
        iat=datetime.now().isoformat(),
    )
    return generate_jwe(json.dumps(jwe.dict()))


class PrivacyRequest(Base):
    """
    The DB ORM model to describe current and historic PrivacyRequests. A privacy request is a
    database record representing a data subject request's progression within the Fidesops system.
    """

    external_id = Column(String, index=True)
    # When the request was dispatched into the Fidesops pipeline
    started_processing_at = Column(DateTime(timezone=True), nullable=True)
    # When the request finished or errored in the Fidesops pipeline
    finished_processing_at = Column(DateTime(timezone=True), nullable=True)
    # When the request was created at the origin
    requested_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(
        EnumColumn(PrivacyRequestStatus),
        index=True,
        nullable=False,
    )
    client_id = Column(
        String,
        ForeignKey(ClientDetail.id_field_path),
    )
    client = relationship(
        ClientDetail,
        backref="privacy_requests",
    )  # Which client submitted the privacy request
    origin = Column(String, nullable=True)  # The origin from the HTTP request
    policy_id = Column(
        String,
        ForeignKey(Policy.id_field_path),
    )
    policy = relationship(
        Policy,
        backref="privacy_requests",
    )

    # passive_deletes="all" prevents execution logs from having their privacy_request_id set to null when
    # a privacy_request is deleted.  We want to retain for record-keeping.
    execution_logs = relationship(
        "ExecutionLog",
        backref="privacy_request",
        lazy="dynamic",
        passive_deletes="all",
        primaryjoin="foreign(ExecutionLog.privacy_request_id)==PrivacyRequest.id",
    )

    def delete(self, db: Session) -> None:
        """
        Clean up the cached data related to this privacy request before deleting this
        object from the database
        """
        cache: FidesopsRedis = get_cache()
        all_keys = get_all_cache_keys_for_privacy_request(privacy_request_id=self.id)
        for key in all_keys:
            cache.delete(key)
        super().delete(db=db)

    def cache_identity(self, identity: PrivacyRequestIdentity) -> None:
        """Sets the identity's values at their specific locations in the Fidesops app cache"""
        cache: FidesopsRedis = get_cache()
        identity_dict: Dict[str, Any] = dict(identity)
        for key, value in identity_dict.items():
            if value is not None:
                cache.set_with_autoexpire(
                    get_identity_cache_key(self.id, key),
                    value,
                )

    def cache_encryption(self, encryption_key: Optional[str] = None) -> None:
        """Sets the encryption key in the Fidesops app cache if provided"""
        if not encryption_key:
            return

        cache: FidesopsRedis = get_cache()
        cache.set_with_autoexpire(
            get_encryption_cache_key(self.id, "key"),
            encryption_key,
        )

    def get_cached_identity_data(self) -> Dict[str, Any]:
        """Retrieves any identity data pertaining to this request from the cache"""
        prefix = f"id-{self.id}-identity-*"
        cache: FidesopsRedis = get_cache()
        keys = cache.keys(prefix)
        return {key.split("-")[-1]: cache.get(key) for key in keys}

    def get_results(self) -> Dict[str, Any]:
        """Retrieves all cached identity data associated with this Privacy Request"""
        cache: FidesopsRedis = get_cache()
        result_prefix = f"{self.id}__*"
        return cache.get_encoded_objects_by_prefix(result_prefix)

    def trigger_policy_webhook(self, webhook: WebhookTypes) -> None:
        """Trigger a request to a single customer-defined policy webhook. Raises an exception if webhook response
        should cause privacy request execution to stop.

        Pre-Execution webhooks send headers to the webhook in case the service needs to send back instructions
        to halt.  To resume, they use send a request to the reply-to URL with the reply-to-token.
        """
        https_connector: HTTPSConnector = get_connector(webhook.connection_config)
        request_body = SecondPartyRequestFormat(
            privacy_request_id=self.id,
            direction=webhook.direction.value,
            callback_type=webhook.prefix,
            identities=self.get_cached_identity_data(),
        )

        headers = {}
        is_pre_webhook = webhook.__class__ == PolicyPreWebhook
        response_expected = webhook.direction == WebhookDirection.two_way
        if is_pre_webhook and response_expected:
            headers = {
                "reply-to": f"/privacy-request/{self.id}/resume",
                "reply-to-token": generate_request_callback_jwe(webhook),
            }

        logger.info(f"Calling webhook {webhook.key} for privacy_request {self.id}")
        response: Optional[SecondPartyResponseFormat] = https_connector.execute(
            request_body.dict(),
            response_expected=response_expected,
            additional_headers=headers,
        )
        if not response:
            return

        response_body = SecondPartyResponseFormat(**response)

        # Cache any new identities
        if response_body.derived_identities and any(
            [response_body.derived_identities.dict().values()]
        ):
            logger.info(
                f"Updating known identities on privacy request {self.id} from webhook {webhook.key}."
            )
            self.cache_identity(response_body.derived_identities)

        # Pause execution if instructed
        if response_body.halt and is_pre_webhook:
            raise PrivacyRequestPaused(
                f"Halt instruction received on privacy request {self.id}."
            )

        return


class ExecutionLogStatus(EnumType):
    """Enum for execution log statuses, reflecting where they are in their workflow"""

    in_processing = "in_processing"
    pending = "pending"
    complete = "complete"
    error = "error"
    retrying = "retrying"


class ExecutionLog(Base):
    """
    Stores the individual execution logs associated with a PrivacyRequest.

    Execution logs contain information about the individual queries as they progress through the workflow
    generated by the query builder.
    """

    # Name of the fides-annotated dataset, for example: my-mongo-db
    dataset_name = Column(String, index=True)
    # Name of the particular collection or table affected
    collection_name = Column(String, index=True)
    # A JSON Array describing affected fields along with their data categories and paths
    fields_affected = Column(MutableList.as_mutable(JSONB), nullable=True)
    # Contains info, warning, or error messages
    message = Column(String)
    action_type = Column(
        EnumColumn(ActionType),
        index=True,
        nullable=False,
    )
    status = Column(
        EnumColumn(ExecutionLogStatus),
        index=True,
        nullable=False,
    )

    privacy_request_id = Column(
        String,
        nullable=False,
        index=True,
    )
