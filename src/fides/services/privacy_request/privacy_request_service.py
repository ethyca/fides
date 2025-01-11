from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.common_exceptions import (
    IdentityNotFoundException,
    MessageDispatchException,
    PolicyNotFoundException,
)
from fides.api.models.audit_log import AuditLog, AuditLogAction
from fides.api.models.policy import Policy
from fides.api.models.pre_approval_webhook import PreApprovalWebhook
from fides.api.models.privacy_preference import PrivacyPreferenceHistory
from fides.api.models.privacy_request import (
    ConsentRequest,
    ExecutionLog,
    PrivacyRequest,
    PrivacyRequestSource,
    PrivacyRequestStatus,
    RequestTask,
)
from fides.api.models.property import Property
from fides.api.schemas.api import BulkUpdateFailed
from fides.api.schemas.messaging.messaging import (
    FidesopsMessage,
    MessagingActionType,
    RequestReceiptBodyParams,
)
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import (
    BulkPostPrivacyRequests,
    BulkReviewResponse,
    PrivacyRequestCreate,
    PrivacyRequestResponse,
)
from fides.api.schemas.redis_cache import Identity
from fides.api.service.messaging.message_dispatch_service import (
    dispatch_message_task,
    message_send_enabled,
)
from fides.api.service.privacy_request.request_service import (
    build_required_privacy_request_kwargs,
    cache_data,
)
from fides.api.tasks import MESSAGING_QUEUE_NAME
from fides.api.util.cache import cache_task_tracking_key
from fides.api.util.logger import Pii
from fides.api.util.logger_context_utils import LoggerContextKeys, log_context
from fides.config.config_proxy import ConfigProxy
from fides.services.messaging.messaging_service import (
    MessagingService,
    check_and_dispatch_error_notifications,
    send_verification_code_to_user,
)


class PrivacyRequestError(Exception):
    """Base exception for privacy request operations."""

    def __init__(self, message: str, data: dict):
        self.message = message
        self.data = data
        super().__init__(message)


