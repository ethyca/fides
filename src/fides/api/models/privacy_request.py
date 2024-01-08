# pylint: disable=R0401, C0302

from __future__ import annotations

import json
from datetime import datetime, timedelta
from enum import Enum as EnumType
from typing import Any, Dict, List, Optional, Set, Union

from celery.result import AsyncResult
from loguru import logger
from pydantic import BaseModel
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import Session, backref, relationship
from sqlalchemy_utils.types.encrypted.encrypted_type import (
    AesGcmEngine,
    StringEncryptedType,
)

from fides.api.common_exceptions import (
    IdentityVerificationException,
    ManualWebhookFieldsUnset,
    NoCachedManualWebhookEntry,
    PrivacyRequestPaused,
)
from fides.api.cryptography.cryptographic_util import generate_salt, hash_with_salt
from fides.api.db.base_class import Base  # type: ignore[attr-defined]
from fides.api.db.base_class import JSONTypeOverride
from fides.api.db.util import EnumColumn
from fides.api.graph.config import CollectionAddress
from fides.api.graph.graph_differences import GraphRepr
from fides.api.models.audit_log import AuditLog
from fides.api.models.client import ClientDetail
from fides.api.models.fides_user import FidesUser
from fides.api.models.manual_webhook import AccessManualWebhook
from fides.api.models.policy import (
    CurrentStep,
    Policy,
    PolicyPreWebhook,
    WebhookDirection,
    WebhookTypes,
)
from fides.api.oauth.jwt import generate_jwe
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.drp_privacy_request import DrpPrivacyRequestCreate
from fides.api.schemas.external_https import SecondPartyResponseFormat, WebhookJWE
from fides.api.schemas.masking.masking_secrets import MaskingSecretCache
from fides.api.schemas.policy import ActionType
from fides.api.schemas.redis_cache import (
    CustomPrivacyRequestField as CustomPrivacyRequestFieldSchema,
)
from fides.api.schemas.redis_cache import Identity, IdentityBase
from fides.api.tasks import celery_app
from fides.api.util.cache import (
    FidesopsRedis,
    get_all_cache_keys_for_privacy_request,
    get_async_task_tracking_cache_key,
    get_cache,
    get_custom_privacy_request_field_cache_key,
    get_drp_request_body_cache_key,
    get_encryption_cache_key,
    get_identity_cache_key,
    get_masking_secret_cache_key,
)
from fides.api.util.collection_util import Row
from fides.api.util.constants import API_DATE_FORMAT
from fides.api.util.identity_verification import IdentityVerificationMixin
from fides.common.api.scope_registry import PRIVACY_REQUEST_CALLBACK_RESUME
from fides.config import CONFIG

# Locations from which privacy request execution can be resumed, in order.
EXECUTION_CHECKPOINTS = [
    CurrentStep.pre_webhooks,
    CurrentStep.access,
    CurrentStep.erasure,
    CurrentStep.consent,
    CurrentStep.email_post_send,
    CurrentStep.post_webhooks,
]


class ManualAction(FidesSchema):
    """
    Surface how to retrieve or mask data in a database-agnostic way

    - 'locators' are similar to the SQL "WHERE" information.
    - 'get' contains a list of fields that should be retrieved from the source
    - 'update' is a dictionary of fields and the replacement value/masking strategy
    """

    locators: Dict[str, Any]
    get: Optional[List[str]]
    update: Optional[Dict[str, Any]]


class CheckpointActionRequired(FidesSchema):
    """Describes actions needed on a particular checkpoint.

    Examples are a paused collection that needs manual input, a failed collection that
    needs to be restarted, or a collection where instructions need to be emailed to a third
    party to complete the request.
    """

    step: CurrentStep
    collection: Optional[CollectionAddress]
    action_needed: Optional[List[ManualAction]] = None

    class Config:
        arbitrary_types_allowed = True


EmailRequestFulfillmentBodyParams = Dict[
    CollectionAddress, Optional[CheckpointActionRequired]
]


class PrivacyRequestStatus(str, EnumType):
    """Enum for privacy request statuses, reflecting where they are in the Privacy Request Lifecycle"""

    identity_unverified = "identity_unverified"
    requires_input = "requires_input"
    pending = "pending"
    approved = "approved"
    denied = "denied"
    in_processing = "in_processing"
    complete = "complete"
    paused = "paused"
    awaiting_email_send = "awaiting_email_send"
    canceled = "canceled"
    error = "error"


class CallbackType(EnumType):
    """We currently have two types of Policy Webhooks: pre and post"""

    pre = "pre"
    post = "post"


class SecondPartyRequestFormat(BaseModel):
    """
    The request body we will use when calling a user's HTTP endpoint from fides.api
    This class is defined here to avoid circular import issues between this file and
    models.policy
    """

    privacy_request_id: str
    privacy_request_status: PrivacyRequestStatus
    direction: WebhookDirection
    callback_type: CallbackType
    identity: Identity
    policy_action: Optional[ActionType]

    class Config:
        """Using enum values"""

        use_enum_values = True


def generate_request_callback_jwe(webhook: PolicyPreWebhook) -> str:
    """Generate a JWE to be used to resume privacy request execution."""
    jwe = WebhookJWE(
        webhook_id=webhook.id,
        scopes=[PRIVACY_REQUEST_CALLBACK_RESUME],
        iat=datetime.now().isoformat(),
    )
    return generate_jwe(
        json.dumps(jwe.dict()),
        CONFIG.security.app_encryption_key,
    )


