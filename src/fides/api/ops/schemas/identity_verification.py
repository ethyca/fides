from fides.api.ops.schemas.base_class import BaseSchema


class IdentityVerificationConfigResponse(BaseSchema):
    """Response for identity verification config info"""

    identity_verification_required: bool
    valid_email_config_exists: bool
