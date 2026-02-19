from copy import deepcopy
from typing import Any, Optional

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.common_exceptions import (
    ManualWebhookFieldsUnset,
    NoCachedManualWebhookEntry,
    ValidationError,
)
from fides.api.models.attachment import Attachment
from fides.api.models.manual_webhook import AccessManualWebhook
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.service.privacy_request.attachment_handling import (
    get_attachments_content,
    process_attachments_for_upload,
)


class ManualWebhookResults(FidesSchema):
    """Represents manual webhook data retrieved from the cache and whether privacy request execution should continue"""

    manual_data_for_upload: dict[str, list[dict[str, Optional[Any]]]]
    manual_data_for_storage: dict[str, list[dict[str, Optional[Any]]]]
    proceed: bool


def get_manual_webhook_access_inputs(
    db: Session, privacy_request: PrivacyRequest, policy: Policy
) -> ManualWebhookResults:
    """Retrieves manually uploaded data for all AccessManualWebhooks and formats in a way
    to match automatically retrieved data (a list of rows). Also returns if execution should proceed.

    This data will be uploaded to the user as-is, without filtering.
    """
    manual_inputs_for_upload: dict[str, list[dict[str, Optional[Any]]]] = {}
    manual_inputs_for_storage: dict[str, list[dict[str, Optional[Any]]]] = {}

    if not policy.get_rules_for_action(action_type=ActionType.access):
        # Don't fetch manual inputs unless this policy has an access rule
        return ManualWebhookResults(
            manual_data_for_upload=manual_inputs_for_upload,
            manual_data_for_storage=manual_inputs_for_storage,
            proceed=True,
        )

    try:
        for manual_webhook in AccessManualWebhook.get_enabled(db, ActionType.access):
            # Get the manual webhook input data
            webhook_data_for_storage = (
                privacy_request.get_manual_webhook_access_input_strict(manual_webhook)
            )
            # Add the system name to the webhook data for display purposes
            webhook_data_for_storage["system_name"] = (
                manual_webhook.connection_config.system.name
            )
            webhook_data_for_upload = deepcopy(webhook_data_for_storage)

            # Get any attachments for this webhook, load from db to ensure they have their configs
            webhook_attachments = privacy_request.get_access_manual_webhook_attachments(
                db, manual_webhook.id
            )
            if webhook_attachments:
                attachment_ids = [wa.id for wa in webhook_attachments]
                loaded_attachments = (
                    db.query(Attachment).filter(Attachment.id.in_(attachment_ids)).all()
                )
                (
                    webhook_data_for_upload["attachments"],
                    webhook_data_for_storage["attachments"],
                ) = process_attachments_for_upload(
                    get_attachments_content(loaded_attachments)
                )

            manual_inputs_for_upload[manual_webhook.connection_config.key] = [
                webhook_data_for_upload
            ]
            manual_inputs_for_storage[manual_webhook.connection_config.key] = [  # type: ignore[assignment]
                webhook_data_for_storage
            ]

    except (
        NoCachedManualWebhookEntry,
        ValidationError,
        ManualWebhookFieldsUnset,
    ) as exc:
        logger.info(exc)
        privacy_request.status = PrivacyRequestStatus.requires_input
        privacy_request.save(db)
        return ManualWebhookResults(
            manual_data_for_upload=manual_inputs_for_upload,
            manual_data_for_storage=manual_inputs_for_storage,
            proceed=False,
        )

    return ManualWebhookResults(
        manual_data_for_upload=manual_inputs_for_upload,
        manual_data_for_storage=manual_inputs_for_storage,
        proceed=True,
    )


def get_manual_webhook_erasure_inputs(
    db: Session, privacy_request: PrivacyRequest, policy: Policy
) -> ManualWebhookResults:
    manual_inputs: dict[str, list[dict[str, Optional[Any]]]] = {}

    if not policy.get_rules_for_action(action_type=ActionType.erasure):
        # Don't fetch manual inputs unless this policy has an access rule
        return ManualWebhookResults(
            manual_data_for_upload=manual_inputs,
            manual_data_for_storage=manual_inputs,
            proceed=True,
        )
    try:
        for manual_webhook in AccessManualWebhook().get_enabled(db, ActionType.erasure):
            manual_inputs[manual_webhook.connection_config.key] = [
                privacy_request.get_manual_webhook_erasure_input_strict(manual_webhook)
            ]
    except (
        NoCachedManualWebhookEntry,
        ValidationError,
        ManualWebhookFieldsUnset,
    ) as exc:
        logger.info(exc)
        privacy_request.status = PrivacyRequestStatus.requires_input
        privacy_request.save(db)
        return ManualWebhookResults(
            manual_data_for_upload=manual_inputs,
            manual_data_for_storage=manual_inputs,
            proceed=False,
        )

    return ManualWebhookResults(
        manual_data_for_upload=manual_inputs,
        manual_data_for_storage=manual_inputs,
        proceed=True,
    )
