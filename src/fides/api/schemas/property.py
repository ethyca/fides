from enum import Enum

from fides.api.schemas.base_class import FidesSchema


class PropertyType(Enum):
    website = "Website"
    other = "Other"


class PropertyCreate(FidesSchema):
    name: str
    type: PropertyType


class Property(PropertyCreate):
    key: str
