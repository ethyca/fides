from __future__ import annotations

from sqlalchemy.orm import Session

from fides.api.ops.models.email import EmailConfig
from fides.api.ops.models.privacy_request import ConsentRequest, PrivacyRequest
from fides.api.ops.schemas.email.email import (
    EmailActionType,
    SubjectIdentityVerificationBodyParams,
)
from fides.api.ops.service.email.email_dispatch_service import dispatch_email
from fides.api.ops.service.privacy_request.request_runner_service import (
    generate_id_verification_code,
)
from fides.ctl.core.config import get_config

CONFIG = get_config()


def send_verification_code_to_user(
    db: Session, request: ConsentRequest | PrivacyRequest, email: str | None
) -> str:
    """Generate and cache a verification code, and then email to the user"""
    EmailConfig.get_configuration(
        db=db
    )  # Validates Fidesops is currently configured to send emails
    verification_code = generate_id_verification_code()
    request.cache_identity_verification_code(verification_code)
    email_action_type = (
        EmailActionType.CONSENT_REQUEST
        if isinstance(request, ConsentRequest)
        else EmailActionType.SUBJECT_IDENTITY_VERIFICATION
    )
    dispatch_email(
        db,
        action_type=email_action_type,
        to_email=email,
        email_body_params=SubjectIdentityVerificationBodyParams(
            verification_code=verification_code,
            verification_code_ttl_seconds=CONFIG.redis.identity_verification_code_ttl_seconds,
        ),
    )

    return verification_code
