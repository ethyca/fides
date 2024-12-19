"""
Fides-specific extensions to the pydantic models of taxonomy elements as defined in fideslang.
"""

from typing import List, Optional

from fideslang.models import DataCategory as BaseDataCategory
from fideslang.models import DataSubject as BaseDataSubject
from fideslang.models import DataSubjectRights
from fideslang.models import DataUse as BaseDataUse
from fideslang.models import DefaultModel
from fideslang.validation import FidesKey
from pydantic import BaseModel, Field

active_field = Field(
    default=True, description="Indicates whether the resource is currently 'active'."
)


class DataUse(BaseDataUse):
    active: bool = active_field


class DataCategory(BaseDataCategory):
    active: bool = active_field


class DataSubject(BaseDataSubject):
    active: bool = active_field


class TaxonomyCreateOrUpdateBase(DefaultModel, BaseModel):
    name: Optional[str] = None
    description: Optional[str]
    active: Optional[bool] = True
    fides_key: Optional[FidesKey] = None
    tags: Optional[List[str]] = None
    organization_fides_key: Optional[FidesKey] = "default_organization"


class DataUseCreateOrUpdate(TaxonomyCreateOrUpdateBase):
    parent_key: Optional[FidesKey] = None


class DataCategoryCreateOrUpdate(TaxonomyCreateOrUpdateBase):
    parent_key: Optional[FidesKey] = None


class DataSubjectCreateOrUpdate(TaxonomyCreateOrUpdateBase):
    rights: Optional[DataSubjectRights] = None
    automated_decisions_or_profiling: Optional[bool] = None
