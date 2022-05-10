from enum import Enum
from typing import Optional, List

from fidesops.models.policy import DrpAction
from fidesops.schemas.base_class import BaseSchema


class DrpMeta(BaseSchema):
    """Enum to hold Drp metadata. Only version is supported at this time"""

    version: str


class DrpRegime(Enum):
    """Enum to hold Drp Regime. Only ccpa supported at this time"""

    ccpa = "ccpa"


class DrpPrivacyRequestCreate(BaseSchema):
    """Data required to create a DRP PrivacyRequest"""

    meta: DrpMeta
    regime: Optional[DrpRegime]
    exercise: DrpAction
    relationships: Optional[List[str]]
    identity: str
    status_callback: Optional[str]

    class Config:
        """Populate models with the raw value of enum fields, rather than the enum itself"""

        use_enum_values = True
