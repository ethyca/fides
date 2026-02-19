from __future__ import annotations

from datetime import datetime
from typing import Optional

from loguru import logger

from fides.api.common_exceptions import (
    IdentityNotFoundException,
    MessageDispatchException,
)
from fides.api.models.audit_log import AuditLog, AuditLogAction
from fides.api.schemas.messaging.messaging import MessagingActionType
from fides.api.schemas.policy import ActionType, CurrentStep
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.service.messaging.message_dispatch_service import message_send_enabled
from fides.api.service.privacy_request.completion_notification_service import (
    initiate_consent_request_completion_email,
    initiate_privacy_request_completion_email,
)
from fides.api.service.privacy_request.pipeline.base import PipelineStep, StepResult
from fides.api.service.privacy_request.pipeline.context import PipelineContext
from fides.api.util.logger import _log_exception
from fides.config import CONFIG
from fides.config.config_proxy import ConfigProxy


class FinalizationStep(PipelineStep):
    @property
    def checkpoint(self) -> Optional[CurrentStep]:
        return CurrentStep.finalization

    def execute(self, ctx: PipelineContext) -> StepResult:
        if ctx.privacy_request.status == PrivacyRequestStatus.error:
            return StepResult.CONTINUE

        policy = ctx.policy
        erasure_rules = policy.get_rules_for_action(action_type=ActionType.erasure)
        config_proxy = ConfigProxy(ctx.session)

        requires_finalization = ctx.privacy_request.finalized_at is None and (
            erasure_rules
            and config_proxy.execution.erasure_request_finalization_required
        )
        if requires_finalization:
            logger.info(
                "Marking privacy request '{}' as requires manual finalization.",
                ctx.privacy_request.id,
            )
            ctx.privacy_request.status = (
                PrivacyRequestStatus.requires_manual_finalization
            )
            ctx.privacy_request.save(db=ctx.session)
            return StepResult.HALT

        if ctx.privacy_request.finalized_at:
            logger.info(
                "Marking privacy request '{}' as finalized.",
                ctx.privacy_request.id,
            )
            ctx.privacy_request.add_success_execution_log(
                ctx.session,
                connection_key=None,
                dataset_name="Request finalized",
                collection_name=None,
                message=f"Request finalized for privacy request: {ctx.privacy_request.id}",
                action_type=ctx.privacy_request.policy.get_action_type(),  # type: ignore
            )

        logger.info(
            "Marking privacy request '{}' as complete.",
            ctx.privacy_request.id,
        )
        AuditLog.create(
            db=ctx.session,
            data={
                "user_id": "system",
                "privacy_request_id": ctx.privacy_request.id,
                "action": AuditLogAction.finished,
                "message": "",
            },
        )
        ctx.privacy_request.status = PrivacyRequestStatus.complete
        ctx.privacy_request.finished_processing_at = datetime.utcnow()
        ctx.privacy_request.save(db=ctx.session)

        if ctx.privacy_request.status != PrivacyRequestStatus.complete:
            return StepResult.CONTINUE

        legacy_request_completion_enabled = ConfigProxy(
            ctx.session
        ).notifications.send_request_completion_notification

        action_types = policy.get_all_action_types()

        if ActionType.access in action_types or ActionType.erasure in action_types:
            return self._send_access_erasure_email(
                ctx, action_types, legacy_request_completion_enabled
            )
        elif ActionType.consent in action_types:
            return self._send_consent_email(ctx, legacy_request_completion_enabled)

        return StepResult.CONTINUE

    def _send_access_erasure_email(
        self,
        ctx: PipelineContext,
        action_types: set[ActionType],
        legacy_request_completion_enabled: bool,
    ) -> StepResult:
        action_type = (
            MessagingActionType.PRIVACY_REQUEST_COMPLETE_ACCESS
            if ActionType.access in action_types
            else MessagingActionType.PRIVACY_REQUEST_COMPLETE_DELETION
        )

        message_send_result = message_send_enabled(
            ctx.session,
            ctx.privacy_request.property_id,
            action_type,
            legacy_request_completion_enabled,
        )

        if not message_send_result:
            return StepResult.CONTINUE

        access_result_urls = ctx.access_result_urls
        if not access_result_urls:
            access_result_urls = (ctx.privacy_request.access_result_urls or {}).get(
                "access_result_urls", []
            )

        try:
            initiate_privacy_request_completion_email(
                ctx.session,
                ctx.policy,
                access_result_urls,
                ctx.identity_data,
                ctx.privacy_request.property_id,
                ctx.privacy_request.id,
            )
            ctx.privacy_request.add_success_execution_log(
                ctx.session,
                connection_key=None,
                dataset_name="Privacy request completion email",
                collection_name=None,
                message="Privacy request completion email sent successfully.",
                action_type=ctx.privacy_request.policy.get_action_type(),  # type: ignore
            )
        except (IdentityNotFoundException, MessageDispatchException) as e:
            ctx.privacy_request.add_error_execution_log(
                ctx.session,
                connection_key=None,
                dataset_name="Privacy request completion email",
                collection_name=None,
                message=f"Privacy request completion email failed: {str(e)}",
                action_type=ctx.privacy_request.policy.get_action_type(),  # type: ignore
            )
            ctx.privacy_request.error_processing(db=ctx.session)
            _log_exception(e, CONFIG.dev_mode)
            return StepResult.HALT

        return StepResult.CONTINUE

    def _send_consent_email(
        self,
        ctx: PipelineContext,
        legacy_request_completion_enabled: bool,
    ) -> StepResult:
        consent_message_enabled = message_send_enabled(
            ctx.session,
            ctx.privacy_request.property_id,
            MessagingActionType.PRIVACY_REQUEST_COMPLETE_CONSENT,
            legacy_request_completion_enabled,
        )
        if not consent_message_enabled:
            return StepResult.CONTINUE

        try:
            email_sent = initiate_consent_request_completion_email(
                ctx.session,
                ctx.identity_data,
                ctx.privacy_request.property_id,
            )
            if email_sent:
                ctx.privacy_request.add_success_execution_log(
                    ctx.session,
                    connection_key=None,
                    dataset_name="Consent request completion email",
                    collection_name=None,
                    message="Consent request completion email sent successfully.",
                    action_type=ActionType.consent,
                )
        except MessageDispatchException as e:
            ctx.privacy_request.add_error_execution_log(
                ctx.session,
                connection_key=None,
                dataset_name="Consent request completion email",
                collection_name=None,
                message=f"Consent request completion email failed: {str(e)}",
                action_type=ActionType.consent,
            )
            ctx.privacy_request.error_processing(db=ctx.session)
            _log_exception(e, CONFIG.dev_mode)
            return StepResult.HALT

        return StepResult.CONTINUE
