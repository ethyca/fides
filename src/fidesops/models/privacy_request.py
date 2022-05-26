# pylint: disable=R0401
import json
import logging
from datetime import datetime
from enum import Enum as EnumType
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Session, backref, relationship

from fidesops.api.v1.scope_registry import PRIVACY_REQUEST_CALLBACK_RESUME
from fidesops.common_exceptions import PrivacyRequestPaused
from fidesops.db.base_class import Base, FidesopsBase
from fidesops.graph.config import CollectionAddress
from fidesops.models.audit_log import AuditLog
from fidesops.models.client import ClientDetail
from fidesops.models.fidesops_user import FidesopsUser
from fidesops.models.policy import (
    ActionType,
    Policy,
    PolicyPreWebhook,
    WebhookDirection,
    WebhookTypes,
)
from fidesops.schemas.drp_privacy_request import DrpPrivacyRequestCreate
from fidesops.schemas.external_https import (
    SecondPartyRequestFormat,
    SecondPartyResponseFormat,
    WebhookJWE,
)
from fidesops.schemas.masking.masking_secrets import MaskingSecretCache
from fidesops.schemas.redis_cache import PrivacyRequestIdentity
from fidesops.util.cache import (
    FidesopsRedis,
    get_all_cache_keys_for_privacy_request,
    get_cache,
    get_drp_request_body_cache_key,
    get_encryption_cache_key,
    get_identity_cache_key,
    get_masking_secret_cache_key,
)
from fidesops.util.collection_util import Row
from fidesops.util.oauth_util import generate_jwe

logger = logging.getLogger(__name__)


