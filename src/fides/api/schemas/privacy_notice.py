from typing import List, Optional

from fideslang.validation import FidesKey
from pydantic import ConfigDict

from fides.api.models.privacy_notice import ConsentMechanism, EnforcementLevel
from fides.api.schemas.base_class import FidesSchema


class PrivacyNoticeHistorySchema(FidesSchema):
    """
    An minimal API representation of a PrivacyNoticeHistory.

    Some elements here are used to build a consent email. Most of the other notice
    schemas are in Plus.
    """

    id: str
    name: str
    notice_key: Optional[FidesKey]
    data_uses: Optional[List[str]] = []
    consent_mechanism: ConsentMechanism
    enforcement_level: Optional[EnforcementLevel]
    version: float
    translation_id: Optional[str]
    model_config = ConfigDict(use_enum_values=True, from_attributes=True)