class PrivacyRequestService:
    def __init__(
        self,
        db: Session,
        config_proxy: ConfigProxy,
        messaging_service: MessagingService,
    ):
        self.db = db
        self.config_proxy = config_proxy
        self.messaging_service = messaging_service

    def get_privacy_request(self, privacy_request_id: str) -> Optional[PrivacyRequest]:
        privacy_request: Optional[PrivacyRequest] = PrivacyRequest.get(
            self.db, object_id=privacy_request_id
        )
        if not privacy_request:
            logger.info(f"Privacy request with ID {privacy_request_id} was not found.")
        return privacy_request

    def create_privacy_request(
        self,
        privacy_request_data: PrivacyRequestCreate,
        *,
        authenticated: bool = False,
        privacy_preferences: Optional[List[PrivacyPreferenceHistory]] = None,
        user_id: Optional[str] = None,
    ) -> PrivacyRequest:
        """Creates a single privacy request.

        Args:
            privacy_request_data: Data for creating the privacy request
            authenticated: If True, bypasses identity verification
            privacy_preferences: List of privacy preferences (for consent requests only)
            user_id: Optional ID of the user submitting the request

        Returns:
            Created PrivacyRequest

        Raises:
            PrivacyRequestError: For any creation failures
        """

        if not any(privacy_request_data.identity.model_dump(mode="json").values()):
            raise PrivacyRequestError(
                "You must provide at least one identity to process",
                privacy_request_data.model_dump(mode="json"),
            )

        if privacy_request_data.property_id:
            valid_property = Property.get_by(
                self.db, field="id", value=privacy_request_data.property_id
            )
            if not valid_property:
                raise PrivacyRequestError(
                    "Property id must be valid to process",
                    privacy_request_data.model_dump(mode="json"),
                )

        policy = Policy.get_by(
            db=self.db,
            field="key",
            value=privacy_request_data.policy_key,
        )
        if policy is None:
            raise PrivacyRequestError(
                f"Policy with key {privacy_request_data.policy_key} does not exist",
                privacy_request_data.model_dump(mode="json"),
            )

        kwargs = build_required_privacy_request_kwargs(
            privacy_request_data.requested_at,
            policy.id,
            self.config_proxy.execution.subject_identity_verification_required,
            authenticated,
        )

        OPTIONAL_FIELDS = [
            "id",
            "external_id",
            "started_processing_at",
            "finished_processing_at",
            "consent_preferences",
            "property_id",
            "source",
        ]

        for field in OPTIONAL_FIELDS:
            attr = getattr(privacy_request_data, field)
            if attr is not None:
                if field == "consent_preferences":
                    attr = [consent.model_dump(mode="json") for consent in attr]
                kwargs[field] = attr

        if (
            getattr(privacy_request_data, "source")
            == PrivacyRequestSource.request_manager
        ):
            kwargs["submitted_by"] = user_id

        try:
            privacy_request = PrivacyRequest.create(db=self.db, data=kwargs)
            privacy_request.persist_identity(
                db=self.db, identity=privacy_request_data.identity
            )
            _create_or_update_custom_fields(
                self.db,
                privacy_request,
                privacy_request_data.consent_request_id,
                privacy_request_data.custom_privacy_request_fields,
            )

            if privacy_preferences:
                for privacy_preference in privacy_preferences:
                    privacy_preference.privacy_request_id = privacy_request.id
                    privacy_preference.save(db=self.db)

            cache_data(
                privacy_request,
                policy,
                privacy_request_data.identity,
                privacy_request_data.encryption_key,
                None,
                privacy_request_data.custom_privacy_request_fields,
            )

            check_and_dispatch_error_notifications(db=self.db)

            _handle_notifications_and_processing(
                self.db,
                self.config_proxy,
                privacy_request,
                privacy_request_data,
                policy,
                authenticated,
            )

            return privacy_request

        except MessageDispatchException as exc:
            kwargs["privacy_request_id"] = privacy_request.id
            raise PrivacyRequestError(
                "Verification message could not be sent.", kwargs
            ) from exc
        except Exception as exc:
            as_string = Pii(str(exc))
            error_cls = str(exc.__class__.__name__)
            logger.error(f"Exception {error_cls}: {as_string}")
            raise PrivacyRequestError("This record could not be added", kwargs) from exc

    def create_bulk_privacy_requests(
        self,
        data: List[PrivacyRequestCreate],
        *,
        authenticated: bool = False,
        privacy_preferences: Optional[List[PrivacyPreferenceHistory]] = None,
        user_id: Optional[str] = None,
    ) -> BulkPostPrivacyRequests:
        """Creates multiple privacy requests.

        If authenticated is True the identity verification step is bypassed.
        """

        privacy_preferences = privacy_preferences or []
        created = []
        failed = []

        logger.info("Starting creation for {} privacy requests", len(data))

        for privacy_request_data in data:
            try:
                privacy_request = self.create_privacy_request(
                    privacy_request_data,
                    authenticated=authenticated,
                    privacy_preferences=privacy_preferences,
                    user_id=user_id,
                )
                created.append(privacy_request)
            except PrivacyRequestError as exc:
                failed.append(BulkUpdateFailed(message=exc.message, data=exc.data))

        return BulkPostPrivacyRequests(
            succeeded=created,
            failed=failed,
        )

    def resubmit_privacy_request(
        self, privacy_request_id: str
    ) -> Optional[PrivacyRequest]:
        """
        Creates a new privacy request based on an existing one and deletes the original.

        Args:
            privacy_request_id: The ID of the existing privacy request to resubmit

        Returns:
            PrivacyRequest: The newly created privacy request or None if the request is not found.
        """
        existing_privacy_request: Optional[PrivacyRequest] = self.get_privacy_request(
            privacy_request_id
        )

        if not existing_privacy_request:
            return None

        # Copy all needed data first
        create_data = PrivacyRequestCreate(
            id=privacy_request_id,
            requested_at=existing_privacy_request.created_at,
            identity=existing_privacy_request.get_persisted_identity(),
            custom_privacy_request_fields=existing_privacy_request.get_persisted_custom_privacy_request_fields(),
            policy_key=existing_privacy_request.policy.key,
        )
        user_id = existing_privacy_request.submitted_by

        # Delete old request and associated data first
        self.db.query(AuditLog).filter(
            AuditLog.privacy_request_id == privacy_request_id
        ).delete()
        self.db.query(ExecutionLog).filter(
            ExecutionLog.privacy_request_id == privacy_request_id
        ).delete()
        self.db.query(RequestTask).filter(
            RequestTask.privacy_request_id == privacy_request_id
        ).delete()
        self.db.delete(existing_privacy_request)
        existing_privacy_request.clear_cached_values()

        logger.info(f"Resubmitting privacy request {privacy_request_id}")

        # Create new request
        privacy_request = self.create_privacy_request(
            create_data,
            authenticated=True,
        )

        self.approve_privacy_requests([privacy_request_id], user_id=user_id)

        return privacy_request

    def approve_privacy_requests(
        self,
        request_ids: List[str],
        *,
        webhook_id: Optional[str] = None,
        user_id: Optional[str] = None,
        suppress_notification: Optional[bool] = False,
    ) -> BulkReviewResponse:
        succeeded: List[PrivacyRequest] = []
        failed: List[BulkUpdateFailed] = []

        for request_id in request_ids:
            privacy_request = self.get_privacy_request(request_id)

            if not privacy_request:
                failed.append(
                    BulkUpdateFailed(
                        message=f"No privacy request found with id '{request_id}'",
                        data={"privacy_request_id": request_id},
                    )
                )
                continue

            if privacy_request.deleted_at is not None:
                failed.append(
                    BulkUpdateFailed(
                        message="Cannot transition status for a deleted request",
                        data=PrivacyRequestResponse.model_validate(
                            privacy_request
                        ).model_dump(mode="json"),
                    )
                )
                continue

            if privacy_request.status != PrivacyRequestStatus.pending:
                failed.append(
                    BulkUpdateFailed(
                        message="Cannot transition status",
                        data=PrivacyRequestResponse.model_validate(
                            privacy_request
                        ).model_dump(mode="json"),
                    )
                )
                continue

            try:
                now = datetime.utcnow()
                privacy_request.status = PrivacyRequestStatus.approved
                privacy_request.reviewed_at = now
                privacy_request.reviewed_by = user_id

                if privacy_request.custom_fields:  # type: ignore[attr-defined]
                    privacy_request.custom_privacy_request_fields_approved_at = now
                    privacy_request.custom_privacy_request_fields_approved_by = user_id

                privacy_request.save(db=self.db)

                AuditLog.create(
                    db=self.db,
                    data={
                        "privacy_request_id": privacy_request.id,
                        "action": AuditLogAction.approved,
                        "user_id": user_id,
                        "webhook_id": webhook_id,  # the last webhook reply received is what approves the entire request
                    },
                )

                if suppress_notification:
                    self.messaging_service.send_request_approved(privacy_request)
                queue_privacy_request(privacy_request.id)

                succeeded.append(privacy_request)
            except Exception as exc:
                logger.exception(exc)
                failed.append(
                    BulkUpdateFailed(
                        message="Privacy request could not be updated",
                        data=PrivacyRequestResponse.model_validate(
                            privacy_request
                        ).model_dump(mode="json"),
                    )
                )

        return BulkReviewResponse(succeeded=succeeded, failed=failed)

    def deny_privacy_requests(
        self,
        request_ids: List[str],
        deny_reason: Optional[str],
        *,
        user_id: Optional[str] = None,
    ) -> BulkReviewResponse:
        succeeded: List[PrivacyRequest] = []
        failed: List[BulkUpdateFailed] = []

        for request_id in request_ids:
            privacy_request = self.get_privacy_request(request_id)

            if not privacy_request:
                failed.append(
                    BulkUpdateFailed(
                        message=f"No privacy request found with id '{request_id}'",
                        data={"privacy_request_id": request_id},
                    )
                )
                continue

            if privacy_request.deleted_at is not None:
                failed.append(
                    BulkUpdateFailed(
                        message="Cannot transition status for a deleted request",
                        data=PrivacyRequestResponse.model_validate(
                            privacy_request
                        ).model_dump(mode="json"),
                    )
                )
                continue

            if privacy_request.status != PrivacyRequestStatus.pending:
                failed.append(
                    BulkUpdateFailed(
                        message="Cannot transition status",
                        data=PrivacyRequestResponse.model_validate(
                            privacy_request
                        ).model_dump(mode="json"),
                    )
                )
                continue

            try:
                privacy_request.status = PrivacyRequestStatus.denied
                privacy_request.reviewed_at = datetime.utcnow()
                privacy_request.reviewed_by = user_id
                privacy_request.save(db=self.db)

                AuditLog.create(
                    db=self.db,
                    data={
                        "user_id": user_id,
                        "privacy_request_id": privacy_request.id,
                        "action": AuditLogAction.denied,
                        "message": deny_reason,
                    },
                )

                self.messaging_service.send_request_denied(privacy_request, deny_reason)

                succeeded.append(privacy_request)
            except Exception:
                failed.append(
                    BulkUpdateFailed(
                        message="Privacy request could not be updated",
                        data=PrivacyRequestResponse.model_validate(
                            privacy_request
                        ).model_dump(mode="json"),
                    )
                )

        return BulkReviewResponse(succeeded=succeeded, failed=failed)


