from enum import Enum
from typing import Iterable, List, Optional

from pydantic import validator

from fides.api.custom_types import CssStr
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.privacy_center_config import PrivacyCenterConfig


class MinimalPrivacyExperienceConfig(FidesSchema):
    """
    Minimal representation of a privacy experience config, contains enough information
    to select experience configs by name in the UI and an ID to link the selections in the database.
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
    experiences: List[MinimalPrivacyExperienceConfig]
    privacy_center_config: Optional[PrivacyCenterConfig]
    stylesheet: Optional[CssStr]
    paths: List[str]

    @validator("paths", pre=True)
    def convert_to_list(cls, value: Iterable) -> List[str]:
        return list(value)
