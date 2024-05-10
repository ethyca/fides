from fides.api.schemas.base_class import FidesSchema


class IdentityVerificationConfigResponse(FidesSchema):
    """Response for identity verification config info"""

    identity_verification_required: bool
    disable_consent_identity_verification: bool
    valid_email_config_exists: bool
