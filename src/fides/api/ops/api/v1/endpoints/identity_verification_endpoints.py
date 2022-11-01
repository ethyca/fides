import logging
from typing import Optional

from fastapi import Depends
from sqlalchemy.orm import Session

from fides.api.ops.api import deps
from fides.api.ops.api.v1 import urn_registry as urls
from fides.api.ops.models.email import EmailConfig
from fides.api.ops.schemas.identity_verification import (
    IdentityVerificationConfigResponse,
)
from fides.api.ops.util.api_router import APIRouter
from fides.ctl.core.config import get_config

logger = logging.getLogger(__name__)
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
    email_config: Optional[EmailConfig] = db.query(EmailConfig).first()
    return IdentityVerificationConfigResponse(
        identity_verification_required=config.execution.subject_identity_verification_required,
        valid_email_config_exists=bool(email_config and email_config.secrets),
    )
