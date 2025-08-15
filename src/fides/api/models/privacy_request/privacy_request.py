# pylint: disable=R0401, C0302

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Union

from celery.result import AsyncResult
from loguru import logger
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import Query, RelationshipProperty, Session, backref, relationship
from sqlalchemy.orm.dynamic import AppenderQuery
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
from fides.api.cryptography.cryptographic_util import (
    hash_credential_with_salt,
    hash_value_with_salt,
)
from fides.api.cryptography.identity_salt import get_identity_salt
from fides.api.db.base_class import Base  # type: ignore[attr-defined]
from fides.api.db.base_class import JSONTypeOverride
from fides.api.db.util import EnumColumn
from fides.api.graph.config import (
    ROOT_COLLECTION_ADDRESS,
    TERMINATOR_ADDRESS,
    CollectionAddress,
)
from fides.api.migrations.hash_migration_mixin import HashMigrationMixin
from fides.api.models.attachment import (
    Attachment,
    AttachmentReference,
    AttachmentReferenceType,
)
from fides.api.models.audit_log import AuditLog
from fides.api.models.client import ClientDetail
from fides.api.models.comment import Comment, CommentReference, CommentReferenceType
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.fides_user import FidesUser
from fides.api.models.field_types import EncryptedLargeDataDescriptor
from fides.api.models.manual_task import (
    ManualTask,
    ManualTaskConfig,
    ManualTaskConfigurationType,
    ManualTaskEntityType,
    ManualTaskInstance,
)
from fides.api.models.manual_webhook import AccessManualWebhook
from fides.api.models.masking_secret import MaskingSecret
from fides.api.models.policy import (
    Policy,
    PolicyPreWebhook,
    WebhookDirection,
    WebhookTypes,
)
from fides.api.models.pre_approval_webhook import (
    PreApprovalWebhook,
    PreApprovalWebhookReply,
)
from fides.api.models.privacy_request.execution_log import (
    COMPLETED_EXECUTION_LOG_STATUSES,
    EXITED_EXECUTION_LOG_STATUSES,
    ExecutionLog,
)
from fides.api.models.privacy_request.provided_identity import ProvidedIdentity
from fides.api.models.privacy_request.request_task import RequestTask
from fides.api.models.privacy_request.webhook import (
    CallbackType,
    SecondPartyRequestFormat,
    generate_request_callback_pre_approval_jwe,
    generate_request_callback_resume_jwe,
)
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.drp_privacy_request import DrpPrivacyRequestCreate
from fides.api.schemas.external_https import SecondPartyResponseFormat
from fides.api.schemas.masking.masking_secrets import MaskingSecretCache
from fides.api.schemas.policy import ActionType, CurrentStep
from fides.api.schemas.privacy_request import (
    CheckpointActionRequired,
    ManualAction,
    PrivacyRequestSource,
    PrivacyRequestStatus,
)
from fides.api.schemas.redis_cache import (
    CustomPrivacyRequestField as CustomPrivacyRequestFieldSchema,
)
from fides.api.schemas.redis_cache import Identity, LabeledIdentity, MultiValue
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
)
from fides.api.util.collection_util import Row, extract_key_for_address
from fides.api.util.constants import API_DATE_FORMAT
from fides.api.util.custom_json_encoder import CustomJSONEncoder
from fides.api.util.decrypted_identity_automaton import DecryptedIdentityAutomatonMixin
from fides.api.util.identity_verification import IdentityVerificationMixin
from fides.api.util.logger import Pii
from fides.api.util.logger_context_utils import Contextualizable, LoggerContextKeys
from fides.config import CONFIG

if TYPE_CHECKING:
    from fides.api.models.privacy_request.consent import (  # type: ignore[attr-defined]
        Consent,
        ConsentRequest,
    )


