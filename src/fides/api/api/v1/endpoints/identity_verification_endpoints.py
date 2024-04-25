from typing import Optional

from fastapi import Depends
from sqlalchemy.orm import Session

from fides.api.api import deps
from fides.api.models.messaging import MessagingConfig
from fides.api.schemas.identity_verification import IdentityVerificationConfigResponse
from fides.api.util.api_router import APIRouter
from fides.common.api.v1 import urn_registry as urls
from fides.config.config_proxy import ConfigProxy

router = APIRouter(tags=["Identity Verification"], prefix=urls.V1_URL_PREFIX)


@router.get(
    urls.ID_VERIFICATION_CONFIG,
    response_model=IdentityVerificationConfigResponse,
)
def get_id_verification_config(
    *,
    db: Session = Depends(deps.get_db),
    config_proxy: ConfigProxy = Depends(deps.get_config_proxy),
) -> IdentityVerificationConfigResponse:
    """Returns id verification config."""
    messaging_config: Optional[MessagingConfig] = db.query(MessagingConfig).first()
    return IdentityVerificationConfigResponse(
        identity_verification_required=config_proxy.execution.subject_identity_verification_required,
        disable_consent_identity_verification=config_proxy.execution.disable_consent_identity_verification,
        valid_email_config_exists=bool(messaging_config and messaging_config.secrets),
    )