@log_context(capture_args={"privacy_request_id": LoggerContextKeys.privacy_request_id})
def queue_privacy_request(
    privacy_request_id: str,
    from_webhook_id: Optional[str] = None,
    from_step: Optional[str] = None,
) -> str:
    logger.info("Queueing privacy request from step {}", from_step)

    from fides.api.service.privacy_request.request_runner_service import (
        run_privacy_request,
    )

    task = run_privacy_request.delay(
        privacy_request_id=privacy_request_id,
        from_webhook_id=from_webhook_id,
        from_step=from_step,
    )
    cache_task_tracking_key(privacy_request_id, task.task_id)

    return task.task_id


def _create_or_update_custom_fields(
    db: Session,
    privacy_request: PrivacyRequest,
    consent_request_id: Optional[str],
    custom_privacy_request_fields: Optional[Dict[str, Any]],
) -> None:
    """
    Updates existing custom privacy request fields in the database with a privacy request ID.
    Creates new custom privacy request fields if there aren't any available.

    The presence or absence of custom fields is based on whether or not the creation of this
    current privacy request was triggered by a consent request.
    """
    consent_request = ConsentRequest.get_by_key_or_id(
        db=db, data={"id": consent_request_id}
    )
    if consent_request and consent_request.custom_fields:
        for custom_field in consent_request.custom_fields:  # type: ignore[attr-defined]
            custom_field.privacy_request_id = privacy_request.id
            custom_field.save(db=db)
    elif custom_privacy_request_fields:
        privacy_request.persist_custom_privacy_request_fields(
            db=db,
            custom_privacy_request_fields=custom_privacy_request_fields,
        )