class PrivacyRequest(
    IdentityVerificationMixin, DecryptedIdentityAutomatonMixin, Contextualizable, Base
):  # pylint: disable=R0904,too-many-instance-attributes
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
    finalized_at = Column(DateTime(timezone=True), nullable=True)
    finalized_by = Column(
        String,
        ForeignKey(FidesUser.id_field_path, ondelete="SET NULL"),
        nullable=True,
    )
    submitted_by = Column(
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
    attachments = relationship(
        "Attachment",
        secondary="attachment_reference",
        primaryjoin="and_(PrivacyRequest.id == AttachmentReference.reference_id, "
        "AttachmentReference.reference_type == 'privacy_request')",
        secondaryjoin="Attachment.id == AttachmentReference.attachment_id",
        order_by="Attachment.created_at",
        viewonly=True,
        uselist=True,
    )

    comments = relationship(
        "Comment",
        secondary="comment_reference",
        primaryjoin="and_(PrivacyRequest.id == CommentReference.reference_id, "
        "CommentReference.reference_type == 'privacy_request')",
        secondaryjoin="Comment.id == CommentReference.comment_id",
        order_by="Comment.created_at",
        viewonly=True,
        uselist=True,
    )
    manual_task_instances = relationship(
        "ManualTaskInstance",
        lazy="select",
        passive_deletes="all",
        primaryjoin="and_(ManualTaskInstance.entity_id==foreign(PrivacyRequest.id), "
        "ManualTaskInstance.entity_type=='privacy_request')",
        uselist=True,
    )
    property_id = Column(String, nullable=True)

    cancel_reason = Column(String(200))
    canceled_at = Column(DateTime(timezone=True), nullable=True)
    consent_preferences = Column(MutableList.as_mutable(JSONB), nullable=True)
    source = Column(EnumColumn(PrivacyRequestSource), nullable=True)
    location = Column(String, nullable=True)

    # A PrivacyRequest can be soft deleted, so we store when it was deleted
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    # and who deleted it
    deleted_by = Column(String, nullable=True)

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

    pre_approval_webhook_replies = relationship(
        PreApprovalWebhookReply,
        back_populates="privacy_request",
    )

    paused_at = Column(DateTime(timezone=True), nullable=True)
    identity_verified_at = Column(DateTime(timezone=True), nullable=True)
    custom_privacy_request_fields_approved_at = Column(
        DateTime(timezone=True), nullable=True
    )
    due_date = Column(DateTime(timezone=True), nullable=True)
    awaiting_email_send_at = Column(DateTime(timezone=True), nullable=True)

    # Encrypted filtered access results saved for later retrieval
    _filtered_final_upload = Column(  # An encrypted JSON String - Dict[Dict[str, List[Row]]] - rule keys mapped to the filtered access results
        "filtered_final_upload",
        StringEncryptedType(
            type_in=JSONTypeOverride,
            key=CONFIG.security.app_encryption_key,
            engine=AesGcmEngine,
            padding="pkcs5",
        ),
    )

    # Use descriptor for automatic external storage handling
    filtered_final_upload = EncryptedLargeDataDescriptor(
        field_name="filtered_final_upload", empty_default={}
    )

    # Encrypted filtered access results saved for later retrieval
    access_result_urls = Column(  # An encrypted JSON String - Dict[Dict[str, List[Row]]] - rule keys mapped to the filtered access results
        StringEncryptedType(
            type_in=JSONTypeOverride,
            key=CONFIG.security.app_encryption_key,
            engine=AesGcmEngine,
            padding="pkcs5",
        ),
    )

    # Non-DB fields that are optionally added throughout the codebase
    action_required_details: Optional[CheckpointActionRequired] = None
    execution_and_audit_logs_by_dataset: Optional[property] = None
    resume_endpoint: Optional[str] = None

    request_tasks: RelationshipProperty[AppenderQuery] = relationship(
        "RequestTask",
        back_populates="privacy_request",
        lazy="dynamic",
        order_by="RequestTask.created_at",
    )

    masking_secrets: "RelationshipProperty[List[MaskingSecret]]" = relationship(
        "MaskingSecret",
        back_populates="privacy_request",
        uselist=True,
        passive_deletes="all",
    )

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

    def clear_cached_values(self) -> None:
        """
        Clears all cached values associated with this privacy request from Redis.
        """
        logger.info(f"Clearing cached values for privacy request {self.id}")
        cache: FidesopsRedis = get_cache()
        all_keys = get_all_cache_keys_for_privacy_request(privacy_request_id=self.id)
        for key in all_keys:
            cache.delete(key)

    def delete(self, db: Session) -> None:
        """
        Clean up the cached and persisted data related to this privacy request before
        deleting this object from the database
        """
        self.clear_cached_values()
        self.cleanup_external_storage()
        Attachment.delete_attachments_for_reference_and_type(
            db, self.id, AttachmentReferenceType.privacy_request
        )
        Comment.delete_comments_for_reference_and_type(
            db, self.id, CommentReferenceType.privacy_request
        )

        for provided_identity in self.provided_identities:  # type: ignore[attr-defined]
            provided_identity.delete(db=db)
        super().delete(db=db)

    def soft_delete(self, db: Session, user_id: Optional[str]) -> None:
        """
        Soft delete the privacy request, marking it as deleted and setting the user who deleted it.
        """
        self.deleted_at = datetime.utcnow()
        self.deleted_by = user_id
        self.save(db)

    def cache_identity(
        self, identity: Union[Identity, Dict[str, LabeledIdentity]]
    ) -> None:
        """Sets the identity's values at their specific locations in the Fides app cache"""
        cache: FidesopsRedis = get_cache()

        if isinstance(identity, dict):
            identity = Identity(**identity)

        identity_dict: Dict[str, Any] = identity.labeled_dict()

        for key, value in identity_dict.items():
            if value is not None:
                cache.set_with_autoexpire(
                    get_identity_cache_key(self.id, key),
                    FidesopsRedis.encode_obj(value),
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
                        json.dumps(item.value, cls=CustomJSONEncoder),
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

        if isinstance(identity, dict):
            identity = Identity(**identity)

        identity_dict = identity.labeled_dict()
        for key, value in identity_dict.items():
            if value is not None:
                if isinstance(value, dict):
                    if "label" in value and "value" in value:
                        label = value["label"]
                        value = value["value"]
                    else:
                        raise RuntimeError(
                            f"Programming error: unexpected dict value '{value}' found in an Identity's `labeled_dict()`!"
                        )
                else:
                    label = None

                hashed_value = ProvidedIdentity.hash_value(value)
                provided_identity_data = {
                    "privacy_request_id": self.id,
                    "field_name": key,
                    # We don't need to manually encrypt this field, it's done at the ORM level
                    "encrypted_value": {"value": value},
                    "hashed_value": hashed_value,
                }

                if label is not None:
                    provided_identity_data["field_label"] = label

                ProvidedIdentity.create(
                    db=db,
                    data=provided_identity_data,
                )

        # Simultaneously add identities to automaton for fuzzy search
        if CONFIG.execution.fuzzy_search_enabled:
            try:
                self.add_identities_to_automaton()
            except Exception as exc:
                # This should never affect the ability to create privacy requests
                logger.error(f"Could not add identities to Automaton: {Pii(str(exc))}")

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
        schema_dict = {}
        for field in self.provided_identities:  # type: ignore[attr-defined]
            value = field.encrypted_value.get("value")
            if field.field_label:
                value = LabeledIdentity(label=field.field_label, value=value)
            schema_dict[field.field_name] = value
        return Identity(**schema_dict)

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

    def get_cached_encryption_key(self) -> Optional[str]:
        """Gets the cached encryption key for this privacy request."""
        cache: FidesopsRedis = get_cache()
        encryption_key = cache.get(get_encryption_cache_key(self.id, "key"))
        return encryption_key

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

    def persist_masking_secrets(
        self, masking_secrets: List[MaskingSecretCache]
    ) -> None:
        """Persists masking encryption secrets to database."""
        if not masking_secrets:
            return

        session = Session.object_session(self)
        for masking_secret in masking_secrets:
            MaskingSecret.create(
                db=session,
                data={
                    "privacy_request_id": self.id,
                    "secret": masking_secret.secret,
                    "masking_strategy": masking_secret.masking_strategy,
                    "secret_type": masking_secret.secret_type,
                },
            )

    def get_cached_identity_data(self) -> Dict[str, Any]:
        """Retrieves any identity data pertaining to this request from the cache"""
        prefix = f"id-{self.id}-identity-*"
        cache: FidesopsRedis = get_cache()
        keys = cache.keys(prefix)
        result = {}
        for key in keys:
            value = cache.get(key)
            if value:
                try:
                    # try parsing the value as JSON
                    parsed_value = json.loads(value)
                except json.JSONDecodeError:
                    # if parsing as JSON fails, assume it's a string.
                    # this is purely for backward compatibility: to ensure
                    # that identity data stored pre-2.34.0 in the "old" format
                    # can still be correctly retrieved from the cache.
                    parsed_value = value
                result[key.split("-")[-1]] = parsed_value
        return result

    def get_cached_custom_privacy_request_fields(self) -> Dict[str, Any]:
        """Retrieves any custom fields pertaining to this request from the cache"""
        prefix = f"id-{self.id}-custom-privacy-request-field-*"
        cache: FidesopsRedis = get_cache()
        keys = cache.keys(prefix)
        result = {}
        for key in keys:
            value = cache.get(key)
            if value:
                result[key.split("-")[-1]] = json.loads(value)
        return result

    def get_results(self) -> Dict[str, Any]:
        """Retrieves all cached identity data associated with this Privacy Request
        Just used in testing
        """
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
    ) -> None:
        """
        Cache the checkpoint reached in the Privacy Request so it can be resumed from this point in
        case of failure.

        """
        cache_action_required(
            cache_key=f"FAILED_LOCATION__{self.id}",
            step=step,
            collection=None,  # Deprecated for failed checkpoint details
            action_needed=None,
        )

    def get_failed_checkpoint_details(
        self,
    ) -> Optional[CheckpointActionRequired]:
        """Get the latest checkpoint reached in Privacy Request processing so we know where to resume
        in case of failure.
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
        parsed_data = manual_webhook.fields_schema.model_validate(input_data)

        cache.set_encoded_object(
            f"WEBHOOK_MANUAL_ACCESS_INPUT__{self.id}__{manual_webhook.id}",
            parsed_data.model_dump(mode="json"),
        )

    def cache_manual_webhook_erasure_input(
        self, manual_webhook: AccessManualWebhook, input_data: Optional[Dict[str, Any]]
    ) -> None:
        """Cache manually added data for the given manual webhook.  This is for use by the *manual_webhook* connector,
        which is *NOT* integrated with the graph.

        Dynamically creates a Pydantic model from the manual_webhook to use to validate the input_data
        """
        cache: FidesopsRedis = get_cache()
        parsed_data = manual_webhook.erasure_fields_schema.model_validate(input_data)

        cache.set_encoded_object(
            f"WEBHOOK_MANUAL_ERASURE_INPUT__{self.id}__{manual_webhook.id}",
            parsed_data.model_dump(mode="json"),
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
            data: Dict[str, Any] = manual_webhook.fields_schema.model_validate(
                cached_results
            ).model_dump(exclude_unset=True)
            if set(data.keys()) != set(
                manual_webhook.fields_schema.model_fields.keys()
            ):
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
            data: Dict[str, Any] = manual_webhook.erasure_fields_schema.model_validate(
                cached_results
            ).model_dump(exclude_unset=True)
            if set(data.keys()) != set(
                manual_webhook.erasure_fields_schema.model_fields.keys()
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
            return manual_webhook.fields_non_strict_schema.model_validate(
                cached_results
            ).model_dump(mode="json")
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
            return manual_webhook.erasure_fields_non_strict_schema.model_validate(
                cached_results
            ).model_dump(mode="json")
        return manual_webhook.empty_fields_dict

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
        value_dict: Optional[Dict[str, Optional[Dict[str, Set[str]]]]] = (
            cache.get_encoded_objects_by_prefix(f"DATA_USE_MAP__{self.id}")
        )
        return list(value_dict.values())[0] if value_dict else None

    def trigger_pre_approval_webhook(
        self,
        webhook: PreApprovalWebhook,
        policy_action: Optional[ActionType] = None,
    ) -> None:
        """
        Firing pre-approval webhooks allows the privacy request to be automatically approved if all webhooks
        respond with "eligible" to be approved.

        To respond, the service should send a request to one of the reply-to URLs with the reply-to-token.
        """
        # temp fix for circular dependency
        from fides.api.service.connectors import HTTPSConnector, get_connector

        https_connector: HTTPSConnector = get_connector(webhook.connection_config)  # type: ignore
        request_body = SecondPartyRequestFormat(
            privacy_request_id=self.id,
            privacy_request_status=self.status,
            direction=WebhookDirection.two_way,
            callback_type=CallbackType.pre_approval,
            identity=self.get_cached_identity_data(),
            policy_action=policy_action,
        )
        headers = {
            "reply-to-approve": f"/privacy-request/{self.id}/pre-approve/eligible",
            "reply-to-deny": f"/privacy-request/{self.id}/pre-approve/not-eligible",
            "reply-to-token": generate_request_callback_pre_approval_jwe(webhook),  # type: ignore[arg-type]
        }

        logger.info(
            "Calling pre approval webhook '{}' for privacy_request '{}'",
            webhook.key,
            self.id,
        )
        https_connector.execute(  # type: ignore
            request_body.model_dump(mode="json"),
            response_expected=False,
            additional_headers=headers,
        )

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
                "reply-to-token": generate_request_callback_resume_jwe(webhook),  # type: ignore[arg-type]
            }

        logger.info(
            "Calling webhook '{}' for privacy_request '{}'", webhook.key, self.id
        )
        response: Optional[SecondPartyResponseFormat] = https_connector.execute(  # type: ignore
            request_body.model_dump(mode="json"),
            response_expected=response_expected,
            additional_headers=headers,
        )
        if not response:
            return

        response_body = SecondPartyResponseFormat(**response)  # type: ignore

        # Cache any new identities
        if response_body.derived_identity and any(
            [response_body.derived_identity.model_dump(mode="json").values()]
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
        if self.status in [PrivacyRequestStatus.pending, PrivacyRequestStatus.approved]:
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
            # Add execution log to inform user that processing is paused for email send
            ExecutionLog.create(
                db=db,
                data={
                    "privacy_request_id": self.id,
                    "connection_key": None,
                    "dataset_name": "Pending batch email send",
                    "collection_name": None,
                    "status": ExecutionLogStatus.pending,
                    "message": "Privacy request paused pending batch email send job",
                    "action_type": (
                        self.policy.get_action_type() if self.policy else None
                    ),
                },
            )
        self.status = PrivacyRequestStatus.awaiting_email_send
        self.save(db=db)

    def get_request_task_celery_task_ids(self) -> List[str]:
        """Returns the celery task ids for each of the Request Tasks (subtasks)

        It is possible Request Tasks get queued multiple times, so the celery task
        id returned is the last celery task queued.
        """
        request_task_celery_ids: List[str] = []
        for request_task in self.request_tasks:
            request_task_id: Optional[str] = request_task.get_cached_task_id()
            if request_task_id:
                request_task_celery_ids.append(request_task_id)
        return request_task_celery_ids

    def cancel_celery_tasks(self) -> None:
        """Cancel all Celery tasks associated with this privacy request.

        This includes both the main privacy request task and any sub-tasks (Request Tasks).
        """
        task_ids: List[str] = []

        # Add the main privacy request task ID
        parent_task_id = self.get_cached_task_id()
        if parent_task_id:
            task_ids.append(parent_task_id)

        # Add all request task IDs
        request_task_celery_ids = self.get_request_task_celery_task_ids()
        task_ids.extend(request_task_celery_ids)

        if not task_ids:
            return

        # Revoke all Celery tasks in batch
        logger.info(f"Revoking {len(task_ids)} tasks for privacy request {self.id}")
        try:
            # Use terminate=False to allow graceful shutdown if already running
            celery_app.control.revoke(task_ids, terminate=False)
            logger.info(
                f"Successfully revoked {len(task_ids)} tasks for privacy request {self.id}"
            )
        except Exception as exc:
            logger.warning(
                f"Failed to revoke {len(task_ids)} tasks for privacy request {self.id}: {exc}"
            )

    def cancel_processing(self, db: Session, cancel_reason: Optional[str]) -> None:
        """Cancels a privacy request.  Currently should only cancel 'pending' tasks

        Just in case, also tries to cancel sub tasks (Request Tasks) if applicable,
        although these shouldn't exist if the Privacy Request is pending.
        """
        if self.canceled_at is None:
            self.status = PrivacyRequestStatus.canceled
            self.cancel_reason = cancel_reason
            self.canceled_at = datetime.utcnow()
            self.save(db)

            self.cancel_celery_tasks()

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

    def get_log_context(self) -> Dict[LoggerContextKeys, Any]:
        context = {LoggerContextKeys.privacy_request_id: self.id}
        if self.source:
            context[LoggerContextKeys.privacy_request_source] = self.source.value
        return context

    @property
    def access_tasks(self) -> Query:
        """Return existing Access Request Tasks for the current privacy request"""
        return self.request_tasks.filter(RequestTask.action_type == ActionType.access)

    @property
    def erasure_tasks(self) -> Query:
        """Return existing Erasure Request Tasks for the current privacy request"""
        return self.request_tasks.filter(RequestTask.action_type == ActionType.erasure)

    @property
    def consent_tasks(self) -> Query:
        """Return existing Consent Request Tasks for the current privacy request"""
        return self.request_tasks.filter(RequestTask.action_type == ActionType.consent)

    def get_comment_by_id(self, db: Session, comment_id: str) -> Optional[Comment]:
        """Get the comment associated with the privacy request"""
        comment = (
            db.query(Comment)
            .join(CommentReference, Comment.id == CommentReference.comment_id)
            .filter(
                CommentReference.reference_id
                == self.id,  # Ensure the comment is linked to this privacy request
                Comment.id == comment_id,  # Match the specific comment ID
            )
            .first()
        )
        if not comment:
            logger.info(
                f"Comment with id {comment_id} not found on privacy request {self.id}"
            )
        return comment

    def get_attachment_by_id(
        self, db: Session, attachment_id: str
    ) -> Optional[Attachment]:
        """Get the attachment associated with the privacy request"""
        attachment = (
            db.query(Attachment)
            .join(
                AttachmentReference, Attachment.id == AttachmentReference.attachment_id
            )
            .filter(
                AttachmentReference.reference_id == self.id,
                Attachment.id == attachment_id,
            )
            .first()
        )
        if not attachment:
            logger.info(
                f"Attachment with id {attachment_id} not found on privacy request {self.id}"
            )
        return attachment

    def delete_attachment_by_id(self, db: Session, attachment_id: str) -> None:
        """Delete the attachment associated with the privacy request"""
        attachment = self.get_attachment_by_id(db, attachment_id)
        if attachment:
            attachment.delete(db)

    def _get_manual_webhook_attachments(
        self, db: Session, manual_webhook_id: str, reference_type: str
    ) -> List[Attachment]:
        """Helper method to get attachments that have references to both this privacy request and the specified manual webhook"""
        query = """
            SELECT DISTINCT a.*
            FROM attachment a
            INNER JOIN attachment_reference ar1 ON a.id = ar1.attachment_id
            INNER JOIN attachment_reference ar2 ON a.id = ar2.attachment_id
            WHERE ar1.reference_id = :privacy_request_id
            AND ar1.reference_type = 'privacy_request'
            AND ar2.reference_id = :manual_webhook_id
            AND ar2.reference_type = :reference_type
        """
        result = db.execute(
            query,
            {
                "privacy_request_id": self.id,
                "manual_webhook_id": manual_webhook_id,
                "reference_type": reference_type,
            },
        )
        return [Attachment(**row) for row in result]

    def get_access_manual_webhook_attachments(
        self, db: Session, manual_webhook_id: str
    ) -> List[Attachment]:
        """Get all attachments that have references to both this privacy request and the specified access manual webhook"""
        return self._get_manual_webhook_attachments(
            db, manual_webhook_id, "access_manual_webhook"
        )

    def get_erasure_manual_webhook_attachments(
        self, db: Session, manual_webhook_id: str
    ) -> List[Attachment]:
        """Get all attachments that have references to both this privacy request and the specified erasure manual webhook"""
        return self._get_manual_webhook_attachments(
            db, manual_webhook_id, "erasure_manual_webhook"
        )

    def create_manual_task_instances(
        self, db: Session, connection_configs_with_manual_tasks: list[ConnectionConfig]
    ) -> list[ManualTaskInstance]:
        """Create ManualTaskInstance entries for all active manual tasks relevant to a privacy request."""
        # Early return if no relevant policy rules
        policy_rules = {
            ActionType.access: bool(
                self.policy.get_rules_for_action(action_type=ActionType.access)
            ),
            ActionType.erasure: bool(
                self.policy.get_rules_for_action(action_type=ActionType.erasure)
            ),
        }

        if not any(policy_rules.values()):
            return []

        # Build configuration types using list comprehension
        config_types = [
            (
                ManualTaskConfigurationType.access_privacy_request
                if action_type == ActionType.access
                else ManualTaskConfigurationType.erasure_privacy_request
            )
            for action_type, has_rules in policy_rules.items()
            if has_rules
        ]

        # Get all relevant manual tasks and configs in one query
        connection_config_ids = [cc.id for cc in connection_configs_with_manual_tasks]
        manual_tasks_with_configs = (
            db.query(ManualTask, ManualTaskConfig)
            .join(ManualTaskConfig, ManualTask.id == ManualTaskConfig.task_id)
            .filter(
                ManualTask.parent_entity_id.in_(connection_config_ids),
                ManualTask.parent_entity_type == "connection_config",
                ManualTaskConfig.is_current.is_(True),
                ManualTaskConfig.config_type.in_(config_types),
            )
            .all()
        )

        # Get existing config IDs to avoid duplicates
        existing_config_ids = {
            instance.config_id for instance in self.manual_task_instances
        }

        # Create instances using list comprehension and filter out existing ones
        return [
            ManualTaskInstance.create(
                db=db,
                data={
                    "entity_id": self.id,
                    "entity_type": ManualTaskEntityType.privacy_request,
                    "task_id": manual_task.id,
                    "config_id": config.id,
                },
            )
            for manual_task, config in manual_tasks_with_configs
            if config.id not in existing_config_ids
        ]

    def get_existing_request_task(
        self,
        db: Session,
        action_type: ActionType,
        collection_address: CollectionAddress,
    ) -> Optional[RequestTask]:
        """Returns a Request Task for the current Privacy Request with action type and collection address"""
        return (
            db.query(RequestTask)
            .filter(
                RequestTask.privacy_request_id == self.id,
                RequestTask.action_type == action_type,
                RequestTask.collection_address == collection_address.value,
            )
            .first()
        )

    def get_tasks_by_action(self, action: ActionType) -> Query:
        """Convenience helper to get RequestTasks of a certain action type for the given
        privacy request"""
        if action == ActionType.access:
            return self.access_tasks

        if action == ActionType.erasure:
            return self.erasure_tasks

        if action == ActionType.consent:
            return self.consent_tasks

        raise Exception(f"Unsupported Privacy Request Action Type {action}")

    def get_root_task_by_action(self, action: ActionType) -> RequestTask:
        """Get the root tasks for a specific action"""
        root: Optional[RequestTask] = (
            self.get_tasks_by_action(action)
            .filter(RequestTask.collection_address == ROOT_COLLECTION_ADDRESS.value)
            .first()
        )
        if not root:
            raise Exception(
                f"Expected {action.value.capitalize()} root node cannot be found on privacy request {self.id} "
            )
        assert root  # for mypy
        return root

    def get_terminate_task_by_action(self, action: ActionType) -> RequestTask:
        """Get the terminate task for a specific action"""
        terminate: Optional[RequestTask] = (
            self.get_tasks_by_action(action)
            .filter(RequestTask.collection_address == TERMINATOR_ADDRESS.value)
            .first()
        )
        if not terminate:
            raise Exception(
                f"Expected {action.value.capitalize()} terminate node cannot be found on privacy request {self.id} "
            )
        assert terminate  # for mypy
        return terminate

    def get_raw_access_results(self) -> Dict[str, Optional[List[Row]]]:
        """Retrieve the *raw* access data saved on the individual access nodes

        These shouldn't be returned to the user - they are not filtered by data category
        """
        # For DSR 3.0, pull these off of the RequestTask.access_data fields
        if self.access_tasks.count():
            final_results: Dict = {}
            for task in self.access_tasks.filter(
                RequestTask.status == PrivacyRequestStatus.complete,
                RequestTask.collection_address.notin_(
                    [ROOT_COLLECTION_ADDRESS.value, TERMINATOR_ADDRESS.value]
                ),
            ):
                final_results[task.collection_address] = task.get_access_data()

            return final_results

        # TODO Remove when we stop support for DSR 2.0
        # We will no longer be pulling access results from the cache, but off of Request Tasks instead
        cache: FidesopsRedis = get_cache()
        value_dict = cache.get_encoded_objects_by_prefix(f"{self.id}__access_request")
        # extract request id to return a map of address:value
        number_of_leading_strings_to_exclude = 2
        return {
            extract_key_for_address(k, number_of_leading_strings_to_exclude): v
            for k, v in value_dict.items()
        }

    def get_raw_masking_counts(self) -> Dict[str, int]:
        """For parity, return the rows masked for an erasure request

        This is largely just used for testing
        """
        if self.erasure_tasks.count():
            # For DSR 3.0
            return {
                t.collection_address: t.rows_masked
                for t in self.erasure_tasks.filter(
                    RequestTask.status.in_(COMPLETED_EXECUTION_LOG_STATUSES)
                )
                if not t.is_root_task and not t.is_terminator_task
            }

        # TODO Remove when we stop support for DSR 2.0
        cache: FidesopsRedis = get_cache()
        value_dict = cache.get_encoded_objects_by_prefix(f"{self.id}__erasure_request")
        # extract request id to return a map of address:value
        number_of_leading_strings_to_exclude = 2
        return {extract_key_for_address(k, number_of_leading_strings_to_exclude): v for k, v in value_dict.items()}  # type: ignore

    def get_consent_results(self) -> Dict[str, int]:
        """For parity, return whether a consent request was sent for third
        party consent propagation

        This is largely just used for testing
        """
        if self.consent_tasks.count():
            # For DSR 3.0
            return {
                t.collection_address: t.consent_sent
                for t in self.consent_tasks.filter(
                    RequestTask.status.in_(EXITED_EXECUTION_LOG_STATUSES)
                )
                if not t.is_root_task and not t.is_terminator_task
            }
        # DSR 2.0 does not cache the results so nothing to do here
        return {}

    def cleanup_external_storage(self) -> None:
        """Clean up all external storage files for this privacy request"""
        # Access the descriptor from the class to call cleanup
        PrivacyRequest.filtered_final_upload.cleanup(self)

    def save_filtered_access_results(
        self, db: Session, results: Dict[str, Dict[str, List[Row]]]
    ) -> None:
        """
        For access requests, save the access data filtered by data category that we uploaded to the end user

        This is keyed by policy rule key, because we uploaded different packages for different policy rules

        """
        if not self.policy.get_rules_for_action(action_type=ActionType.access):
            return None
        self.filtered_final_upload = results
        self.save(db)

        return None

    def get_filtered_final_upload(self) -> Dict[str, Dict[str, List[Row]]]:
        """Fetched the same filtered access results we uploaded to the user"""
        return self.filtered_final_upload or {}

    def add_success_execution_log(
        self,
        db: Session,
        connection_key: Optional[str],
        dataset_name: Optional[str],
        collection_name: Optional[str],
        message: str,
        action_type: ActionType,
    ) -> ExecutionLog:
        return ExecutionLog.create(
            db=db,
            data={
                "privacy_request_id": self.id,
                "connection_key": connection_key,
                "dataset_name": dataset_name,
                "collection_name": collection_name,
                "status": ExecutionLogStatus.complete,
                "message": message,
                "action_type": action_type,
            },
        )

    def add_skipped_execution_log(
        self,
        db: Session,
        connection_key: Optional[str],
        dataset_name: Optional[str],
        collection_name: Optional[str],
        message: str,
        action_type: ActionType,
    ) -> ExecutionLog:
        return ExecutionLog.create(
            db=db,
            data={
                "privacy_request_id": self.id,
                "connection_key": connection_key,
                "dataset_name": dataset_name,
                "collection_name": collection_name,
                "status": ExecutionLogStatus.skipped,
                "message": message,
                "action_type": action_type,
            },
        )

    def add_error_execution_log(
        self,
        db: Session,
        connection_key: Optional[str],
        dataset_name: Optional[str],
        collection_name: Optional[str],
        message: str,
        action_type: ActionType,
    ) -> ExecutionLog:
        return ExecutionLog.create(
            db=db,
            data={
                "privacy_request_id": self.id,
                "connection_key": connection_key,
                "dataset_name": dataset_name,
                "collection_name": collection_name,
                "status": ExecutionLogStatus.error,
                "message": message,
                "action_type": action_type,
            },
        )


class PrivacyRequestError(Base):
    """The DB ORM model to track PrivacyRequests error message status."""

    message_sent = Column(Boolean, nullable=False, default=False)
    privacy_request_id = Column(
        String,
        ForeignKey(
            PrivacyRequest.id_field_path, ondelete="CASCADE", onupdate="CASCADE"
        ),
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
    cached_results: Optional[Optional[Dict[str, Any]]] = (
        cache.get_encoded_objects_by_prefix(
            f"WEBHOOK_MANUAL_ACCESS_INPUT__{privacy_request.id}__{manual_webhook.id}"
        )
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
    cached_results: Optional[Optional[Dict[str, Any]]] = (
        cache.get_encoded_objects_by_prefix(
            f"WEBHOOK_MANUAL_ERASURE_INPUT__{privacy_request.id}__{manual_webhook.id}"
        )
    )
    if cached_results:
        return list(cached_results.values())[0]
    return None


class PrivacyRequestNotifications(Base):
    email = Column(String, nullable=False)
    notify_after_failures = Column(Integer, nullable=False)


class CustomPrivacyRequestField(HashMigrationMixin, Base):
    @declared_attr
    def __tablename__(self) -> str:
        return "custom_privacy_request_field"

    privacy_request_id = Column(
        String,
        ForeignKey(
            PrivacyRequest.id_field_path, ondelete="CASCADE", onupdate="CASCADE"
        ),
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
    def bcrypt_hash_value(
        cls,
        value: MultiValue,
        encoding: str = "UTF-8",
    ) -> Optional[str]:
        """
        Temporary function used to hash values to the previously used bcrypt hashes.
        This can be removed once the bcrypt to SHA-256 migration is complete.
        """

        def hash_single_value(value: Union[str, int]) -> str:
            SALT = "$2b$12$UErimNtlsE6qgYf2BrI1Du"
            value_str = str(value)
            hashed_value = hash_credential_with_salt(
                value_str.encode(encoding),
                SALT.encode(encoding),
            )
            return hashed_value

        if isinstance(value, list):
            # Skip hashing lists: this avoids us hashing and later indexing potentially large values and our index
            # is not useful for array search anyway
            return None
        return hash_single_value(value)

    @classmethod
    def hash_value(
        cls,
        value: MultiValue,
        encoding: str = "UTF-8",
    ) -> Optional[str]:
        """Utility function to hash the value(s) with a generated salt"""

        def hash_single_value(value: Union[str, int]) -> str:
            SALT = get_identity_salt()
            value_str = str(value)
            hashed_value = hash_value_with_salt(
                value_str.encode(encoding),
                SALT.encode(encoding),
            )
            return hashed_value

        if isinstance(value, list):
            # Skip hashing lists: this avoids us hashing and later indexing potentially large values and our index
            # is not useful for array search anyway
            return None
        return hash_single_value(value)

    def migrate_hashed_fields(self) -> None:
        if value := self.encrypted_value.get("value"):
            self.hashed_value = self.hash_value(value)  # type: ignore
        self.is_hash_migrated = True


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
        action_required.model_dump() if action_required else None,
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


def _parse_cache_to_checkpoint_action_required(
    cache: dict[str, Any],
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
