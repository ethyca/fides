from enum import Enum
from typing import Iterable, List, Optional

from pydantic import validator

from fides.api.custom_types import CssStr
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.privacy_center_config import PrivacyCenterConfig


class MinimalPrivacyExperience(FidesSchema):
    """
    Minimal representation of a privacy experience, contains enough information
    to select experiences by name in the UI and an ID to link the selections in the database.
    """

    id: str
    name: str


class PropertyType(Enum):
    website = "Website"
    other = "Other"


class MinimalProperty(FidesSchema):
    id: str
    name: str


class Property(FidesSchema):
    name: str
    type: PropertyType
    id: Optional[str] = None
    experiences: List[MinimalPrivacyExperience]
    privacy_center_config: Optional[PrivacyCenterConfig]
    stylesheet: Optional[CssStr]
    paths: Optional[List[str]] = None

    @validator("paths", pre=True)
    def convert_to_list(cls, value):
        return list(value)
