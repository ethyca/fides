from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import Extra, conlist

from fides.api.custom_types import SafeStr
from fides.api.ops.models.privacy_experience import ComponentType, DeliveryMechanism
from fides.api.ops.models.privacy_notice import PrivacyNoticeRegion
from fides.api.ops.schemas.base_class import BaseSchema
from fides.api.ops.schemas.privacy_notice import PrivacyNoticeResponse


class PrivacyExperience(BaseSchema):
    """
    Base for PrivacyExperience API objects
    """

    disabled: Optional[bool] = False
    component: ComponentType
    delivery_mechanism: DeliveryMechanism
    regions: Optional[conlist(PrivacyNoticeRegion, min_items=1)]  # type: ignore
    component_title: Optional[SafeStr]
    component_description: Optional[SafeStr]
    banner_title: Optional[SafeStr]
    banner_description: Optional[SafeStr]
    link_label: Optional[SafeStr]
    confirmation_button_label: Optional[SafeStr]
    reject_button_label: Optional[SafeStr]
    acknowledgement_button_label: Optional[SafeStr]

    class Config:
        """Populate models with the raw value of enum fields, rather than the enum itself"""

        use_enum_values = True
        orm_mode = True
        extra = Extra.forbid


class PrivacyExperienceResponse(PrivacyExperience):
    """
    An API representation of a PrivacyExperience used for response payloads
    """

    id: str
    created_at: datetime
    updated_at: datetime
    version: float
    privacy_experience_history_id: str
    privacy_experience_template_id: Optional[str]
    privacy_notices: Optional[List[PrivacyNoticeResponse]]


class PrivacyExperienceHistorySchema(PrivacyExperience):
    """
    An API representation of a PrivacyExperienceHistory used for response payloads
    """

    version: float
    privacy_experience_id: str
    privacy_experience_template_id: str

    class Config:
        use_enum_values = True
        orm_mode = True
