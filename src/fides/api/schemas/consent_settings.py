from datetime import datetime

from fides.api.schemas.base_class import FidesSchema


class ConsentSettingsRequestSchema(FidesSchema):
    """Response schema for consent settings update"""

    tcf_enabled: bool = False


class ConsentSettingsResponseSchema(ConsentSettingsRequestSchema):
    """Response schema for consent settings response"""

    created_at: datetime
    updated_at: datetime
