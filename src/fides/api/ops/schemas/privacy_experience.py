from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import Extra, conlist, validator

from fides.api.custom_types import SafeStr
from fides.api.ops.models.privacy_experience import ComponentType, DeliveryMechanism
from fides.api.ops.models.privacy_notice import PrivacyNoticeRegion
from fides.api.ops.schemas.base_class import BaseSchema
from fides.api.ops.schemas.privacy_notice import PrivacyNoticeResponse


class PrivacyExperience(BaseSchema):
    """
    Base for PrivacyExperience API objects.  Here all fields are optional since
    Pydantic allows subclasses to be more strict but not less strict
    """

    disabled: Optional[bool] = False
    component: Optional[ComponentType]
    delivery_mechanism: Optional[DeliveryMechanism]
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

    @validator("regions")
    @classmethod
    def validate_regions(
        cls, regions: List[PrivacyNoticeRegion]
    ) -> List[PrivacyNoticeRegion]:
        """Assert regions aren't duplicated.  Without this, duplications get flagged as misleading duplicate data uses"""
        if len(regions) != len(set(regions)):
            raise ValueError("Duplicate regions found.")
        return regions


class PrivacyExperienceCreate(PrivacyExperience):
    """
    An API representation of a PrivacyExperience.
    This model doesn't include an `id` so that it can be used for creation.
    It also establishes some fields _required_ for creation
    """

    regions: conlist(PrivacyNoticeRegion, min_items=1)  # type: ignore
    delivery_mechanism: DeliveryMechanism
    component: ComponentType


class PrivacyExperienceWithId(PrivacyExperience):
    """
    An API representation of a PrivacyExperience that includes an `id` field.
    Used to help model API responses and update payloads
    """

    id: str


class PrivacyExperienceResponse(PrivacyExperienceWithId):
    """
    An API representation of a PrivacyExperience used for response payloads
    """

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
