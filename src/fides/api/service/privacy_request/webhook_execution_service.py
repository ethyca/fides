from typing import Optional

from loguru import logger
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.orm import Session

from fides.api.common_exceptions import (
    ClientUnsuccessfulException,
    PrivacyRequestPaused,
)
from fides.api.models.policy import (
    PolicyPreWebhook,
    WebhookTypes,
)
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.policy import CurrentStep
from fides.api.service.privacy_request.completion_notification_service import (
    initiate_paused_privacy_request_followup,
)
from fides.api.util.logger import Pii


def run_webhooks_and_report_status(
    db: Session,
    privacy_request: PrivacyRequest,
    webhook_cls: WebhookTypes,
    after_webhook_id: Optional[str] = None,
) -> bool:
    """
    Runs a series of webhooks either pre- or post- privacy request execution, if any are configured.
    Updates privacy request status if execution is paused/errored.
    Returns True if execution should proceed.
    """
    webhooks = db.query(webhook_cls).filter_by(policy_id=privacy_request.policy.id)  # type: ignore

    if after_webhook_id:
        # Only run webhooks configured to run after this Pre-Execution webhook
        pre_webhook = PolicyPreWebhook.get(db=db, object_id=after_webhook_id)
        webhooks = webhooks.filter(  # type: ignore[call-arg]
            webhook_cls.order > pre_webhook.order,  # type: ignore[union-attr]
        )

    current_step = CurrentStep[f"{webhook_cls.prefix}_webhooks"]

    for webhook in webhooks.order_by(webhook_cls.order):  # type: ignore[union-attr]
        try:
            privacy_request.trigger_policy_webhook(
                webhook=webhook,
                policy_action=privacy_request.policy.get_action_type(),
            )
        except PrivacyRequestPaused:
            logger.info(
                "Pausing execution of privacy request {}. Halt instruction received from webhook {}.",
                privacy_request.id,
                webhook.key,
            )
            privacy_request.pause_processing(db)
            initiate_paused_privacy_request_followup(privacy_request)
            return False
        except ClientUnsuccessfulException as exc:
            error_message = f"Webhook '{webhook.key}' returned an error: {exc.args[0]}"
            logger.error(
                "Privacy Request '{}' exited after response from webhook '{}': {}.",
                privacy_request.id,
                webhook.key,
                Pii(str(exc.args[0])),
            )
            privacy_request.add_error_execution_log(
                db,
                connection_key=None,
                dataset_name=f"Webhook: {webhook.key}",
                collection_name=None,
                message=error_message,
                action_type=privacy_request.policy.get_action_type(),  # type: ignore[arg-type]
            )
            privacy_request.error_processing(db)
            privacy_request.cache_failed_checkpoint_details(current_step)
            return False
        except PydanticValidationError as exc:
            error_message = f"Webhook '{webhook.key}' returned an invalid response format: {str(exc)}"
            logger.error(
                "Privacy Request '{}' errored due to response validation error from webhook '{}'.",
                privacy_request.id,
                webhook.key,
            )
            privacy_request.add_error_execution_log(
                db,
                connection_key=None,
                dataset_name=f"Webhook: {webhook.key}",
                collection_name=None,
                message=error_message,
                action_type=privacy_request.policy.get_action_type(),  # type: ignore[arg-type]
            )
            privacy_request.error_processing(db)
            privacy_request.cache_failed_checkpoint_details(current_step)
            return False

    return True