class PrivacyRequestStatus(str, EnumType):
    """Enum for privacy request statuses, reflecting where they are in the Privacy Request Lifecycle"""

    pending = "pending"
    approved = "approved"
    denied = "denied"
    in_processing = "in_processing"
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
    # When the request was approved/denied
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    # Who approved/denied the request
    reviewed_by = Column(
        String,
        ForeignKey(FidesopsUser.id_field_path, ondelete="SET NULL"),
        nullable=True,
    )
    client_id = Column(
        String,
        ForeignKey(ClientDetail.id_field_path),
        nullable=True,
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

    # passive_deletes="all" prevents audit logs from having their privacy_request_id set to null when
    # a privacy_request is deleted.  We want to retain for record-keeping.
    audit_logs = relationship(
        AuditLog,
        backref="privacy_request",
        lazy="dynamic",
        passive_deletes="all",
        primaryjoin="foreign(AuditLog.privacy_request_id)==PrivacyRequest.id",
    )

    reviewer = relationship(
        "FidesopsUser", backref=backref("privacy_request", passive_deletes=True)
    )

    @classmethod
    def create(cls, db: Session, *, data: Dict[str, Any]) -> FidesopsBase:
        """
        Check whether this object has been passed a `requested_at` value. Default to
        the current datetime if not.
        """
        if data.get("requested_at", None) is None:
            data["requested_at"] = datetime.utcnow()
        return super().create(db=db, data=data)

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

    def cache_drp_request_body(self, drp_request_body: DrpPrivacyRequestCreate) -> None:
        """Sets the identity's values at their specific locations in the Fidesops app cache"""
        cache: FidesopsRedis = get_cache()
        drp_request_body_dict: Dict[str, Any] = dict(drp_request_body)
        for key, value in drp_request_body_dict.items():
            if value is not None:
                # handle nested dict/objects
                if not isinstance(value, (bytes, str, int, float)):
                    cache.set_with_autoexpire(
                        get_drp_request_body_cache_key(self.id, key),
                        repr(value),
                    )
                else:
                    cache.set_with_autoexpire(
                        get_drp_request_body_cache_key(self.id, key),
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

    def cache_masking_secret(self, masking_secret: MaskingSecretCache) -> None:
        """Sets masking encryption secrets in the Fidesops app cache if provided"""
        if not masking_secret:
            return
        cache: FidesopsRedis = get_cache()
        cache.set_with_autoexpire(
            get_masking_secret_cache_key(
                self.id,
                masking_strategy=masking_secret.masking_strategy,
                secret_type=masking_secret.secret_type,
            ),
            FidesopsRedis.encode_obj(masking_secret.secret),
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

    PAUSED_SEPARATOR = "__fidesops_paused_sep__"

    def cache_paused_step_and_collection(
        self,
        paused_step: Optional[ActionType] = None,
        paused_collection: Optional[CollectionAddress] = None,
    ) -> None:
        """
        When a privacy request is paused, cache both the paused step (access or erasure) and the collection
        awaiting manual input.  For example, we might pause a privacy request at the erasure step of the
        postgres_example:address collection.

        The paused_step is needed because we may build and execute multiple graphs as part of running a privacy request.
        An erasure request builds two graphs, one to access the data, and the second to mask it.
        We need to know if we should resume execution from the access or the erasure portion of the request.
        """
        cache: FidesopsRedis = get_cache()
        paused_key = f"PAUSED_LOCATION__{self.id}"

        # Store both the paused separator and paused collection in one value
        cache.set_encoded_object(
            paused_key,
            f"{paused_step.value}{self.PAUSED_SEPARATOR}{paused_collection.value}"
            if paused_step and paused_collection
            else None,
        )

    def get_paused_step_and_collection(
        self,
    ) -> Tuple[Optional[ActionType], Optional[CollectionAddress]]:
        """Get both the paused step (access or erasure) and collection awaiting manual input for the given privacy request.

        The paused step lets us know if we should resume privacy request execution from the "access" or the "erasure"
        portion of the privacy request flow, and the collection tells us where we should cache manual input data for later use,
        In other words, this manual data belongs to this collection.
        """
        cache: FidesopsRedis = get_cache()
        node_addr: str = cache.get_encoded_by_key(f"EN_PAUSED_LOCATION__{self.id}")

        if node_addr:
            split_addr = node_addr.split(self.PAUSED_SEPARATOR)
            return ActionType(split_addr[0]), CollectionAddress.from_string(
                split_addr[1]
            )
        return None, None  # If no cached data, return a tuple of Nones

    def cache_manual_input(
        self, collection: CollectionAddress, manual_rows: Optional[List[Row]]
    ) -> None:
        """Cache manually added rows for the given CollectionAddress"""
        cache: FidesopsRedis = get_cache()
        cache.set_encoded_object(
            f"MANUAL_INPUT__{self.id}__{collection.value}",
            manual_rows,
        )

    def get_manual_input(
        self, collection: CollectionAddress
    ) -> Optional[Dict[str, Optional[List[Row]]]]:
        """Retrieve manually added rows from the cache for the given CollectionAddress.
        Returns the manual key mapped to the manual data.
        """
        cache: FidesopsRedis = get_cache()
        return cache.get_encoded_objects_by_prefix(
            f"MANUAL_INPUT__{self.id}__{collection.value}"
        )

    def trigger_policy_webhook(self, webhook: WebhookTypes) -> None:
        """Trigger a request to a single customer-defined policy webhook. Raises an exception if webhook response
        should cause privacy request execution to stop.

        Pre-Execution webhooks send headers to the webhook in case the service needs to send back instructions
        to halt.  To resume, they use send a request to the reply-to URL with the reply-to-token.
        """
        # temp fix for circular dependency
        from fidesops.service.connectors import HTTPSConnector, get_connector

        https_connector: HTTPSConnector = get_connector(webhook.connection_config)
        request_body = SecondPartyRequestFormat(
            privacy_request_id=self.id,
            direction=webhook.direction.value,
            callback_type=webhook.prefix,
            identity=self.get_cached_identity_data(),
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
        if response_body.derived_identity and any(
            [response_body.derived_identity.dict().values()]
        ):
            logger.info(
                f"Updating known identities on privacy request {self.id} from webhook {webhook.key}."
            )
            self.cache_identity(response_body.derived_identity)

        # Pause execution if instructed
        if response_body.halt and is_pre_webhook:
            raise PrivacyRequestPaused(
                f"Halt instruction received on privacy request {self.id}."
            )

        return

    def start_processing(self, db: Session) -> None:
        """Dispatches this PrivacyRequest throughout the Fidesops System"""
        if self.started_processing_at is None:
            self.started_processing_at = datetime.utcnow()
            self.save(db=db)

    def error_processing(self, db: Session) -> None:
        """Mark privacy request as errored, and note time processing was finished"""
        self.update(
            db,
            data={
                "status": PrivacyRequestStatus.error,
                "finished_processing_at": datetime.utcnow(),
            },
        )


class ExecutionLogStatus(EnumType):
    """Enum for execution log statuses, reflecting where they are in their workflow"""

    in_processing = "in_processing"
    pending = "pending"
    complete = "complete"
    error = "error"
    paused = "paused"
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