class PrivacyRequest(IdentityVerificationMixin, Base):  # pylint: disable=R0904
    """
    The DB ORM model to describe current and historic PrivacyRequests.
    A privacy request is a database record representing the request's
    progression within the Fides system.
    """

    external_id = Column(String, index=True)
    # When the request was dispatched into the Fides pipeline
    started_processing_at = Column(DateTime(timezone=True), nullable=True)
    # When the request finished or errored in the Fides pipeline
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
        ForeignKey(FidesUser.id_field_path, ondelete="SET NULL"),
        nullable=True,
    )
    custom_privacy_request_fields_approved_by = Column(
        String,
        ForeignKey(FidesUser.id_field_path, ondelete="SET NULL"),
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

    cancel_reason = Column(String(200))
    canceled_at = Column(DateTime(timezone=True), nullable=True)
    consent_preferences = Column(MutableList.as_mutable(JSONB), nullable=True)

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

    privacy_request_error = relationship(
        "PrivacyRequestError",
        back_populates="privacy_request",
        cascade="delete, delete-orphan",
    )

    reviewer = relationship(
        FidesUser,
        backref=backref("privacy_requests", passive_deletes=True),
        foreign_keys=[reviewed_by],
    )

    paused_at = Column(DateTime(timezone=True), nullable=True)
    identity_verified_at = Column(DateTime(timezone=True), nullable=True)
    custom_privacy_request_fields_approved_at = Column(
        DateTime(timezone=True), nullable=True
    )
    due_date = Column(DateTime(timezone=True), nullable=True)
    awaiting_email_send_at = Column(DateTime(timezone=True), nullable=True)

    # Non-DB fields that are optionally added throughout the codebase
    action_required_details: Optional[CheckpointActionRequired] = None
    execution_and_audit_logs_by_dataset: Optional[property] = None
    resume_endpoint: Optional[str] = None

    @property
    def days_left(self: PrivacyRequest) -> Union[int, None]:
        if self.due_date is None:
            return None

        delta = self.due_date.date() - datetime.utcnow().date()
        return delta.days

    @classmethod
    def create(
        cls, db: Session, *, data: Dict[str, Any], check_name: bool = True
    ) -> PrivacyRequest:
        """
        Check whether this object has been passed a `requested_at` value. Default to
        the current datetime if not.
        """
        if data.get("requested_at", None) is None:
            data["requested_at"] = datetime.utcnow()

        policy: Optional[Policy] = Policy.get_by(
            db=db,
            field="id",
            value=data["policy_id"],
        )

        if policy:
            if policy.execution_timeframe:
                requested_at = data["requested_at"]
                if isinstance(requested_at, str):
                    requested_at = datetime.strptime(requested_at, API_DATE_FORMAT)
                data["due_date"] = requested_at + timedelta(
                    days=policy.execution_timeframe
                )

        return super().create(db=db, data=data, check_name=check_name)

    def delete(self, db: Session) -> None:
        """
        Clean up the cached and persisted data related to this privacy request before
        deleting this object from the database
        """
        cache: FidesopsRedis = get_cache()
        all_keys = get_all_cache_keys_for_privacy_request(privacy_request_id=self.id)
        for key in all_keys:
            cache.delete(key)

        for provided_identity in self.provided_identities:  # type: ignore[attr-defined]
            provided_identity.delete(db=db)
        super().delete(db=db)

    def cache_identity(self, identity: Identity) -> None:
        """Sets the identity's values at their specific locations in the Fides app cache"""
        cache: FidesopsRedis = get_cache()
        identity_dict: Dict[str, Any] = dict(identity)
        for key, value in identity_dict.items():
            if value is not None:
                cache.set_with_autoexpire(
                    get_identity_cache_key(self.id, key),
                    value,
                )

    def cache_custom_privacy_request_fields(
        self,
        custom_privacy_request_fields: Optional[
            Dict[str, CustomPrivacyRequestFieldSchema]
        ] = None,
    ) -> None:
        """Sets each of the custom privacy request fields values under their own key in the cache"""
        if not custom_privacy_request_fields:
            return

        if not CONFIG.execution.allow_custom_privacy_request_field_collection:
            return

        if CONFIG.execution.allow_custom_privacy_request_fields_in_request_execution:
            cache: FidesopsRedis = get_cache()
            for key, item in custom_privacy_request_fields.items():
                if item is not None:
                    cache.set_with_autoexpire(
                        get_custom_privacy_request_field_cache_key(self.id, key),
                        item.value,
                    )
        else:
            logger.info(
                "Custom fields from privacy request {}, but config setting 'CONFIG.execution.allow_custom_privacy_request_fields_in_request_execution' is set to false and prevents their usage.",
                self.id,
            )

    def persist_identity(self, db: Session, identity: Identity) -> None:
        """
        Stores the identity provided with the privacy request in a secure way, compatible with
        blind indexing for later searching and audit purposes.
        """
        identity_dict: Dict[str, Any] = dict(identity)
        for key, value in identity_dict.items():
            if value:
                hashed_value = ProvidedIdentity.hash_value(value)
                ProvidedIdentity.create(
                    db=db,
                    data={
                        "privacy_request_id": self.id,
                        "field_name": key,
                        # We don't need to manually encrypt this field, it's done at the ORM level
                        "encrypted_value": {"value": value},
                        "hashed_value": hashed_value,
                    },
                )

    def persist_custom_privacy_request_fields(
        self,
        db: Session,
        custom_privacy_request_fields: Dict[str, CustomPrivacyRequestFieldSchema],
    ) -> None:
        if not custom_privacy_request_fields:
            return

        if CONFIG.execution.allow_custom_privacy_request_field_collection:
            for key, item in custom_privacy_request_fields.items():
                if item.value:
                    hashed_value = CustomPrivacyRequestField.hash_value(item.value)
                    CustomPrivacyRequestField.create(
                        db=db,
                        data={
                            "privacy_request_id": self.id,
                            "field_name": key,
                            "field_label": item.label,
                            "encrypted_value": {"value": item.value},
                            "hashed_value": hashed_value,
                        },
                    )
        else:
            logger.info(
                "Custom fields provided in privacy request {}, but config setting 'CONFIG.execution.allow_custom_privacy_request_field_collection' prevents their storage.",
                self.id,
            )

    def get_persisted_identity(self) -> Identity:
        """
        Retrieves persisted identity fields from the DB.
        """
        schema = Identity()
        for field in self.provided_identities:  # type: ignore[attr-defined]
            setattr(
                schema,
                field.field_name.value,
                field.encrypted_value["value"],
            )
        return schema

    def get_persisted_custom_privacy_request_fields(self) -> Dict[str, Any]:
        return {
            field.field_name: {
                "label": field.field_label,
                "value": field.encrypted_value["value"],
            }
            for field in self.custom_fields  # type: ignore[attr-defined]
        }

    def verify_identity(self, db: Session, provided_code: str) -> "PrivacyRequest":
        """Verify the identification code supplied by the user
        If verified, change the status of the request to "pending", and set the datetime the identity was verified.
        """
        if not self.status == PrivacyRequestStatus.identity_unverified:
            raise IdentityVerificationException(
                f"Invalid identity verification request. Privacy request '{self.id}' status = {self.status.value}."  # type: ignore # pylint: disable=no-member
            )

        self._verify_identity(provided_code=provided_code)

        self.status = PrivacyRequestStatus.pending
        self.identity_verified_at = datetime.utcnow()
        self.save(db)
        return self

    def cache_task_id(self, task_id: str) -> None:
        """Sets a task_id for this privacy request's asynchronous execution."""
        cache: FidesopsRedis = get_cache()
        cache.set(
            get_async_task_tracking_cache_key(self.id),
            task_id,
        )

    def get_cached_task_id(self) -> Optional[str]:
        """Gets the cached task ID for this privacy request."""
        cache: FidesopsRedis = get_cache()
        task_id = cache.get(get_async_task_tracking_cache_key(self.id))
        return task_id

    def get_async_execution_task(self) -> Optional[AsyncResult]:
        """Returns a task reflecting the state of this privacy request's asynchronous execution."""
        task_id = self.get_cached_task_id()
        res: AsyncResult = AsyncResult(task_id)
        return res

    def cache_drp_request_body(self, drp_request_body: DrpPrivacyRequestCreate) -> None:
        """Sets the identity's values at their specific locations in the Fides app cache"""
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
        """Sets the encryption key in the Fides app cache if provided"""
        if not encryption_key:
            return

        cache: FidesopsRedis = get_cache()
        cache.set_with_autoexpire(
            get_encryption_cache_key(self.id, "key"),
            encryption_key,
        )

    def cache_masking_secret(self, masking_secret: MaskingSecretCache) -> None:
        """Sets masking encryption secrets in the Fides app cache if provided"""
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

    def get_cached_custom_privacy_request_fields(self) -> Dict[str, Any]:
        """Retrieves any custom fields pertaining to this request from the cache"""
        prefix = f"id-{self.id}-custom-privacy-request-field-*"
        cache: FidesopsRedis = get_cache()
        keys = cache.keys(prefix)
        return {key.split("-")[-1]: cache.get(key) for key in keys}

    def get_results(self) -> Dict[str, Any]:
        """Retrieves all cached identity data associated with this Privacy Request"""
        cache: FidesopsRedis = get_cache()
        result_prefix = f"{self.id}__*"
        return cache.get_encoded_objects_by_prefix(result_prefix)

    def cache_email_connector_template_contents(
        self,
        step: CurrentStep,
        collection: CollectionAddress,
        action_needed: List[ManualAction],
    ) -> None:
        """Cache the raw details needed to email to a third party service regarding action they must complete
        on their end for the given collection"""
        cache_action_required(
            cache_key=f"EMAIL_INFORMATION__{self.id}__{step.value}__{collection.dataset}__{collection.collection}",
            step=step,
            collection=collection,
            action_needed=action_needed,
        )

    def get_email_connector_template_contents_by_dataset(
        self, step: CurrentStep, dataset: str
    ) -> List[CheckpointActionRequired]:
        """Retrieve the raw details to populate an email template for collections on a given dataset."""
        cache: FidesopsRedis = get_cache()
        email_contents: Dict[str, Optional[Any]] = cache.get_encoded_objects_by_prefix(
            f"EMAIL_INFORMATION__{self.id}__{step.value}__{dataset}"
        )

        actions: List[CheckpointActionRequired] = []
        for email_content in email_contents.values():
            if email_content:
                actions.append(
                    _parse_cache_to_checkpoint_action_required(email_content)
                )
        return actions

    def cache_paused_collection_details(
        self,
        step: Optional[CurrentStep] = None,
        collection: Optional[CollectionAddress] = None,
        action_needed: Optional[List[ManualAction]] = None,
    ) -> None:
        """
        Cache details about the paused step, paused collection, and any action needed to resume the privacy request.
        """
        cache_action_required(
            cache_key=f"PAUSED_LOCATION__{self.id}",
            step=step,
            collection=collection,
            action_needed=action_needed,
        )

    def get_paused_collection_details(
        self,
    ) -> Optional[CheckpointActionRequired]:
        """Return details about the paused step, paused collection, and any action needed to resume the paused privacy request.

        The paused step lets us know if we should resume privacy request execution from the "access" or the "erasure"
        portion of the privacy request flow, and the collection tells us where we should cache manual input data for later use,
        In other words, this manual data belongs to this collection.
        """
        return get_action_required_details(cached_key=f"EN_PAUSED_LOCATION__{self.id}")

    def cache_failed_checkpoint_details(
        self,
        step: Optional[CurrentStep] = None,
        collection: Optional[CollectionAddress] = None,
    ) -> None:
        """
        Cache a checkpoint where the privacy request failed so we can later resume from this failure point.

        Cache details about the failed step and failed collection details (where applicable).
        No specific input data is required to resume a failed request, so action_needed is None.
        """
        cache_action_required(
            cache_key=f"FAILED_LOCATION__{self.id}",
            step=step,
            collection=collection,
            action_needed=None,
        )

    def get_failed_checkpoint_details(
        self,
    ) -> Optional[CheckpointActionRequired]:
        """Get details about the failed step (access or erasure) and collection that triggered failure.

        If DSR processing failed within the graph, this will let us know if we should resume privacy request execution
        from the "access" or "erasure" portion of the privacy request flow.
        """
        return get_action_required_details(cached_key=f"EN_FAILED_LOCATION__{self.id}")

    def cache_manual_webhook_access_input(
        self, manual_webhook: AccessManualWebhook, input_data: Optional[Dict[str, Any]]
    ) -> None:
        """Cache manually added data for the given manual webhook.  This is for use by the *manual_webhook* connector,
        which is *NOT* integrated with the graph.

        Dynamically creates a Pydantic model from the manual_webhook to use to validate the input_data
        """
        cache: FidesopsRedis = get_cache()
        parsed_data = manual_webhook.fields_schema.parse_obj(input_data)

        cache.set_encoded_object(
            f"WEBHOOK_MANUAL_ACCESS_INPUT__{self.id}__{manual_webhook.id}",
            parsed_data.dict(),
        )

    def cache_manual_webhook_erasure_input(
        self, manual_webhook: AccessManualWebhook, input_data: Optional[Dict[str, Any]]
    ) -> None:
        """Cache manually added data for the given manual webhook.  This is for use by the *manual_webhook* connector,
        which is *NOT* integrated with the graph.

        Dynamically creates a Pydantic model from the manual_webhook to use to validate the input_data
        """
        cache: FidesopsRedis = get_cache()
        parsed_data = manual_webhook.erasure_fields_schema.parse_obj(input_data)

        cache.set_encoded_object(
            f"WEBHOOK_MANUAL_ERASURE_INPUT__{self.id}__{manual_webhook.id}",
            parsed_data.dict(),
        )

    def get_manual_webhook_access_input_strict(
        self, manual_webhook: AccessManualWebhook
    ) -> Dict[str, Any]:
        """
        Retrieves manual webhook fields saved to the privacy request in strict mode.
        Fails either if extra saved fields are detected (webhook definition had fields removed) or fields were not
        explicitly set (webhook definition had fields added). This mode lets us know if webhooks data needs to be re-uploaded.

        This is for use by the *manual_webhook* connector which is *NOT* integrated with the graph.
        """
        cached_results: Optional[Dict[str, Any]] = _get_manual_access_input_from_cache(
            privacy_request=self, manual_webhook=manual_webhook
        )

        if cached_results:
            data: Dict[str, Any] = manual_webhook.fields_schema.parse_obj(
                cached_results
            ).dict(exclude_unset=True)
            if set(data.keys()) != set(manual_webhook.fields_schema.__fields__.keys()):
                raise ManualWebhookFieldsUnset(
                    f"Fields unset for privacy_request_id '{self.id}' for connection config '{manual_webhook.connection_config.key}'"
                )
            return data
        raise NoCachedManualWebhookEntry(
            f"No data cached for privacy_request_id '{self.id}' for connection config '{manual_webhook.connection_config.key}'"
        )

    def get_manual_webhook_erasure_input_strict(
        self, manual_webhook: AccessManualWebhook
    ) -> Dict[str, Any]:
        """
        Retrieves manual webhook fields saved to the privacy request in strict mode.
        Fails either if extra saved fields are detected (webhook definition had fields removed) or fields were not
        explicitly set (webhook definition had fields added). This mode lets us know if webhooks data needs to be re-uploaded.

        This is for use by the *manual_webhook* connector which is *NOT* integrated with the graph.
        """
        cached_results: Optional[Dict[str, Any]] = _get_manual_erasure_input_from_cache(
            privacy_request=self, manual_webhook=manual_webhook
        )

        if cached_results:
            data: Dict[str, Any] = manual_webhook.erasure_fields_schema.parse_obj(
                cached_results
            ).dict(exclude_unset=True)
            if set(data.keys()) != set(
                manual_webhook.erasure_fields_schema.__fields__.keys()
            ):
                raise ManualWebhookFieldsUnset(
                    f"Fields unset for privacy_request_id '{self.id}' for connection config '{manual_webhook.connection_config.key}'"
                )
            return data
        raise NoCachedManualWebhookEntry(
            f"No data cached for privacy_request_id '{self.id}' for connection config '{manual_webhook.connection_config.key}'"
        )

    def get_manual_webhook_access_input_non_strict(
        self, manual_webhook: AccessManualWebhook
    ) -> Dict[str, Any]:
        """Retrieves manual webhook fields saved to the privacy request in non-strict mode.
        Returns None for any fields not explicitly set and ignores extra fields.

        This is for use by the *manual_webhook* connector which is *NOT* integrated with the graph.
        """
        cached_results: Optional[Dict[str, Any]] = _get_manual_access_input_from_cache(
            privacy_request=self, manual_webhook=manual_webhook
        )
        if cached_results:
            return manual_webhook.fields_non_strict_schema.parse_obj(
                cached_results
            ).dict()
        return manual_webhook.empty_fields_dict

    def get_manual_webhook_erasure_input_non_strict(
        self, manual_webhook: AccessManualWebhook
    ) -> Dict[str, Any]:
        """Retrieves manual webhook fields saved to the privacy request in non-strict mode.
        Returns None for any fields not explicitly set and ignores extra fields.

        This is for use by the *manual_webhook* connector which is *NOT* integrated with the graph.
        """
        cached_results: Optional[Dict[str, Any]] = _get_manual_erasure_input_from_cache(
            privacy_request=self, manual_webhook=manual_webhook
        )
        if cached_results:
            return manual_webhook.erasure_fields_non_strict_schema.parse_obj(
                cached_results
            ).dict()
        return manual_webhook.empty_fields_dict

    def cache_manual_access_input(
        self, collection: CollectionAddress, manual_rows: Optional[List[Row]]
    ) -> None:
        """Cache manually added rows for the given CollectionAddress. This is for use by the *manual* connector which is integrated with the graph."""
        cache: FidesopsRedis = get_cache()
        cache.set_encoded_object(
            f"MANUAL_INPUT__{self.id}__{collection.value}",
            manual_rows,
        )

    def get_manual_access_input(
        self, collection: CollectionAddress
    ) -> Optional[List[Row]]:
        """Retrieve manually added rows from the cache for the given CollectionAddress.
        Returns the manual data if it exists, otherwise None.

        This is for use by the *manual* connector which is integrated with the graph.
        """
        cache: FidesopsRedis = get_cache()
        cached_results: Optional[
            Dict[str, Optional[List[Row]]]
        ] = cache.get_encoded_objects_by_prefix(
            f"MANUAL_INPUT__{self.id}__{collection.value}"
        )
        return list(cached_results.values())[0] if cached_results else None

    def cache_manual_erasure_count(
        self, collection: CollectionAddress, count: int
    ) -> None:
        """Cache the number of rows manually masked for a given collection.

        This is for use by the *manual* connector which is integrated with the graph.
        """
        cache: FidesopsRedis = get_cache()
        cache.set_encoded_object(
            f"MANUAL_MASK__{self.id}__{collection.value}",
            count,
        )

    def get_manual_erasure_count(self, collection: CollectionAddress) -> Optional[int]:
        """Retrieve number of rows manually masked for this collection from the cache.

        Cached as an integer to mimic what we return from erasures in an automated way.
        This is for use by the *manual* connector which is integrated with the graph.
        """
        cache: FidesopsRedis = get_cache()
        prefix = f"MANUAL_MASK__{self.id}__{collection.value}"
        value_dict: Optional[Dict[str, int]] = cache.get_encoded_objects_by_prefix(  # type: ignore
            prefix
        )
        return list(value_dict.values())[0] if value_dict else None

    def cache_access_graph(self, value: GraphRepr) -> None:
        """Cache a representation of the graph built for the access request"""
        cache: FidesopsRedis = get_cache()
        cache.set_encoded_object(f"ACCESS_GRAPH__{self.id}", value)

    def get_cached_access_graph(self) -> Optional[GraphRepr]:
        """Fetch the graph built for the access request"""
        cache: FidesopsRedis = get_cache()
        value_dict: Optional[
            Dict[str, Optional[GraphRepr]]
        ] = cache.get_encoded_objects_by_prefix(f"ACCESS_GRAPH__{self.id}")
        return list(value_dict.values())[0] if value_dict else None

    def cache_data_use_map(self, value: Dict[str, Set[str]]) -> None:
        """
        Cache a dict of collections traversed in the privacy request
        mapped to their associated data uses
        """
        cache: FidesopsRedis = get_cache()
        cache.set_encoded_object(f"DATA_USE_MAP__{self.id}", value)

    def get_cached_data_use_map(self) -> Optional[Dict[str, Set[str]]]:
        """
        Fetch the collection -> data use map cached for this privacy request
        """
        cache: FidesopsRedis = get_cache()
        value_dict: Optional[
            Dict[str, Optional[Dict[str, Set[str]]]]
        ] = cache.get_encoded_objects_by_prefix(f"DATA_USE_MAP__{self.id}")
        return list(value_dict.values())[0] if value_dict else None

    def trigger_policy_webhook(
        self,
        webhook: WebhookTypes,
        policy_action: Optional[ActionType] = None,
    ) -> None:
        """Trigger a request to a single customer-defined policy webhook. Raises an exception if webhook response
        should cause privacy request execution to stop.

        Pre-Execution webhooks send headers to the webhook in case the service needs to send back instructions
        to halt.  To resume, they use send a request to the reply-to URL with the reply-to-token.
        """
        # temp fix for circular dependency
        from fides.api.service.connectors import HTTPSConnector, get_connector

        https_connector: HTTPSConnector = get_connector(webhook.connection_config)  # type: ignore
        request_body = SecondPartyRequestFormat(
            privacy_request_id=self.id,
            privacy_request_status=self.status,
            direction=webhook.direction.value,  # type: ignore
            callback_type=webhook.prefix,
            identity=self.get_cached_identity_data(),
            policy_action=policy_action,
        )

        headers = {}
        is_pre_webhook = isinstance(webhook, PolicyPreWebhook)
        response_expected = webhook.direction == WebhookDirection.two_way
        if is_pre_webhook and response_expected:
            headers = {
                "reply-to": f"/privacy-request/{self.id}/resume",
                "reply-to-token": generate_request_callback_jwe(webhook),  # type: ignore[arg-type]
            }

        logger.info(
            "Calling webhook '{}' for privacy_request '{}'", webhook.key, self.id
        )
        response: Optional[SecondPartyResponseFormat] = https_connector.execute(  # type: ignore
            request_body.dict(),
            response_expected=response_expected,
            additional_headers=headers,
        )
        if not response:
            return

        response_body = SecondPartyResponseFormat(**response)  # type: ignore

        # Cache any new identities
        if response_body.derived_identity and any(
            [response_body.derived_identity.dict().values()]
        ):
            logger.info(
                "Updating known identities on privacy request '{}' from webhook '{}'.",
                self.id,
                webhook.key,
            )
            # Don't persist derived identities because they aren't provided directly
            # by the end user
            self.cache_identity(response_body.derived_identity)

        # Pause execution if instructed
        if response_body.halt and is_pre_webhook:
            raise PrivacyRequestPaused(
                f"Halt instruction received on privacy request '{self.id}'."
            )

        return

    def start_processing(self, db: Session) -> None:
        """Dispatches this PrivacyRequest throughout the Fidesops System"""
        if self.started_processing_at is None:
            self.started_processing_at = datetime.utcnow()
        if self.status == PrivacyRequestStatus.pending:
            self.status = PrivacyRequestStatus.in_processing
        self.save(db=db)

    def pause_processing(self, db: Session) -> None:
        """Mark privacy request as paused, and save paused_at"""
        self.update(
            db,
            data={
                "status": PrivacyRequestStatus.paused,
                "paused_at": datetime.utcnow(),
            },
        )

    def pause_processing_for_email_send(self, db: Session) -> None:
        """Put the privacy request in a state of awaiting_email_send"""
        if self.awaiting_email_send_at is None:
            self.awaiting_email_send_at = datetime.utcnow()
        self.status = PrivacyRequestStatus.awaiting_email_send
        self.save(db=db)

    def cancel_processing(self, db: Session, cancel_reason: Optional[str]) -> None:
        """Cancels a privacy request.  Currently should only cancel 'pending' tasks"""
        if self.canceled_at is None:
            self.status = PrivacyRequestStatus.canceled
            self.cancel_reason = cancel_reason
            self.canceled_at = datetime.utcnow()
            self.save(db)

            task_id = self.get_cached_task_id()
            if task_id:
                logger.info("Revoking task {} for request {}", task_id, self.id)
                # Only revokes if execution is not already in progress
                celery_app.control.revoke(task_id, terminate=False)

    def error_processing(self, db: Session) -> None:
        """Mark privacy request as errored, and note time processing was finished"""
        self.update(
            db,
            data={
                "status": PrivacyRequestStatus.error,
                "finished_processing_at": datetime.utcnow(),
            },
        )

        PrivacyRequestError.create(
            db=db, data={"message_sent": False, "privacy_request_id": self.id}
        )


class PrivacyRequestError(Base):
    """The DB ORM model to track PrivacyRequests error message status."""

    message_sent = Column(Boolean, nullable=False, default=False)
    privacy_request_id = Column(
        String,
        ForeignKey(PrivacyRequest.id_field_path),
        nullable=False,
    )

    privacy_request = relationship(
        PrivacyRequest, back_populates="privacy_request_error"
    )


def _get_manual_access_input_from_cache(
    privacy_request: PrivacyRequest, manual_webhook: AccessManualWebhook
) -> Optional[Dict[str, Any]]:
    """Get raw manual input uploaded to the privacy request for the given webhook
    from the cache without attempting to coerce into a Pydantic schema"""
    cache: FidesopsRedis = get_cache()
    cached_results: Optional[
        Optional[Dict[str, Any]]
    ] = cache.get_encoded_objects_by_prefix(
        f"WEBHOOK_MANUAL_ACCESS_INPUT__{privacy_request.id}__{manual_webhook.id}"
    )
    if cached_results:
        return list(cached_results.values())[0]
    return None


def _get_manual_erasure_input_from_cache(
    privacy_request: PrivacyRequest, manual_webhook: AccessManualWebhook
) -> Optional[Dict[str, Any]]:
    """Get raw manual input uploaded to the privacy request for the given webhook
    from the cache without attempting to coerce into a Pydantic schema"""
    cache: FidesopsRedis = get_cache()
    cached_results: Optional[
        Optional[Dict[str, Any]]
    ] = cache.get_encoded_objects_by_prefix(
        f"WEBHOOK_MANUAL_ERASURE_INPUT__{privacy_request.id}__{manual_webhook.id}"
    )
    if cached_results:
        return list(cached_results.values())[0]
    return None


class PrivacyRequestNotifications(Base):
    email = Column(String, nullable=False)
    notify_after_failures = Column(Integer, nullable=False)


class ProvidedIdentityType(EnumType):
    """Enum for privacy request identity types"""

    email = "email"
    phone_number = "phone_number"
    ga_client_id = "ga_client_id"
    ljt_readerID = "ljt_readerID"
    fides_user_device_id = "fides_user_device_id"


class ProvidedIdentity(Base):  # pylint: disable=R0904
    """
    A table for storing identity fields and values provided at privacy request
    creation time.
    """

    privacy_request_id = Column(
        String,
        ForeignKey(PrivacyRequest.id_field_path),
    )
    privacy_request = relationship(
        PrivacyRequest,
        backref="provided_identities",
    )  # Which privacy request this identity belongs to

    field_name = Column(
        EnumColumn(ProvidedIdentityType),
        index=False,
        nullable=False,
    )
    hashed_value = Column(
        String,
        index=True,
        unique=False,
        nullable=True,
    )  # This field is used as a blind index for exact match searches
    encrypted_value = Column(
        MutableDict.as_mutable(
            StringEncryptedType(
                JSONTypeOverride,
                CONFIG.security.app_encryption_key,
                AesGcmEngine,
                "pkcs5",
            )
        ),
        nullable=True,
    )  # Type bytea in the db
    consent = relationship(
        "Consent", back_populates="provided_identity", cascade="delete, delete-orphan"
    )
    consent_request = relationship(
        "ConsentRequest",
        back_populates="provided_identity",
        cascade="delete, delete-orphan",
    )

    @classmethod
    def hash_value(
        cls,
        value: str,
        encoding: str = "UTF-8",
    ) -> str:
        """Utility function to hash the value with a generated salt"""
        SALT = "$2b$12$UErimNtlsE6qgYf2BrI1Du"
        hashed_value = hash_with_salt(
            value.encode(encoding),
            SALT.encode(encoding),
        )
        return hashed_value

    def as_identity_schema(self) -> Identity:
        """Creates an Identity schema from a ProvidedIdentity record in the application DB."""
        identity = Identity()
        if any(
            [
                not self.field_name,
                not self.encrypted_value,
            ]
        ):
            return identity

        setattr(
            identity,
            self.field_name.value,  # type:ignore
            self.encrypted_value.get("value"),  # type:ignore
        )
        return identity


class CustomPrivacyRequestField(Base):
    @declared_attr
    def __tablename__(self) -> str:
        return "custom_privacy_request_field"

    privacy_request_id = Column(
        String,
        ForeignKey(PrivacyRequest.id_field_path),
    )
    privacy_request = relationship(
        PrivacyRequest,
        backref="custom_fields",
    )

    consent_request_id = Column(String, ForeignKey("consentrequest.id"))
    consent_request = relationship("ConsentRequest", back_populates="custom_fields")

    field_name = Column(
        String,
        index=False,
        nullable=False,
    )
    field_label = Column(
        String,
        index=False,
        nullable=False,
    )
    hashed_value = Column(
        String,
        index=True,
        unique=False,
        nullable=True,
    )  # This field is used as a blind index for exact match searches
    encrypted_value = Column(
        MutableDict.as_mutable(
            StringEncryptedType(
                JSONTypeOverride,
                CONFIG.security.app_encryption_key,
                AesGcmEngine,
                "pkcs5",
            )
        ),
        nullable=True,
    )  # Type bytea in the db

    @classmethod
    def hash_value(
        cls,
        value: str,
        encoding: str = "UTF-8",
    ) -> str:
        """Utility function to hash the value with a generated salt"""
        salt = generate_salt()
        hashed_value = hash_with_salt(
            value.encode(encoding),
            salt.encode(encoding),
        )
        return hashed_value


class Consent(Base):
    """The DB ORM model for Consent."""

    provided_identity_id = Column(
        String,
        ForeignKey(ProvidedIdentity.id),
        nullable=False,
    )
    data_use = Column(String, nullable=False)
    data_use_description = Column(String)
    opt_in = Column(Boolean, nullable=False)
    has_gpc_flag = Column(
        Boolean,
        server_default="f",
        default=False,
        nullable=False,
    )
    conflicts_with_gpc = Column(
        Boolean,
        server_default="f",
        default=False,
        nullable=False,
    )

    provided_identity = relationship(ProvidedIdentity, back_populates="consent")

    UniqueConstraint(provided_identity_id, data_use, name="uix_identity_data_use")

    identity: Optional[IdentityBase] = None


class ConsentRequest(IdentityVerificationMixin, Base):
    """Tracks consent requests."""

    provided_identity_id = Column(
        String, ForeignKey(ProvidedIdentity.id), nullable=False
    )
    provided_identity = relationship(
        ProvidedIdentity,
        back_populates="consent_request",
    )

    custom_fields = relationship(
        CustomPrivacyRequestField, back_populates="consent_request"
    )

    preferences = Column(
        MutableList.as_mutable(JSONB),
        nullable=True,
    )

    identity_verified_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    privacy_request_id = Column(String, ForeignKey(PrivacyRequest.id), nullable=True)
    privacy_request = relationship(PrivacyRequest)

    def get_cached_identity_data(self) -> Dict[str, Any]:
        """Retrieves any identity data pertaining to this request from the cache."""
        prefix = f"id-{self.id}-identity-*"
        cache: FidesopsRedis = get_cache()
        keys = cache.keys(prefix)
        return {key.split("-")[-1]: cache.get(key) for key in keys}

    def verify_identity(
        self,
        db: Session,
        provided_code: Optional[str] = None,
    ) -> None:
        """
        A method to call the internal identity verification method provided by the
        `IdentityVerificationMixin`.
        """
        self._verify_identity(provided_code=provided_code)
        self.identity_verified_at = datetime.utcnow()
        self.save(db)

    def persist_custom_privacy_request_fields(
        self,
        db: Session,
        custom_privacy_request_fields: Optional[
            Dict[str, CustomPrivacyRequestFieldSchema]
        ],
    ) -> None:
        if not custom_privacy_request_fields:
            return

        if CONFIG.execution.allow_custom_privacy_request_field_collection:
            for key, item in custom_privacy_request_fields.items():
                if item.value:
                    hashed_value = CustomPrivacyRequestField.hash_value(item.value)
                    CustomPrivacyRequestField.create(
                        db=db,
                        data={
                            "consent_request_id": self.id,
                            "field_name": key,
                            "field_label": item.label,
                            "encrypted_value": {"value": item.value},
                            "hashed_value": hashed_value,
                        },
                    )
        else:
            logger.info(
                "Custom fields provided in consent request {}, but config setting 'CONFIG.execution.allow_custom_privacy_request_field_collection' prevents their storage.",
                self.id,
            )

    def get_persisted_custom_privacy_request_fields(self) -> Dict[str, Any]:
        return {
            field.field_name: {
                "label": field.field_label,
                "value": field.encrypted_value["value"],
            }
            for field in self.custom_fields  # type: ignore[attr-defined]
        }


# Unique text to separate a step from a collection address, so we can store two values in one.
PAUSED_SEPARATOR = "__fidesops_paused_sep__"


def cache_action_required(
    cache_key: str,
    step: Optional[CurrentStep] = None,
    collection: Optional[CollectionAddress] = None,
    action_needed: Optional[List[ManualAction]] = None,
) -> None:
    """Generic method to cache information about additional action required for a collection.

    For example, we might pause a privacy request at the access step of the postgres_example:address collection.  The
    user might need to retrieve an "email" field and an "address" field where the customer_id is 22 to resume the request.

    The "step" describes whether action is needed in the access or the erasure portion of the request.
    """
    cache: FidesopsRedis = get_cache()
    action_required: Optional[CheckpointActionRequired] = None
    if step:
        action_required = CheckpointActionRequired(
            step=step, collection=collection, action_needed=action_needed
        )

    cache.set_encoded_object(
        cache_key,
        action_required.dict() if action_required else None,
    )


def get_action_required_details(
    cached_key: str,
) -> Optional[CheckpointActionRequired]:
    """Get details about the action required for a given collection.

    The "step" lets us know if action is needed in the "access" or the "erasure" portion of the privacy request flow.
    The "collection" is the node in question, and the "action_needed" describes actions that must be manually
    performed to complete the request.
    """
    cache: FidesopsRedis = get_cache()
    cached_stopped: Optional[dict[str, Any]] = cache.get_encoded_by_key(cached_key)
    if cached_stopped:
        return _parse_cache_to_checkpoint_action_required(cached_stopped)

    return None


class ExecutionLogStatus(EnumType):
    """Enum for execution log statuses, reflecting where they are in their workflow"""

    in_processing = "in_processing"
    pending = "pending"
    complete = "complete"
    error = "error"
    paused = "paused"
    retrying = "retrying"
    skipped = "skipped"


class ExecutionLog(Base):
    """
    Stores the individual execution logs associated with a PrivacyRequest.

    Execution logs contain information about the individual queries as they progress through the workflow
    generated by the query builder.
    """

    connection_key = Column(String, index=True)
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


def can_run_checkpoint(
    request_checkpoint: CurrentStep, from_checkpoint: Optional[CurrentStep] = None
) -> bool:
    """Determine whether we should run a specific checkpoint in privacy request execution

    If there's no from_checkpoint specified we should always run the current checkpoint.
    """
    if not from_checkpoint:
        return True
    return EXECUTION_CHECKPOINTS.index(
        request_checkpoint
    ) >= EXECUTION_CHECKPOINTS.index(from_checkpoint)


def _parse_cache_to_checkpoint_action_required(
    cache: dict[str, Any]
) -> CheckpointActionRequired:
    collection = (
        CollectionAddress(
            cache["collection"]["dataset"],
            cache["collection"]["collection"],
        )
        if cache.get("collection")
        else None
    )
    action_needed = (
        [ManualAction(**action) for action in cache["action_needed"]]
        if cache.get("action_needed")
        else None
    )
    return CheckpointActionRequired(
        step=cache["step"],
        collection=collection,
        action_needed=action_needed,
    )
