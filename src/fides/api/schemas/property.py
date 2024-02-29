from enum import Enum
from typing import Optional

from fides.api.schemas.base_class import FidesSchema


class PropertyType(Enum):
    website = "Website"
    other = "Other"


class Property(FidesSchema):
    name: str
    type: PropertyType
    id: Optional[str] = None
