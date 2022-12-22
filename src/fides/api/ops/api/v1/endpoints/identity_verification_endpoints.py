from typing import Optional

from fastapi import Depends
from sqlalchemy.orm import Session

from fides.api.ops.api import deps
from fides.api.ops.api.v1 import urn_registry as urls
from fides.api.ops.models.messaging import MessagingConfig
from fides.api.ops.schemas.identity_verification import (
    IdentityVerificationConfigResponse,
)
from fides.api.ops.util.api_router import APIRouter
from fides.core.config import get_config

router = APIRouter(tags=["Identity Verification"], prefix=urls.V1_URL_PREFIX)


@router.get(
    urls.ID_VERIFICATION_CONFIG,
    response_model=IdentityVerificationConfigResponse,
)
def get_id_verification_config(
    *,
    db: Session = Depends(deps.get_db),
) -> IdentityVerificationConfigResponse:
    """Returns id verification config."""
    config = get_config()
    messaging_config: Optional[MessagingConfig] = db.query(MessagingConfig).first()
    return IdentityVerificationConfigResponse(
        identity_verification_required=config.execution.subject_identity_verification_required,
        valid_email_config_exists=bool(messaging_config and messaging_config.secrets),
    )
