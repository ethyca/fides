from __future__ import annotations

from sqlalchemy.orm import Session

from fides.api.ops.models.privacy_request import ConsentRequest, PrivacyRequest
from fides.api.ops.schemas.messaging.messaging import (
    MessagingActionType,
    SubjectIdentityVerificationBodyParams,
)
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.messaging.message_dispatch_service import dispatch_message
from fides.api.ops.service.privacy_request.request_runner_service import (
    generate_id_verification_code,
)
from fides.core.config import CONFIG
from fides.core.config.config_proxy import ConfigProxy


def send_verification_code_to_user(
    db: Session, request: ConsentRequest | PrivacyRequest, to_identity: Identity | None
) -> str:
    """Generate and cache a verification code, and then message the user"""
    config_proxy = ConfigProxy(db)
    verification_code = generate_id_verification_code()
    request.cache_identity_verification_code(verification_code)
    messaging_action_type = (
        MessagingActionType.CONSENT_REQUEST
        if isinstance(request, ConsentRequest)
        else MessagingActionType.SUBJECT_IDENTITY_VERIFICATION
    )
    dispatch_message(
        db,
        action_type=messaging_action_type,
        to_identity=to_identity,
        service_type=config_proxy.notifications.notification_service_type,
        message_body_params=SubjectIdentityVerificationBodyParams(
            verification_code=verification_code,
            verification_code_ttl_seconds=CONFIG.redis.identity_verification_code_ttl_seconds,
        ),
    )

    return verification_code
