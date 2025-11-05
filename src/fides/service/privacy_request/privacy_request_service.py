from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.common_exceptions import (
    FidesopsException,
    MessageDispatchException,
    PrivacyRequestError,
    RedisNotConfigured,
)
from fides.api.models.audit_log import AuditLog, AuditLogAction
from fides.api.models.policy import Policy
from fides.api.models.pre_approval_webhook import PreApprovalWebhook
from fides.api.models.privacy_center_config import (
    PrivacyCenterConfig as PrivacyCenterConfigModel,
)
from fides.api.models.privacy_preference import PrivacyPreferenceHistory
from fides.api.models.privacy_request import (
    ConsentRequest,
    ExecutionLog,
    PrivacyRequest,
    RequestTask,
)
from fides.api.models.property import Property
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.api import BulkUpdateFailed
from fides.api.schemas.messaging.messaging import MessagingActionType
from fides.api.schemas.policy import ActionType, CurrentStep
from fides.api.schemas.privacy_center_config import LocationCustomPrivacyRequestField
from fides.api.schemas.privacy_center_config import (
    PrivacyCenterConfig as PrivacyCenterConfigSchema,
)
from fides.api.schemas.privacy_request import (
    BulkPostPrivacyRequests,
    BulkReviewResponse,
    CheckpointActionRequired,
    PrivacyRequestCreate,
    PrivacyRequestResponse,
    PrivacyRequestResubmit,
    PrivacyRequestSource,
    PrivacyRequestStatus,
)
from fides.api.service.messaging.message_dispatch_service import message_send_enabled
from fides.api.service.privacy_request.duplication_detection import check_for_duplicates
from fides.api.service.privacy_request.request_service import (
    build_required_privacy_request_kwargs,
    cache_data,
)
from fides.api.tasks import DSR_QUEUE_NAME
from fides.api.util.cache import cache_task_tracking_key
from fides.api.util.logger_context_utils import LoggerContextKeys, log_context
from fides.config.config_proxy import ConfigProxy
from fides.service.messaging.messaging_service import (
    MessagingService,
    check_and_dispatch_error_notifications,
    send_privacy_request_receipt_message_to_user,
    send_verification_code_to_user,
)


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

    def _validate_privacy_request_for_bulk_operation(
        self,
        request_id: str,
    ) -> PrivacyRequest:
        """
        Common validation logic for bulk operations.
        Raises a PrivacyRequestError if the request is not found or deleted.

        Returns the validated privacy request.
        """
        privacy_request = self.get_privacy_request(request_id)
        if not privacy_request:
            raise PrivacyRequestError(
                f"No privacy request found with id '{request_id}'",
                {"privacy_request_id": request_id},
            )
        if privacy_request.deleted_at is not None:
            raise PrivacyRequestError(
                "Cannot transition status for a deleted request",
                PrivacyRequestResponse.model_validate(privacy_request).model_dump(
                    mode="json"
                ),
            )

        return privacy_request

    def _validate_required_location_fields(
        self, privacy_request_data: PrivacyRequestCreate
    ) -> None:
        """Validate that location is provided for required location fields.

        Looks up the actual Privacy Center configuration to check if any location
        fields are marked as required for the specified policy.
        """
        # If location is already provided, no validation needed
        if privacy_request_data.location:
            return

        config_dict = self._resolve_privacy_center_config_dict(
            privacy_request_data.property_id
        )
        if not config_dict:
            return

        privacy_center_config = self._parse_privacy_center_config(config_dict)
        if not privacy_center_config:
            return

        action = self._get_matching_action(
            privacy_center_config, privacy_request_data.policy_key
        )
        if not action or not action.custom_privacy_request_fields:
            return

        missing_required = self._is_required_location_missing(
            action, privacy_request_data
        )
        if missing_required:
            # Find the first location field name to reference in the error for clarity
            first_location_field = next(
                (
                    name
                    for name, cfg in action.custom_privacy_request_fields.items()
                    if isinstance(cfg, LocationCustomPrivacyRequestField)
                    and getattr(cfg, "required", False)
                ),
                "location",
            )
            raise PrivacyRequestError(
                f"Location is required for field '{first_location_field}' but was not provided",
                privacy_request_data.model_dump(mode="json"),
            )

    def _resolve_privacy_center_config_dict(
        self, property_id: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Return the applicable Privacy Center config as a dict using precedence.

        Precedence:
        1) The request's property config (if provided)
        2) The default property's config (if available)
        3) The single-row Privacy Center config table (legacy/global)
        """
        # 1) Request's property config
        if property_id:
            prop = Property.get_by(self.db, field="id", value=property_id)
            if prop and getattr(prop, "privacy_center_config", None):
                return prop.privacy_center_config  # type: ignore[return-value]

        # 2) Default property config
        default_prop = Property.get_by(self.db, field="is_default", value=True)
        if default_prop and getattr(default_prop, "privacy_center_config", None):
            return default_prop.privacy_center_config  # type: ignore[return-value]

        # 3) Single-row global config
        privacy_center_config_record = PrivacyCenterConfigModel.filter(
            db=self.db, conditions=PrivacyCenterConfigModel.single_row  # type: ignore[arg-type]
        ).first()
        if privacy_center_config_record:
            return privacy_center_config_record.config  # type: ignore[return-value]
        return None

    def _parse_privacy_center_config(
        self, config_dict: Dict[str, Any]
    ) -> Optional[PrivacyCenterConfigSchema]:
        """Parse a config dict into a schema instance, logging and skipping on error."""
        try:
            return PrivacyCenterConfigSchema.model_validate(config_dict)
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning(
                f"Could not parse Privacy Center config for location validation: {exc}"
            )
            return None

    @staticmethod
    def _get_matching_action(
        privacy_center_config: PrivacyCenterConfigSchema, policy_key: str
    ) -> Optional[Any]:
        """Return the action entry matching the given policy key, if any."""
        for action in privacy_center_config.actions:
            if action.policy_key == policy_key:
                return action
        return None

    @staticmethod
    def _is_required_location_missing(
        action: Any, privacy_request_data: PrivacyRequestCreate
    ) -> bool:
        """Check if any required location fields exist without values in the request."""
        if not getattr(action, "custom_privacy_request_fields", None):
            return False

        custom_fields = action.custom_privacy_request_fields
        for field_name, field_config in custom_fields.items():
            if not isinstance(field_config, LocationCustomPrivacyRequestField):
                continue
            if not getattr(field_config, "required", False):
                continue

            # Check if this location field has a value in the request custom fields
            field_has_value = False
            if privacy_request_data.custom_privacy_request_fields:
                field_data = privacy_request_data.custom_privacy_request_fields.get(
                    field_name
                )
                if field_data and getattr(field_data, "value", None):
                    field_has_value = True

            if not field_has_value:
                return True

        return False

    # pylint: disable=too-many-branches, too-many-statements
    def create_privacy_request(
        self,
        privacy_request_data: PrivacyRequestCreate,
        *,
        authenticated: bool = False,
        privacy_preferences: Optional[List[PrivacyPreferenceHistory]] = None,
        submitted_by: Optional[str] = None,
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
                    "Property ID must be valid to process",
                    privacy_request_data.model_dump(mode="json"),
                )

        # Validate location is provided for required location fields
        self._validate_required_location_fields(privacy_request_data)

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

        RESUBMIT_FIELDS = [
            "id",
            "reviewed_at",
            "reviewed_by",
            "identity_verified_at",
            "custom_privacy_request_fields_approved_at",
            "custom_privacy_request_fields_approved_by",
        ]

        if isinstance(privacy_request_data, PrivacyRequestResubmit):
            for field in RESUBMIT_FIELDS:
                attr = getattr(privacy_request_data, field)
                if attr is not None:
                    kwargs[field] = attr

        OPTIONAL_FIELDS = [
            "external_id",
            "started_processing_at",
            "finished_processing_at",
            "consent_preferences",
            "property_id",
            "source",
            "location",
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
            kwargs["submitted_by"] = submitted_by

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
                privacy_request_data.identity,
                privacy_request_data.encryption_key,
                None,
                privacy_request_data.custom_privacy_request_fields,
            )

            if masking_secrets := policy.generate_masking_secrets():
                logger.info(
                    "Caching masking secrets for privacy request {}", privacy_request.id
                )
                privacy_request.persist_masking_secrets(masking_secrets)

            check_and_dispatch_error_notifications(db=self.db)

            _handle_notifications_and_processing(
                self.db,
                self.config_proxy,
                privacy_request,
                privacy_request_data,
                policy,
                authenticated,
            )

            if not isinstance(privacy_request_data, PrivacyRequestResubmit):
                check_for_duplicates(db=self.db, privacy_request=privacy_request)

            return privacy_request

        except RedisNotConfigured as exc:
            logger.error(f"{exc.__class__.__name__}: {str(exc)}")
            raise exc
        except MessageDispatchException as exc:
            kwargs["privacy_request_id"] = privacy_request.id
            raise PrivacyRequestError(
                "Verification message could not be sent.", kwargs
            ) from exc
        except Exception as exc:
            logger.error(f"{exc.__class__.__name__}: {str(exc)}")
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
                    submitted_by=user_id,
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

        if existing_privacy_request.status == PrivacyRequestStatus.complete:
            raise FidesopsException(
                f"Cannot resubmit a {existing_privacy_request.status} privacy request"
            )

        # Copy all needed data first
        create_data = PrivacyRequestResubmit(
            id=privacy_request_id,
            external_id=existing_privacy_request.external_id,
            started_processing_at=existing_privacy_request.started_processing_at,
            finished_processing_at=existing_privacy_request.finished_processing_at,
            requested_at=existing_privacy_request.requested_at,
            identity=existing_privacy_request.get_persisted_identity(),
            custom_privacy_request_fields=existing_privacy_request.get_persisted_custom_privacy_request_fields(),
            policy_key=existing_privacy_request.policy.key,
            encryption_key=existing_privacy_request.get_cached_encryption_key(),
            property_id=existing_privacy_request.property_id,
            consent_preferences=existing_privacy_request.consent_preferences,
            source=existing_privacy_request.source,
            reviewed_at=existing_privacy_request.reviewed_at,
            reviewed_by=existing_privacy_request.reviewed_by,
            identity_verified_at=existing_privacy_request.identity_verified_at,
            custom_privacy_request_fields_approved_at=existing_privacy_request.custom_privacy_request_fields_approved_at,
            custom_privacy_request_fields_approved_by=existing_privacy_request.custom_privacy_request_fields_approved_by,
        )
        submitted_by = existing_privacy_request.submitted_by
        reviewed_by = existing_privacy_request.reviewed_by

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
            create_data, authenticated=True, submitted_by=submitted_by
        )

        if _manual_approval_required(self.config_proxy, privacy_request):
            has_webhooks = self.db.query(PreApprovalWebhook).count() > 0
            # If there are pre-approval webhooks, then we do nothing since the
            # create_privacy_request method will have already triggered them,
            # and they will be responsible of approving the request.

            # If there are no pre-approval webhooks, approve the request immediately
            # since it was originally approved by a person and we don't want them to
            # have to manually re-approve
            if not has_webhooks:
                self.approve_privacy_requests(
                    [privacy_request_id],
                    reviewed_by=reviewed_by,
                    suppress_notification=True,
                )

        return privacy_request

    def approve_privacy_requests(
        self,
        request_ids: List[str],
        *,
        webhook_id: Optional[str] = None,
        reviewed_by: Optional[str] = None,
        suppress_notification: Optional[bool] = False,
    ) -> BulkReviewResponse:
        succeeded: List[PrivacyRequest] = []
        failed: List[BulkUpdateFailed] = []

        for request_id in request_ids:
            try:
                privacy_request = self._validate_privacy_request_for_bulk_operation(
                    request_id
                )
            except PrivacyRequestError as exc:
                failed.append(BulkUpdateFailed(message=exc.message, data=exc.data))
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
                privacy_request.reviewed_by = reviewed_by

                if privacy_request.custom_fields:  # type: ignore[attr-defined]
                    privacy_request.custom_privacy_request_fields_approved_at = now
                    privacy_request.custom_privacy_request_fields_approved_by = (
                        reviewed_by
                    )

                privacy_request.save(db=self.db)

                AuditLog.create(
                    db=self.db,
                    data={
                        "privacy_request_id": privacy_request.id,
                        "action": AuditLogAction.approved,
                        "user_id": reviewed_by,
                        "webhook_id": webhook_id,  # the last webhook reply received is what approves the entire request
                    },
                )

                if not suppress_notification:
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
            try:
                privacy_request = self._validate_privacy_request_for_bulk_operation(
                    request_id
                )
            except PrivacyRequestError as exc:
                failed.append(BulkUpdateFailed(message=exc.message, data=exc.data))
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

    def cancel_privacy_requests(
        self,
        request_ids: List[str],
        cancel_reason: Optional[str],
        *,
        user_id: Optional[str] = None,
    ) -> BulkReviewResponse:
        """Cancel a list of privacy requests and/or report failure"""
        succeeded: List[PrivacyRequest] = []
        failed: List[BulkUpdateFailed] = []

        # Terminal states that cannot be canceled
        terminal_states = [
            PrivacyRequestStatus.complete,
            PrivacyRequestStatus.denied,
            PrivacyRequestStatus.canceled,
            PrivacyRequestStatus.error,
        ]

        for request_id in request_ids:
            try:
                privacy_request = self._validate_privacy_request_for_bulk_operation(
                    request_id
                )
            except PrivacyRequestError as exc:
                failed.append(BulkUpdateFailed(message=exc.message, data=exc.data))
                continue

            if privacy_request.status in terminal_states:
                failed.append(
                    BulkUpdateFailed(
                        message=f"Cannot cancel privacy request in {privacy_request.status.value} status",
                        data=PrivacyRequestResponse.model_validate(
                            privacy_request
                        ).model_dump(mode="json"),
                    )
                )
                continue

            try:
                privacy_request.cancel_processing(
                    db=self.db, cancel_reason=cancel_reason
                )

                succeeded.append(privacy_request)
            except Exception:
                failed.append(
                    BulkUpdateFailed(
                        message="Privacy request could not be canceled",
                        data=PrivacyRequestResponse.model_validate(
                            privacy_request
                        ).model_dump(mode="json"),
                    )
                )

        return BulkReviewResponse(succeeded=succeeded, failed=failed)

    def finalize_privacy_requests(
        self,
        request_ids: List[str],
        *,
        user_id: Optional[str] = None,
    ) -> BulkReviewResponse:
        """Bulk finalize privacy requests that are in requires_manual_finalization status"""
        succeeded: List[PrivacyRequest] = []
        failed: List[BulkUpdateFailed] = []

        for request_id in request_ids:
            try:
                privacy_request = self._validate_privacy_request_for_bulk_operation(
                    request_id
                )
            except PrivacyRequestError as exc:
                failed.append(BulkUpdateFailed(message=exc.message, data=exc.data))
                continue

            if (
                privacy_request.status
                != PrivacyRequestStatus.requires_manual_finalization
            ):
                failed.append(
                    BulkUpdateFailed(
                        message=f"Cannot manually finalize privacy request: status is {privacy_request.status}, not requires_manual_finalization",
                        data=PrivacyRequestResponse.model_validate(
                            privacy_request
                        ).model_dump(mode="json"),
                    )
                )
                continue

            try:
                # Set finalized_by and finalized_at here, so the request runner service knows not to
                # put the request back into the requires_finalization state.
                privacy_request.finalized_at = datetime.utcnow()
                privacy_request.finalized_by = user_id
                privacy_request.save(db=self.db)

                # Queue the privacy request for finalization
                queue_privacy_request(
                    privacy_request_id=privacy_request.id,
                    from_step=CurrentStep.finalization.value,
                )

                succeeded.append(privacy_request)
            except Exception as exc:
                logger.exception(exc)
                failed.append(
                    BulkUpdateFailed(
                        message="Privacy request could not be finalized",
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

    task = run_privacy_request.apply_async(
        queue=DSR_QUEUE_NAME,
        kwargs={
            "privacy_request_id": privacy_request_id,
            "from_webhook_id": from_webhook_id,
            "from_step": from_step,
        },
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
        send_privacy_request_receipt_message_to_user(
            policy,
            privacy_request_data.identity,
            config_proxy.notifications.notification_service_type,
            privacy_request.property_id,
        )

    handle_approval(db, config_proxy, privacy_request)


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


def _requeue_privacy_request(
    db: Session,
    privacy_request: PrivacyRequest,
) -> PrivacyRequestResponse:
    """If failed_step is provided, restart the DSR within that step. Otherwise,
    restart the privacy request from the beginning."""

    if privacy_request.status not in [
        PrivacyRequestStatus.approved,
        PrivacyRequestStatus.in_processing,
    ]:
        raise PrivacyRequestError(
            f"Cannot re-queue privacy request {privacy_request.id} with status {privacy_request.status.value}"
        )

    # Both DSR 2.0 and 3.0 cache checkpoint details
    checkpoint_details: Optional[CheckpointActionRequired] = (
        privacy_request.get_failed_checkpoint_details()
    )
    resume_step = checkpoint_details.step if checkpoint_details else None

    # DSR 3.0 additionally stores Request Tasks in the application db that can be used to infer
    # a resume checkpoint in the event the cache has expired.
    if not resume_step and privacy_request.request_tasks.count():
        if privacy_request.consent_tasks.count():
            resume_step = CurrentStep.consent
        elif privacy_request.erasure_tasks.count():
            # Checking if access terminator task was completed, because erasure tasks are created
            # at the same time as the access tasks
            terminator_access_task = privacy_request.get_terminate_task_by_action(
                ActionType.access
            )
            resume_step = (
                CurrentStep.erasure
                if terminator_access_task.status == ExecutionLogStatus.complete
                else CurrentStep.access
            )
        elif privacy_request.access_tasks.count():
            resume_step = CurrentStep.access

    logger.debug(
        "Re-queuing privacy request {} from step {}",
        privacy_request.id,
        resume_step.value if resume_step else None,
    )

    return _process_privacy_request_restart(
        privacy_request,
        resume_step,
        db,
    )


def _process_privacy_request_restart(
    privacy_request: PrivacyRequest,
    failed_step: Optional[CurrentStep],
    db: Session,
) -> PrivacyRequestResponse:
    """If failed_step is provided, restart the DSR within that step. Otherwise,
    restart the privacy request from the beginning."""
    if failed_step:
        logger.info(
            "Restarting failed privacy request '{}' from '{}'",
            privacy_request.id,
            failed_step,
        )
    else:
        logger.info(
            "Restarting failed privacy request '{}' from the beginning",
            privacy_request.id,
        )

    privacy_request.status = PrivacyRequestStatus.in_processing
    privacy_request.save(db=db)
    queue_privacy_request(
        privacy_request_id=privacy_request.id,
        from_step=failed_step.value if failed_step else None,
    )

    return privacy_request  # type: ignore[return-value]


def _manual_approval_required(
    config_proxy: ConfigProxy,
    privacy_request: PrivacyRequest,
) -> bool:
    """Determines if a privacy request requires manual approval."""
    return (
        config_proxy.execution.require_manual_request_approval
        and privacy_request.policy.get_action_type() != ActionType.consent.value
    )


def handle_approval(
    db: Session, config_proxy: ConfigProxy, privacy_request: PrivacyRequest
) -> None:
    """Evaluate manual approval and handle processing or pre-approval webhooks."""
    check_for_duplicates(db=db, privacy_request=privacy_request)
    if privacy_request.status == PrivacyRequestStatus.duplicate:
        return
    if _manual_approval_required(config_proxy, privacy_request):
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