def _handle_notifications_and_processing(
    db: Session,
    config_proxy: ConfigProxy,
    privacy_request: PrivacyRequest,
    privacy_request_data: PrivacyRequestCreate,
    policy: Policy,
    authenticated: bool,
) -> None:
    """Handle notifications and request processing after creation"""
    if not authenticated and message_send_enabled(
        db,
        privacy_request.property_id,
        MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
        config_proxy.execution.subject_identity_verification_required,
    ):
        send_verification_code_to_user(
            db,
            privacy_request,
            privacy_request_data.identity,
            privacy_request.property_id,
        )
        return

    if not authenticated and message_send_enabled(
        db,
        privacy_request.property_id,
        MessagingActionType.PRIVACY_REQUEST_RECEIPT,
        config_proxy.notifications.send_request_receipt_notification,
    ):
        _send_privacy_request_receipt_message_to_user(
            policy,
            privacy_request_data.identity,
            config_proxy.notifications.notification_service_type,
            privacy_request.property_id,
        )

    if config_proxy.execution.require_manual_request_approval:
        _trigger_pre_approval_webhooks(db, privacy_request)
    else:
        AuditLog.create(
            db=db,
            data={
                "user_id": "system",
                "privacy_request_id": privacy_request.id,
                "action": AuditLogAction.approved,
                "message": "",
            },
        )
        queue_privacy_request(privacy_request.id)


def _send_privacy_request_receipt_message_to_user(
    policy: Optional[Policy],
    to_identity: Optional[Identity],
    service_type: Optional[str],
    property_id: Optional[str],
) -> None:
    """Helper function to send request receipt message to the user"""
    if not to_identity:
        logger.error(
            IdentityNotFoundException(
                "Identity was not found, so request receipt message could not be sent."
            )
        )
        return
    if not policy:
        logger.error(
            PolicyNotFoundException(
                "Policy was not found, so request receipt message could not be sent."
            )
        )
        return
    request_types: Set[str] = set()
    for action_type in ActionType:
        if policy.get_rules_for_action(action_type=ActionType(action_type)):
            request_types.add(action_type)

    dispatch_message_task.apply_async(
        queue=MESSAGING_QUEUE_NAME,
        kwargs={
            "message_meta": FidesopsMessage(
                action_type=MessagingActionType.PRIVACY_REQUEST_RECEIPT,
                body_params=RequestReceiptBodyParams(request_types=request_types),
            ).model_dump(mode="json"),
            "service_type": service_type,
            "to_identity": to_identity.labeled_dict(),
            "property_id": property_id,
        },
    )


def _trigger_pre_approval_webhooks(
    db: Session, privacy_request: PrivacyRequest
) -> None:
    """
    Shared method to trigger all configured pre-approval webhooks for a given privacy request.
    """
    pre_approval_webhooks = db.query(PreApprovalWebhook).all()
    for webhook in pre_approval_webhooks:
        privacy_request.trigger_pre_approval_webhook(
            webhook=webhook,
            policy_action=privacy_request.policy.get_action_type(),
        )
