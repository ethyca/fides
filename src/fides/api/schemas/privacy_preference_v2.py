from typing import List

from fides.api.custom_types import SafeStr
from fides.api.schemas.base_class import FidesSchema


class RecordsServed(FidesSchema):
    """Individual lists of consent attributes that were served to the user"""

    privacy_notice_history_ids: List[SafeStr] = []
    tcf_purpose_consents: List[int] = []
    tcf_purpose_legitimate_interests: List[int] = []
    tcf_special_purposes: List[int] = []
    tcf_vendor_consents: List[SafeStr] = []
    tcf_vendor_legitimate_interests: List[SafeStr] = []
    tcf_features: List[int] = []
    tcf_special_features: List[int] = []
    tcf_system_consents: List[SafeStr] = []
    tcf_system_legitimate_interests: List[SafeStr] = []


class RecordsServedResponse(RecordsServed):
    """Response after saving notices served (v2)"""

    served_notice_history_id: str
