import logging
from typing import Optional

from fastapi import Depends
from sqlalchemy.orm import Session

from fidesops.ops.api import deps
from fidesops.ops.api.v1 import urn_registry as urls
from fidesops.ops.core.config import config
from fidesops.ops.models.email import EmailConfig
from fidesops.ops.schemas.identity_verification import (
    IdentityVerificationConfigResponse,
)
from fidesops.ops.util.api_router import APIRouter

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
    email_config: Optional[EmailConfig] = db.query(EmailConfig).first()
    return IdentityVerificationConfigResponse(
        identity_verification_required=config.execution.subject_identity_verification_required,
        valid_email_config_exists=bool(email_config and email_config.secrets),
    )
