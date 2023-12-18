"""
Fides-specific extensions to the pydantic models of taxonomy elements as defined in fideslang.
"""

from fideslang.models import DataCategory as BaseDataCategory
from fideslang.models import DataSubject as BaseDataSubject
from fideslang.models import DataUse as BaseDataUse
from pydantic import Field

active_field = Field(
    default=True, description="Indicates whether the resource is currently 'active'."
)


class DataUse(BaseDataUse):
    active: bool = active_field


class DataCategory(BaseDataCategory):
    active: bool = active_field


class DataSubject(BaseDataSubject):
    active: bool = active_field
