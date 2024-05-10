from enum import Enum
from typing import List, Optional

from fides.api.schemas.base_class import FidesSchema


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
